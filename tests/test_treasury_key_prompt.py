import argparse
import io
import warnings
from unittest.mock import Mock

import pytest

from clear import treasury_cli
from clear.treasury import TreasuryError


@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_key_prompts_once_without_output(monkeypatch, capsys, value):
    monkeypatch.delenv("CLEAR_TREASURER_NSEC", raising=False)
    monkeypatch.setattr(treasury_cli, "open", lambda *a, **kw: io.StringIO(), raising=False)
    prompt = Mock(return_value="private-test-key")
    monkeypatch.setattr(treasury_cli.getpass, "getpass", prompt)
    args = argparse.Namespace(nsec=value)
    assert treasury_cli._treasurer_nsec(args) == "private-test-key"
    assert treasury_cli._treasurer_nsec(args) == "private-test-key"
    assert prompt.call_count == 1
    captured = capsys.readouterr()
    assert "private-test-key" not in captured.out + captured.err


def test_explicit_key_then_environment_precedence(monkeypatch):
    monkeypatch.setenv("CLEAR_TREASURER_NSEC", "environment-key")
    prompt = Mock(side_effect=AssertionError("No prompt expected"))
    monkeypatch.setattr(treasury_cli.getpass, "getpass", prompt)
    assert treasury_cli._treasurer_nsec(argparse.Namespace(nsec="explicit-key")) == "explicit-key"
    assert treasury_cli._treasurer_nsec(argparse.Namespace(nsec="")) == "environment-key"
    prompt.assert_not_called()


@pytest.mark.parametrize("failure", ["echo", "empty", "eof", "interrupt"])
def test_prompt_never_falls_back_to_echo(monkeypatch, failure):
    monkeypatch.delenv("CLEAR_TREASURER_NSEC", raising=False)
    monkeypatch.setattr(treasury_cli, "open", lambda *a, **kw: io.StringIO(), raising=False)
    def prompt(*a, **kw):
        if failure == "echo":
            warnings.warn("Cannot hide input", treasury_cli.getpass.GetPassWarning)
            pytest.fail("Must stop before echoing input")
        if failure == "eof":
            raise EOFError()
        if failure == "interrupt":
            raise KeyboardInterrupt()
        return ""
    monkeypatch.setattr(treasury_cli.getpass, "getpass", prompt)
    expected = {"echo": TreasuryError, "empty": TreasuryError,
                "eof": EOFError, "interrupt": KeyboardInterrupt}[failure]
    with pytest.raises(expected):
        treasury_cli._treasurer_nsec(argparse.Namespace(nsec=None))
