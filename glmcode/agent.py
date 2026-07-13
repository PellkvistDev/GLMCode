"""The agentic loop: model <-> tools until the task is done.

Frontend-agnostic: all rendering and permission prompts go through an
AgentEvents sink (terminal: ui.ConsoleEvents, desktop app: gui.WebEvents).
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

from .api import ApiError, Cancelled, Usage, ZaiClient, estimate_tokens
from .config import Config
from .events import AgentEvents
from .permissions import PermissionEngine
from .prompts import COMPACT_PROMPT, VISION_ANALYSIS_PROMPT, build_system_prompt
from .tools import TOOL_SCHEMAS, ToolError, execute_tool, get_todos


class Agent:
    def __init__(self, cfg: Config, client: ZaiClient, events: AgentEvents | None = None):
        self.cfg = cfg
        self.client = client
        if events is None:
            from .ui import ConsoleEvents
            events = ConsoleEvents(cfg)
        self.events = events
        self.permissions = PermissionEngine(mode=cfg.mode)
        self.messages: list[dict] = []
        self.session_usage = Usage()
        self.cancel = threading.Event()
        self.busy = False
        self.rebuild_system_prompt()

    # ------------------------------------------------------------------ #

    def rebuild_system_prompt(self) -> None:
        sys_msg = {"role": "system",
                   "content": build_system_prompt(Path.cwd(), self.cfg.model)}
        if self.messages and self.messages[0].get("role") == "system":
            self.messages[0] = sys_msg
        else:
            self.messages.insert(0, sys_msg)

    def set_mode(self, mode: str) -> None:
        self.cfg.mode = mode
        self.permissions.mode = mode

    def clear(self) -> None:
        self.messages = []
        self.session_usage = Usage()
        self.rebuild_system_prompt()

    def load_messages(self, messages: list) -> None:
        """Restore a persisted conversation (system prompt rebuilt fresh for
        the current cwd/model rather than reusing whatever was saved)."""
        self.messages = [m for m in messages if m.get("role") != "system"]
        self.rebuild_system_prompt()

    def set_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.session_usage = Usage(prompt_tokens, completion_tokens)

    def request_cancel(self) -> None:
        self.cancel.set()

    # ------------------------------------------------------------------ #
    # Images

    def attach_images(self, text: str, image_paths: list[Path]) -> dict:
        """Build the user message for a turn that includes images.

        vision_route == "describe": ask the free vision model for an exhaustive
        analysis and inline it as text, keeping the strong coding model in charge.
        vision_route == "direct": embed images; the turn runs on the vision model.
        """
        names = ", ".join(p.name for p in image_paths)
        if self.cfg.vision_route == "direct":
            content: list = [
                {"type": "image_url", "image_url": {"url": self._encode(p)}}
                for p in image_paths
            ]
            content.append({"type": "text", "text": text or f"(user attached: {names})"})
            return {"role": "user", "content": content}

        with self.events.status(f"analyzing {names} with {self.cfg.vision_model}..."):
            analysis = self.client.analyze_images(
                self.cfg.vision_model,
                VISION_ANALYSIS_PROMPT.format(user_text=text or "(no message)"),
                image_paths,
            )
        self.events.info(f"vision analysis of {names}: {len(analysis)} chars")
        combined = (
            f"{text}\n\n[Image analysis: {names} — produced by the vision model "
            f"from the image(s) the user attached]\n{analysis}"
        )
        return {"role": "user", "content": combined}

    @staticmethod
    def _encode(p: Path) -> str:
        from .api import encode_image_data_uri
        return encode_image_data_uri(p)

    def _payload_has_images(self) -> bool:
        for m in self.messages:
            c = m.get("content")
            if isinstance(c, list) and any(
                part.get("type") == "image_url" for part in c
            ):
                return True
        return False

    # ------------------------------------------------------------------ #
    # Main loop

    def run_turn(self, user_message: dict) -> None:
        """One user turn: append the message, loop model+tools until done."""
        self.cancel.clear()
        self.busy = True
        try:
            self._run_turn(user_message)
        finally:
            self.busy = False
            self.events.turn_done(self.session_usage, self.context_estimate())

    def _run_turn(self, user_message: dict) -> None:
        self.maybe_autocompact()
        self.messages.append(user_message)

        model = self.cfg.model
        if self._payload_has_images():
            model = self.cfg.vision_model
            self.events.info(f"images in context -> routing to {model}")

        for iteration in range(self.cfg.max_turns_per_request):
            try:
                result = self._call_model(model)
            except ApiError as e:
                self.events.error(str(e))
                if e.status in (401, 403):
                    self.events.warn(
                        "Check the ZAI_API_KEY environment variable "
                        "(setx ZAI_API_KEY your-key). Keys are free at https://z.ai")
                return
            except (Cancelled, KeyboardInterrupt):
                self.events.warn("interrupted")
                self.messages.append({
                    "role": "assistant",
                    "content": "(response interrupted by user)",
                })
                return

            self.session_usage.add(result.usage)
            self.messages.append(result.to_message())

            if not result.tool_calls:
                return  # final answer already streamed

            try:
                self._handle_tool_calls(result.tool_calls)
            except (Cancelled, KeyboardInterrupt):
                self.events.warn("interrupted during tool execution")
                return

        self.events.warn(f"stopped after {self.cfg.max_turns_per_request} agentic "
                         "steps; say 'continue' to let it keep going")

    def _call_model(self, model: str):
        self.events.stream_start()
        try:
            return self.client.chat(
                model=model,
                messages=self.messages,
                tools=TOOL_SCHEMAS,
                temperature=self.cfg.temperature,
                max_tokens=self.cfg.max_tokens,
                thinking=self.cfg.thinking,
                on_content=self.events.content_delta,
                on_reasoning=self.events.reasoning_delta,
                on_status=self.events.info,
                cancel=self.cancel,
            )
        finally:
            self.events.stream_end()

    # ------------------------------------------------------------------ #

    def _handle_tool_calls(self, tool_calls: list) -> None:
        for tc in tool_calls:
            if self.cancel.is_set():
                raise Cancelled()
            name = tc["function"]["name"]
            raw_args = tc["function"]["arguments"] or "{}"
            try:
                args = json.loads(raw_args)
                if not isinstance(args, dict):
                    raise ValueError("arguments must be a JSON object")
            except (json.JSONDecodeError, ValueError) as e:
                self._tool_reply(tc, f"ERROR: could not parse tool arguments: {e}. "
                                     f"Raw arguments were: {raw_args[:500]}",
                                 error=True, name=name, args={})
                continue

            self.events.tool_call(name, args)

            decision = self.permissions.check(name, args, self.events.ask_permission)
            if not decision.allowed:
                msg = "User denied permission for this tool call."
                if decision.feedback:
                    msg += f" User says: {decision.feedback}"
                msg += " Do not retry it as-is; adjust your approach."
                self._tool_reply(tc, msg, error=True, name=name, args=args)
                continue

            try:
                output = execute_tool(name, args)
                self._tool_reply(tc, output, name=name, args=args)
            except ToolError as e:
                self._tool_reply(tc, f"ERROR: {e}", error=True, name=name, args=args)
            except Exception as e:
                self._tool_reply(tc, f"ERROR: unexpected {type(e).__name__}: {e}",
                                 error=True, name=name, args=args)

            if name == "todo_write":
                self.events.todos(get_todos())

    def _tool_reply(self, tc: dict, content: str, error: bool = False,
                    name: str = "", args: dict | None = None) -> None:
        self.events.tool_result(name, content, is_error=error)
        self.messages.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": content,
        })

    # ------------------------------------------------------------------ #
    # Context management

    def context_estimate(self) -> int:
        return estimate_tokens(self.messages)

    def maybe_autocompact(self) -> None:
        if self.context_estimate() > self.cfg.context_limit_tokens:
            self.events.warn("context is getting large; compacting older history...")
            self.compact()

    def compact(self) -> str:
        """Summarize the conversation and restart the context from the summary."""
        if len(self.messages) < 4:
            return "Nothing to compact yet."
        transcript = self.messages[1:]  # skip system prompt
        compact_model = (self.cfg.vision_model if self._payload_has_images()
                         else self.cfg.model)
        with self.events.status("compacting conversation..."):
            result = self.client.chat(
                model=compact_model,
                messages=transcript + [{"role": "user", "content": COMPACT_PROMPT}],
                tools=None,
                temperature=0.3,
                max_tokens=4096,
                thinking=False,
            )
        summary = result.content.strip()
        self.session_usage.add(result.usage)
        self.messages = [self.messages[0], {
            "role": "user",
            "content": ("[Context was compacted. Summary of the session so far:]\n\n"
                        + summary +
                        "\n\n[Continue helping the user from this state.]"),
        }, {
            "role": "assistant",
            "content": "Understood — I have the session summary and will continue from there.",
        }]
        return f"Compacted to ~{self.context_estimate():,} tokens."
