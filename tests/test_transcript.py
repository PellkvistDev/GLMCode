"""Append-only conversation transcripts: written through Agent hooks, and --
the whole point -- still intact after compaction wipes the live context."""

import json

from glmcode.transcript import Transcript, search_sessions

from conftest import FakeResult, tool_call


def make_transcript(tmp_path, sid="chat-1"):
    return Transcript(sid, cwd="/proj", root=tmp_path)


def test_basic_entries_and_header(tmp_path):
    t = make_transcript(tmp_path)
    t.user("hello there")
    t.assistant("hi!", ["read_file({\"path\": \"x\"})"])
    t.tool_result("read_file", "the contents")
    t.marker("context compacted here")
    text = t.path.read_text(encoding="utf-8")
    assert text.startswith("# Chat transcript\nProject: /proj\n")
    assert "## User [" in text and "hello there" in text
    assert "## Assistant [" in text and "-> tool call: read_file" in text
    assert "### tool result: read_file\nthe contents" in text
    assert "*context compacted here*" in text


def test_tool_result_truncated(tmp_path):
    t = make_transcript(tmp_path)
    t.tool_result("grep", "y" * 10_000)
    text = t.path.read_text(encoding="utf-8")
    assert "truncated; full result was 10000 chars" in text
    assert "y" * 2000 not in text


def test_empty_entries_write_nothing(tmp_path):
    t = make_transcript(tmp_path)
    t.user("   ")
    t.assistant("", [])
    assert not t.path.exists()


def test_delete(tmp_path):
    t = make_transcript(tmp_path)
    t.user("x")
    assert t.path.exists()
    t.delete()
    assert not t.path.exists()


def test_prompt_note_names_the_paths(tmp_path):
    t = make_transcript(tmp_path)
    note = t.prompt_note()
    assert str(t.path) in note
    assert str(tmp_path) in note
    assert "grep" in note


def test_agent_logs_full_turn(scripted_agent, tmp_path):
    def script(n):
        if n == 1:
            return FakeResult([tool_call("c1", "list_dir")])
        return FakeResult(content="all done, here is the answer")

    agent = scripted_agent(script)
    agent.transcript = make_transcript(tmp_path)
    agent.run_turn({"role": "user", "content": "please inspect the project"})

    text = agent.transcript.path.read_text(encoding="utf-8")
    assert "please inspect the project" in text
    assert "-> tool call: list_dir" in text
    assert "### tool result: list_dir" in text
    assert "all done, here is the answer" in text


def test_transcript_survives_compaction(scripted_agent, tmp_path):
    # The session store persists the model's CURRENT context, so compaction
    # destroys history on disk too. The transcript must keep everything.
    agent = scripted_agent(lambda n: FakeResult(content=f"answer {n}"))
    agent.transcript = make_transcript(tmp_path)
    agent.run_turn({"role": "user", "content": "the SECRET launch code is 4471"})
    agent.run_turn({"role": "user", "content": "second question"})

    agent.compact()  # scripted client's tools=None branch acts as summarizer
    live = json.dumps(agent.messages)
    assert "4471" not in live, "test setup wrong: compaction kept the context"

    text = agent.transcript.path.read_text(encoding="utf-8")
    assert "the SECRET launch code is 4471" in text
    assert "Context compacted here" in text


def test_system_prompt_advertises_transcript(scripted_agent, tmp_path):
    agent = scripted_agent()
    agent.transcript = make_transcript(tmp_path)
    agent.rebuild_system_prompt()
    sp = agent.messages[0]["content"]
    assert "Conversation transcripts" in sp
    assert str(agent.transcript.path) in sp


def test_compact_summary_names_transcript_path(scripted_agent, tmp_path):
    agent = scripted_agent(lambda n: FakeResult(content=f"answer {n}"))
    agent.transcript = make_transcript(tmp_path)
    agent.run_turn({"role": "user", "content": "first"})
    agent.run_turn({"role": "user", "content": "second"})
    agent.compact()
    # The post-compaction context tells the model exactly where the lost
    # details live.
    assert str(agent.transcript.path) in agent.messages[1]["content"]


def test_set_title_written_once(tmp_path):
    t = make_transcript(tmp_path)
    t.user("hello")
    t.set_title("Fixing The Login Bug")
    assert "Title: Fixing The Login Bug" in t.path.read_text(encoding="utf-8")


def test_search_matches_transcript_content(tmp_path):
    t1 = Transcript("chat-1", root=tmp_path)
    t1.user("we discussed the kubernetes ingress config here")
    t2 = Transcript("chat-2", root=tmp_path)
    t2.user("this chat is about css grid layouts")
    sessions = [
        {"id": "chat-1", "title": "Infra work", "cwd": "/a", "updated": "1"},
        {"id": "chat-2", "title": "Frontend", "cwd": "/b", "updated": "2"},
        {"id": "chat-3", "title": "No transcript here", "cwd": "/c", "updated": "3"},
    ]
    hits = search_sessions(sessions, "kubernetes", root=tmp_path)
    assert [h["id"] for h in hits] == ["chat-1"]
    assert "kubernetes ingress" in hits[0]["snippet"]


def test_search_matches_title_even_without_transcript(tmp_path):
    sessions = [{"id": "chat-3", "title": "Rust rewrite plan", "cwd": "/c", "updated": "3"}]
    hits = search_sessions(sessions, "rust", root=tmp_path)
    assert len(hits) == 1


def test_search_empty_query_returns_everything(tmp_path):
    sessions = [{"id": "a", "title": "x", "cwd": "", "updated": ""}]
    assert search_sessions(sessions, "  ", root=tmp_path) == sessions


def test_search_long_line_snippet_centers_match(tmp_path):
    t = Transcript("chat-long", root=tmp_path)
    t.user("padding " * 60 + "NEEDLE9000 " + "trailing " * 40)
    sessions = [{"id": "chat-long", "title": "t", "cwd": "", "updated": ""}]
    hits = search_sessions(sessions, "needle9000", root=tmp_path)
    assert len(hits) == 1
    assert "NEEDLE9000" in hits[0]["snippet"]
    assert len(hits[0]["snippet"]) < 200


def test_steering_logged_with_label(scripted_agent, tmp_path):
    holder = {}

    def script(n):
        if n == 1:
            holder["a"].steer("focus on the tests")
            return FakeResult([tool_call("c1")])
        return FakeResult(content="done")

    agent = scripted_agent(script)
    holder["a"] = agent
    agent.transcript = make_transcript(tmp_path)
    agent.run_turn({"role": "user", "content": "go"})
    text = agent.transcript.path.read_text(encoding="utf-8")
    assert "## User (steering) [" in text
    assert "focus on the tests" in text
    # the framing boilerplate stays out of the transcript
    assert "NOT a new task" not in text
