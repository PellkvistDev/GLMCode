"""Append-only, per-chat conversation transcripts.

The session store persists the model's CURRENT context -- which means
compaction permanently shrinks what's on disk too. Transcripts fix that:
an append-only markdown log of everything ever said in a chat, living in
the global config dir (~/.glmcode/transcripts/, one file per chat). They
survive compaction, app restarts, and session switches -- and because
they're plain text files, the agent itself can grep/read them to recover
context that's no longer in its window, including from PAST chats.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .config import CONFIG_DIR

TRANSCRIPTS_DIR = CONFIG_DIR / "transcripts"
MAX_TOOL_RESULT_CHARS = 1500


def _safe(sid: str) -> str:
    return "".join(ch for ch in sid if ch.isalnum() or ch in "-_")


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


class Transcript:
    """Best-effort by design: a transcript write must never break a turn,
    so all filesystem errors are swallowed."""

    def __init__(self, session_id: str, cwd: str = "", root: Path | None = None):
        self.root = root or TRANSCRIPTS_DIR
        self.path = self.root / f"{_safe(session_id)}.md"
        self._cwd = cwd

    # ------------------------------------------------------------------ #

    def user(self, text: str, label: str = "User") -> None:
        text = (text or "").strip()
        if text:
            self._append(f"\n## {label} [{_now()}]\n{text}\n")

    def assistant(self, text: str, tool_calls: list | None = None) -> None:
        parts = []
        if text and text.strip():
            parts.append(text.strip())
        for tc in tool_calls or []:
            parts.append(f"-> tool call: {tc}")
        if parts:
            self._append(f"\n## Assistant [{_now()}]\n" + "\n".join(parts) + "\n")

    def tool_result(self, name: str, content: str, is_error: bool = False) -> None:
        content = content or ""
        body = content[:MAX_TOOL_RESULT_CHARS]
        if len(content) > MAX_TOOL_RESULT_CHARS:
            body += f"\n... [truncated; full result was {len(content)} chars]"
        tag = "tool ERROR" if is_error else "tool result"
        self._append(f"\n### {tag}: {name}\n{body}\n")

    def marker(self, text: str) -> None:
        """An out-of-band note, e.g. 'context was compacted here'."""
        self._append(f"\n---\n*{text}*\n")

    # ------------------------------------------------------------------ #

    def prompt_note(self) -> str:
        """System-prompt blurb telling the model these files exist and how
        to use them."""
        return (
            f"\n\n# Conversation transcripts\n"
            f"Every chat's FULL conversation is appended to a markdown transcript "
            f"file -- including everything that has since been compacted out of "
            f"your context.\n"
            f"This chat's transcript: {self.path}\n"
            f"All chats' transcripts (one file per chat, past chats included): {self.root}\n"
            f"If the user refers to something from earlier that you no longer have "
            f"-- or from a previous chat entirely -- use grep/read_file on those "
            f"files to look it up instead of guessing or asking them to repeat it."
        )

    def delete(self) -> None:
        try:
            self.path.unlink(missing_ok=True)
        except OSError:
            pass

    # ------------------------------------------------------------------ #

    def _append(self, text: str) -> None:
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            is_new = not self.path.exists()
            with self.path.open("a", encoding="utf-8") as f:
                if is_new:
                    f.write(f"# Chat transcript\nProject: {self._cwd}\n"
                            f"Started: {_now()}\n")
                f.write(text)
        except OSError:
            pass
