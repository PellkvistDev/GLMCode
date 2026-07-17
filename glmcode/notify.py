"""OS-level notifications, dependency-free and best-effort.

Used when a chat needs the user's attention while they are working in
another window: a permission prompt is blocking, or a turn finished and
the agent is waiting. Windows gets a native toast via PowerShell's WinRT
bridge, macOS goes through osascript, Linux through notify-send. Every
failure (missing binary, weird desktop, sandbox) is swallowed -- a missed
toast must never break a turn.
"""

from __future__ import annotations

import subprocess
import sys
import threading

from .tools import NO_WINDOW_KWARGS

APP_NAME = "Make No Mistakes"

# Showing a toast on Windows requires a registered AppUserModelID; using
# PowerShell's own id is the standard trick that lets an unpackaged app
# toast without touching the registry.
_PS_APP_ID = (r"{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}"
              r"\WindowsPowerShell\v1.0\powershell.exe")


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&apos;"))


def _ps_quote(s: str) -> str:
    """PowerShell single-quoted literal: only ' needs doubling."""
    return "'" + s.replace("'", "''") + "'"


def _as_quote(s: str) -> str:
    """AppleScript double-quoted literal."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _command(title: str, body: str, platform: str | None = None) -> list[str]:
    plat = platform or sys.platform
    title, body = title[:100], body[:200]
    if plat.startswith("win"):
        xml = ('<toast><visual><binding template="ToastGeneric">'
               f"<text>{_xml_escape(title)}</text>"
               f"<text>{_xml_escape(body)}</text>"
               "</binding></visual></toast>")
        script = (
            "$null = [Windows.UI.Notifications.ToastNotificationManager, "
            "Windows.UI.Notifications, ContentType = WindowsRuntime];"
            "$null = [Windows.Data.Xml.Dom.XmlDocument, "
            "Windows.Data.Xml.Dom, ContentType = WindowsRuntime];"
            "$x = New-Object Windows.Data.Xml.Dom.XmlDocument;"
            f"$x.LoadXml({_ps_quote(xml)});"
            "$t = New-Object Windows.UI.Notifications.ToastNotification $x;"
            "[Windows.UI.Notifications.ToastNotificationManager]::"
            f"CreateToastNotifier({_ps_quote(_PS_APP_ID)}).Show($t)")
        return ["powershell", "-NoProfile", "-NonInteractive",
                "-Command", script]
    if plat == "darwin":
        return ["osascript", "-e",
                f"display notification {_as_quote(body)} "
                f"with title {_as_quote(title)}"]
    return ["notify-send", "--app-name", APP_NAME, title, body]


def _run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, capture_output=True, timeout=15, **NO_WINDOW_KWARGS)
    except Exception:
        pass


def notify(title: str, body: str) -> None:
    """Fire-and-forget: never blocks the caller (the PowerShell toast in
    particular takes ~1s to spin up) and never raises."""
    threading.Thread(target=_run, args=(_command(title, body),),
                     daemon=True, name="os-notify").start()
