"""Plan mode: hard read-only enforcement + display unwrapping."""

import json

from glmcode.permissions import PermissionEngine
from glmcode.prompts import EXECUTE_PLAN_MESSAGE, PLAN_MODE_PREAMBLE
from glmcode.sessions import to_display

from conftest import FakeResult, tool_call


def _deny_asker(*a, **k):
    raise AssertionError("plan mode must deny without asking")


def test_plan_only_denies_writes_and_commands():
    eng = PermissionEngine(mode="yolo", plan_only=True)  # yolo can't bypass it
    for name, args in (("write_file", {"path": "x", "content": ""}),
                       ("edit_file", {"path": "x", "old_string": "a", "new_string": "b"}),
                       ("run_powershell", {"command": "rm -rf /"}),
                       ("spawn_agents", {"agents": []})):
        d = eng.check(name, args, _deny_asker)
        assert not d.allowed
        assert "Plan mode" in d.feedback


def test_plan_only_allows_readonly_exploration():
    eng = PermissionEngine(mode="ask", plan_only=True)
    for name in ("read_file", "grep", "glob", "list_dir", "todo_write",
                 "review_changes"):
        assert eng.check(name, {}, _deny_asker).allowed


def test_agent_plan_turn_blocks_edit_with_feedback(scripted_agent, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    def script(n):
        if n == 1:
            args = json.dumps({"path": str(tmp_path / "f.py"), "content": "x"})
            return FakeResult([tool_call("c1", "write_file", args)])
        return FakeResult(content="1. Step one\n2. Step two")

    agent = scripted_agent(script)
    agent.permissions.plan_only = True
    agent.run_turn({"role": "user",
                    "content": PLAN_MODE_PREAMBLE.format(text="refactor auth")})

    assert not (tmp_path / "f.py").exists()  # the write never happened
    tool_msgs = [m["content"] for m in agent.messages if m.get("role") == "tool"]
    assert any("Plan mode is active" in t for t in tool_msgs)
    assert agent.messages[-1]["content"] == "1. Step one\n2. Step two"


def test_display_unwraps_plan_and_execute_messages():
    msgs = [
        {"role": "user", "content": PLAN_MODE_PREAMBLE.format(text="add dark mode")},
        {"role": "assistant", "content": "1. do things"},
        {"role": "user", "content": EXECUTE_PLAN_MESSAGE},
        {"role": "assistant", "content": "done"},
    ]
    items = to_display(msgs)
    users = [it for it in items if it["kind"] == "user"]
    assert users[0]["text"] == "add dark mode" and users[0]["plan"] is True
    assert users[1]["text"] == "Execute the approved plan."
    assert users[1]["plan"] is False
