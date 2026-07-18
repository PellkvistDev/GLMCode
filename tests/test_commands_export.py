"""Custom slash commands (config CRUD) and Markdown chat export."""

import sys
import types
from pathlib import Path

sys.modules.setdefault("webview", types.SimpleNamespace(
    Window=object, FOLDER_DIALOG=object(), OPEN_DIALOG=object(), SAVE_DIALOG=object()))

from glmcode.config import Config  # noqa: E402
from glmcode.gui import app as gui_app  # noqa: E402


def _api(monkeypatch, cfg=None):
    api = gui_app.Api.__new__(gui_app.Api)
    api._cfg = cfg or Config()
    monkeypatch.setattr(gui_app, "save_config", lambda c: None)
    return api


def test_add_and_delete_command(monkeypatch):
    api = _api(monkeypatch)
    res = api.add_command("/review", "Review my changes for bugs. Focus: $INPUT")
    assert "error" not in res
    assert res["commands"] == [{"name": "review",
                                "template": "Review my changes for bugs. Focus: $INPUT"}]
    # re-adding the same name replaces, doesn't duplicate
    api.add_command("review", "New template")
    assert len(api._cfg.commands) == 1 and api._cfg.commands[0]["template"] == "New template"
    res = api.delete_command("review")
    assert res["commands"] == []


def test_command_validation(monkeypatch):
    api = _api(monkeypatch)
    assert "required" in api.add_command("", "x")["error"]
    assert "required" in api.add_command("x", "")["error"]
    assert "may only contain" in api.add_command("bad name!", "t")["error"]


def test_export_chat_writes_markdown(monkeypatch, tmp_path):
    out = tmp_path / "chat.md"

    api = gui_app.Api.__new__(gui_app.Api)
    api.session_id = "s1"
    agent = types.SimpleNamespace(
        workdir=tmp_path,
        messages=[
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "add a hello function"},
            {"role": "assistant", "content": "Done, added hello()."},
            {"role": "assistant", "content": None,
             "tool_calls": [{"id": "t1", "function": {"name": "write_file",
                             "arguments": '{"path": "h.py"}'}}]},
            {"role": "tool", "tool_call_id": "t1", "content": "Created h.py"},
        ])
    cs = types.SimpleNamespace(sid="s1", agent=agent, title="Hello feature")
    api._chats = {"s1": cs}
    api._window = types.SimpleNamespace(
        create_file_dialog=lambda *a, **k: str(out))

    res = api.export_chat()
    assert res.get("ok") and Path(res["path"]) == out
    md = out.read_text(encoding="utf-8")
    assert "# Hello feature" in md
    assert "### You" in md and "add a hello function" in md
    assert "### Agent" in md and "Done, added hello()." in md
    assert "`write_file`" in md          # tool call noted
    assert "sys" not in md               # system prompt never exported


def test_export_no_active_chat():
    api = gui_app.Api.__new__(gui_app.Api)
    api.session_id = None
    api._chats = {}
    assert "error" in api.export_chat()


def test_commands_default_empty():
    assert Config().commands == []
