"""Pasting a screenshot (Ctrl+V): the JS paste handler sends a base64 data
URL; paste_image saves it to a real file under CONFIG_DIR/pasted/ and returns
the same {path, name, thumb} attachment shape as pick_files/attach_paths."""

import base64
import sys
import types
from pathlib import Path

sys.modules.setdefault("webview", types.SimpleNamespace(
    Window=object, FOLDER_DIALOG=object(), OPEN_DIALOG=object(), SAVE_DIALOG=object()))

from glmcode.gui import app as gui_app  # noqa: E402

_PNG_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
_PNG_URL = "data:image/png;base64," + _PNG_B64


def _api(monkeypatch, tmp_path):
    monkeypatch.setattr(gui_app, "CONFIG_DIR", tmp_path)
    return gui_app.Api.__new__(gui_app.Api)


def test_paste_image_saves_png_and_returns_attachment(monkeypatch, tmp_path):
    api = _api(monkeypatch, tmp_path)
    att = api.paste_image(_PNG_URL)
    assert "error" not in att
    p = Path(att["path"])
    assert p.is_file() and p.parent == tmp_path / "pasted"
    assert p.suffix == ".png" and att["name"] == p.name
    assert p.read_bytes() == base64.b64decode(_PNG_B64)  # saved verbatim
    assert att["thumb"].startswith("data:image")         # usable thumbnail


def test_paste_image_extension_follows_mime(monkeypatch, tmp_path):
    api = _api(monkeypatch, tmp_path)
    att = api.paste_image("data:image/jpeg;base64," + _PNG_B64)
    assert Path(att["path"]).suffix == ".jpg"
    # unknown image subtype falls back to .png rather than failing
    att = api.paste_image("data:image/x-odd;base64," + _PNG_B64)
    assert Path(att["path"]).suffix == ".png"


def test_paste_image_two_pastes_never_collide(monkeypatch, tmp_path):
    api = _api(monkeypatch, tmp_path)
    a = api.paste_image(_PNG_URL)
    b = api.paste_image(_PNG_URL)  # same second, same content
    assert a["path"] != b["path"]
    assert Path(a["path"]).is_file() and Path(b["path"]).is_file()


def test_paste_image_rejects_non_image_and_garbage(monkeypatch, tmp_path):
    api = _api(monkeypatch, tmp_path)
    for bad in ("data:text/plain;base64," + _PNG_B64,  # not an image
                "not a data url", "", None):
        res = api.paste_image(bad)
        assert res.get("error")
    assert not list((tmp_path / "pasted").glob("*")) if (tmp_path / "pasted").exists() else True


def test_paste_image_never_raises_on_bad_base64(monkeypatch, tmp_path):
    api = _api(monkeypatch, tmp_path)
    res = api.paste_image("data:image/png;base64,@@@not-base64@@@")
    assert res.get("error")
