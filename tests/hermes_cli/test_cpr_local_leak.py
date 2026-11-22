"""Classic-CLI prompt_toolkit output selection: native Windows keeps prompt_toolkit's default
output unless PROMPT_TOOLKIT_NO_CPR opts in to the CPR-disabled output."""

from __future__ import annotations

import sys

import pytest

from prompt_toolkit.output.color_depth import ColorDepth

from cli import (
    _build_cpr_disabled_output,
    _select_classic_cli_pt_output,
    _terminal_may_leak_cpr,
)

@pytest.fixture(autouse=True)
def _clear_cpr_env(monkeypatch):
    for var in ("SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY", "PROMPT_TOOLKIT_NO_CPR"):
        monkeypatch.delenv(var, raising=False)

class TestClassicCliOutputSelection:

    @pytest.mark.platforms("windows")
    def test_windows_preserves_default_output_selection(self):
        assert _terminal_may_leak_cpr() is False
        assert _select_classic_cli_pt_output(sys.stdout) is None

    @pytest.mark.platforms("windows")
    def test_windows_honors_explicit_no_cpr(self, monkeypatch):
        monkeypatch.setenv("PROMPT_TOOLKIT_NO_CPR", "1")
        assert _terminal_may_leak_cpr() is True
        out = _select_classic_cli_pt_output(sys.stdout)
        # Build may return None if stdout is not a real tty in CI; if it
        # succeeds it must be CPR-disabled.
        assert out is None or out.enable_cpr is False


class TestCprDisabledOutputColorDepth:

    @pytest.fixture(autouse=True)
    def _clear_color_env(self, monkeypatch):
        for var in ("NO_COLOR", "PROMPT_TOOLKIT_COLOR_DEPTH", "COLORTERM"):
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv("TERM", "xterm-256color")

    def test_honors_prompt_toolkit_color_depth(self, monkeypatch):
        monkeypatch.setenv("PROMPT_TOOLKIT_COLOR_DEPTH", "DEPTH_24_BIT")
        out = _build_cpr_disabled_output(sys.stdout)
        assert out.get_default_color_depth() is ColorDepth.DEPTH_24_BIT

    @pytest.mark.parametrize("colorterm", ["truecolor", "24bit"])
    def test_colorterm_selects_true_color(self, monkeypatch, colorterm):
        monkeypatch.setenv("COLORTERM", colorterm)
        out = _build_cpr_disabled_output(sys.stdout)
        assert out.get_default_color_depth() is ColorDepth.DEPTH_24_BIT

    def test_explicit_depth_wins_over_colorterm(self, monkeypatch):
        monkeypatch.setenv("COLORTERM", "truecolor")
        monkeypatch.setenv("PROMPT_TOOLKIT_COLOR_DEPTH", "DEPTH_8_BIT")
        out = _build_cpr_disabled_output(sys.stdout)
        assert out.get_default_color_depth() is ColorDepth.DEPTH_8_BIT

    def test_dumb_term_keeps_monochrome(self, monkeypatch):
        monkeypatch.setenv("TERM", "dumb")
        out = _build_cpr_disabled_output(sys.stdout)
        assert out.get_default_color_depth() is ColorDepth.DEPTH_1_BIT

    def test_without_hints_keeps_prompt_toolkit_default(self):
        out = _build_cpr_disabled_output(sys.stdout)
        assert out.get_default_color_depth() is ColorDepth.DEFAULT
