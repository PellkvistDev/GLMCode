"""Bring-your-own-model: provider config, per-chat model override, and the
vision-client split for custom providers."""

import json

import glmcode.config as config
from glmcode.config import (BUILTIN_PROVIDER_NAME, Config, all_providers,
                            builtin_provider, find_provider, load_config,
                            save_config)
from glmcode.sessions import SessionStore

from conftest import FakeResult, tool_call


def test_builtin_provider_always_first():
    cfg = Config()
    provs = all_providers(cfg)
    assert provs[0]["name"] == BUILTIN_PROVIDER_NAME
    assert provs[0]["builtin"] is True
    assert cfg.model in provs[0]["models"]


def test_find_provider():
    cfg = Config(providers=[{"name": "OpenRouter", "base_url": "https://x/v1",
                             "api_key": "k", "models": ["m1"]}])
    assert find_provider(cfg, "OpenRouter")["base_url"] == "https://x/v1"
    assert find_provider(cfg, BUILTIN_PROVIDER_NAME)["builtin"] is True
    assert find_provider(cfg, "nope") is None


def test_providers_roundtrip_through_config_file(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    cfg = Config(providers=[{"name": "Local", "base_url": "http://l/v1",
                             "api_key": "", "models": ["a", "b"]}])
    save_config(cfg)
    loaded = load_config()
    assert loaded.providers == cfg.providers


def test_session_stores_model_choice(tmp_path):
    store = SessionStore(root=tmp_path)
    store.save("s1", "/proj", [{"role": "user", "content": "hi"}], 1, 1,
               model_provider="Ollama (local)", model="llama3:8b")
    data = store.load("s1")
    assert data["model_provider"] == "Ollama (local)"
    assert data["model"] == "llama3:8b"


def test_agent_uses_model_override(scripted_agent):
    seen = {}

    def script(n):
        return FakeResult(content="hi")

    agent = scripted_agent(script)
    orig_chat = agent.client.chat

    def spy(**kwargs):
        seen["model"] = kwargs.get("model")
        return orig_chat(**kwargs)

    agent.client.chat = spy
    agent.model_override = "custom/model-x"
    agent.run_turn({"role": "user", "content": "q"})
    assert seen["model"] == "custom/model-x"


def test_client_for_routes_vision_to_vision_client(scripted_agent):
    agent = scripted_agent()
    other = object()
    agent.vision_client = other
    assert agent._client_for(agent.cfg.vision_model) is other
    assert agent._client_for("anything-else") is agent.client
    agent.vision_client = None
    assert agent._client_for(agent.cfg.vision_model) is agent.client


def test_subagent_inherits_model_override(scripted_agent):
    from conftest import ScriptedClient
    coord = scripted_agent(allow_subagents=True)
    coord.model_override = "custom/model-x"
    seen = []

    def sub_script(n):
        return FakeResult(content="report")

    ScriptedClient.scripts = [sub_script]
    orig_init = ScriptedClient.__init__

    coord._run_subagents([{"name": "w", "task": "t"}])
    # the coordinator's report path worked; verify the override reached the
    # sub-agent by checking the recorded transcript of models isn't possible
    # via ScriptedClient (it ignores model), so assert via a fresh sub run:
    # simplest -- the propagation line itself:
    # (covered indirectly; direct check below)
    import glmcode.agent as agent_mod
    sub_holder = {}
    real_run = agent_mod.Agent.run_turn

    def capture_run(self, msg):
        sub_holder["override"] = self.model_override
        return real_run(self, msg)

    ScriptedClient.scripts = [sub_script]
    agent_mod.Agent.run_turn = capture_run
    try:
        coord._run_subagents([{"name": "w", "task": "t"}])
    finally:
        agent_mod.Agent.run_turn = real_run
    assert sub_holder["override"] == "custom/model-x"
