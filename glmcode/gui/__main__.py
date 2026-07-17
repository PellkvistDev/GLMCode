"""Entry point for `python -m glmcode.gui`."""
import sys
import traceback


def _show_error(title: str, message: str) -> None:
    """Show a visible error dialog even under pythonw (no console)."""
    try:
        import tkinter.messagebox as mb
        mb.showerror(title, message)
    except Exception:
        # Last resort: write to a file the user can find
        try:
            from pathlib import Path
            (Path.home() / ".makenomistakes" / "crash.log").write_text(
                f"{title}\n\n{message}", encoding="utf-8"
            )
        except OSError:
            pass


if __name__ == "__main__":
    try:
        from .app import main
        main()
    except Exception:
        _show_error("Make No Mistakes crashed", traceback.format_exc())
        sys.exit(1)
