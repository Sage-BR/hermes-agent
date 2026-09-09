"""Regressions for atomic multiline paste handling in the interactive TUI."""

from types import SimpleNamespace
from unittest.mock import Mock

from hermes_cli.cli_tui_mixin import CLITuiMixin
from hermes_cli import pt_input_extras


class _Buffer:
    def __init__(self, text=""):
        self.text = text
        self.cursor_position = len(text)

    def insert_text(self, value):
        self.text = self.text[:self.cursor_position] + value + self.text[self.cursor_position:]
        self.cursor_position += len(value)


def _cli_for_paste():
    cli = CLITuiMixin.__new__(CLITuiMixin)
    cli._tui_prev_text_len = 0
    cli._tui_prev_newline_count = 0
    cli._tui_paste_just_collapsed = False
    cli._skip_paste_collapse = False
    cli._tui_atomic_paste_depth = 0
    cli._tui_paste_counter = 0
    cli._tui_raw_paste_until = 0.0
    cli._tui_raw_paste_seen = False
    cli._tui_raw_paste_active = False
    cli._tui_raw_paste_payload = ""
    cli._tui_raw_paste_placeholder = ""
    cli._tui_raw_paste_number = 0
    cli._tui_raw_paste_file = None
    cli._tui_raw_paste_window_started = 0.0
    cli._tui_raw_paste_window_chars = 0
    cli.config = {
        "paste_collapse_threshold": 0,
        "paste_collapse_threshold_fallback": 0,
        "paste_collapse_char_threshold": 0,
    }
    return cli


def test_large_windows_paste_patch_is_installed():
    pt_input_extras.install_windows_paste_batch()
    from prompt_toolkit.input.win32 import ConsoleInputReader

    assert getattr(ConsoleInputReader.read, "_hermes_large_paste_batch", False) is True
    assert 262144 in ConsoleInputReader.read.__code__.co_consts


def test_raw_multiline_paste_hides_partial_batches_immediately(monkeypatch, tmp_path):
    import cli as cli_module

    cli = _cli_for_paste()
    cli.config["paste_collapse_threshold_fallback"] = 1
    monkeypatch.setattr(cli_module, "_hermes_home", tmp_path)
    buf = _Buffer("abcdefghijklmnop")

    cli._tui_on_text_changed(buf)
    buf.text += "\nparte seguinte"
    buf.cursor_position = len(buf.text)
    cli._tui_on_text_changed(buf)

    assert cli._tui_raw_paste_guard_active() is True
    assert cli._tui_raw_paste_active is True
    assert buf.text.startswith("[Pasted text #1: 2 lines")

    buf.text += "\nterceira parte"
    buf.cursor_position = len(buf.text)
    cli._tui_on_text_changed(buf)
    assert buf.text.startswith("[Pasted text #1: 2 lines")
    cli._tui_finalize_raw_paste(buf)
    assert buf.text.startswith("[Pasted text #1: 3 lines")
    paste_file = next((tmp_path / "pastes").glob("*.txt"))
    assert paste_file.read_text(encoding="utf-8") == "abcdefghijklmnop\nparte seguinte\nterceira parte"


def test_raw_paste_enter_becomes_buffer_newline_not_submission():
    cli = _cli_for_paste()
    cli._tui_enter_overlay = lambda event: False
    cli._tui_raw_paste_until = 9999999999.0
    buf = _Buffer("parte 1")
    event = SimpleNamespace(
        current_buffer=buf,
        app=SimpleNamespace(current_buffer=buf, invalidate=lambda: None),
    )

    cli._tui_handle_enter(event)

    assert buf.text == "parte 1\n"


def test_markerless_paste_is_collapsed_after_input_quiet(monkeypatch, tmp_path):
    import cli as cli_module

    cli = _cli_for_paste()
    cli.config["paste_collapse_threshold_fallback"] = 5
    cli._tui_raw_paste_seen = True
    monkeypatch.setattr(cli_module, "_hermes_home", tmp_path)
    buf = _Buffer("\n".join(f"linha {i}" for i in range(1, 201)))

    cli._tui_finalize_raw_paste(buf)

    assert buf.text.startswith("[Pasted text #1: 200 lines")
    assert len(list((tmp_path / "pastes").glob("*.txt"))) == 1


def test_bracketed_paste_inserts_complete_payload_once():
    cli = _cli_for_paste()
    cli._attached_images = []
    cli._try_attach_clipboard_image = lambda: False
    cli._recover_terminal_input_modes = lambda **kwargs: None
    buf = _Buffer()
    event = SimpleNamespace(
        data="linha 1\r\nlinha 2\r\nlinha 3",
        current_buffer=buf,
        app=SimpleNamespace(invalidate=lambda: None),
    )

    cli._tui_handle_paste(event)

    assert buf.text == "linha 1\nlinha 2\nlinha 3"
    assert cli._tui_raw_paste_until == 0.0


def test_large_bracketed_paste_becomes_one_file_reference(monkeypatch, tmp_path):
    import cli as cli_module

    cli = _cli_for_paste()
    cli.config["paste_collapse_threshold"] = 5
    cli._attached_images = []
    cli._try_attach_clipboard_image = lambda: False
    cli._recover_terminal_input_modes = lambda **kwargs: None
    monkeypatch.setattr(cli_module, "_hermes_home", tmp_path)
    buf = _Buffer()
    event = SimpleNamespace(
        data="\n".join(f"linha {i}" for i in range(1, 201)),
        current_buffer=buf,
        app=SimpleNamespace(invalidate=lambda: None),
    )

    cli._tui_handle_paste(event)

    assert buf.text.startswith("[Pasted text #1: 200 lines")
    assert len(list((tmp_path / "pastes").glob("*.txt"))) == 1


def test_process_input_previews_marker_but_sends_full_paste(tmp_path):
    from cli import HermesCLI

    pasted = "linha 1\nlinha 2\nlinha 3"
    paste_file = tmp_path / "paste.txt"
    paste_file.write_text(pasted, encoding="utf-8")
    marker = f"[Pasted text #1: 3 lines → {paste_file}]"

    cli = HermesCLI.__new__(HermesCLI)
    cli._tui_unwrap_input = lambda value: (value, False, False)
    cli._status_bar_suppressed_after_resize = False
    cli._typed_voice_stop = lambda value: False
    cli._pending_resume_sessions = []
    cli.handle_bang_shell = lambda value: False
    cli._tui_run_slash_input = lambda value: value
    cli._print_user_message_preview = Mock()
    cli._app = SimpleNamespace(invalidate=lambda: None)
    cli._turn_summary_begin = lambda: None
    cli._tui_after_turn = lambda: None
    cli._agent_running = False
    cli._pet_turn_error = False
    cli._pet_reasoning = False
    cli.chat = Mock()

    cli._tui_process_one_input(marker)

    assert cli._print_user_message_preview.call_args.args[0] == marker
    assert cli.chat.call_args.args[0] == pasted
