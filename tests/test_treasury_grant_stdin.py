import io
import json
import os

import pytest
from stroma import Keys

from clear import treasury_cli
from clear.treasury_auth import verify_envelope


def grant_for(keys):
    return {"id": "grant-id", "mint_url": "https://clear.example", "npub": keys.public_key_bech32(), "status": "pending", "scope": "keyset:create"}


@pytest.mark.skipif(not hasattr(os, "openpty"), reason="requires POSIX pseudo-terminals")
def test_grant_prompts_use_nonseekable_terminal(monkeypatch):
    keys = Keys(priv_k="1".zfill(64))
    monkeypatch.setenv("CLEAR_TREASURER_NSEC", keys.private_key_bech32())
    monkeypatch.setattr(treasury_cli.sys, "stdin", io.StringIO(json.dumps(grant_for(keys))))
    master, slave = os.openpty()
    try:
        tty_path = os.ttyname(slave)

        def terminal_open(path, mode, **kwargs):
            assert path == "/dev/tty"
            flags = os.O_RDONLY if mode == "r" else os.O_WRONLY
            descriptor = os.open(tty_path, flags | os.O_NOCTTY)
            return os.fdopen(descriptor, mode, **kwargs)

        monkeypatch.setattr(treasury_cli, "open", terminal_open, raising=False)
        os.write(master, b"Community Credits\ncredits\n")
        args = treasury_cli.parser().parse_args(["cmu", "create", "--grant-stdin"])
        treasury_cli._prompt_grant_details(args)
        assert args.name == "Community Credits"
        assert args.unit_alias == "credits"
        assert args.mint == "https://clear.example"
    finally:
        os.close(master)
        os.close(slave)


class Terminal(io.StringIO):
    def __init__(self):
        super().__init__()
        self.answers = iter(["Community Credits\n", "credits\n"])

    def readline(self):
        return next(self.answers, "")


@pytest.mark.parametrize("source", ["stdin", "file"])
def test_piped_grant_prompts_and_posts_signed_request(monkeypatch, capsys, tmp_path, source):
    keys = Keys(priv_k="1".zfill(64))
    monkeypatch.delenv("CLEAR_TREASURER_NSEC", raising=False)
    monkeypatch.setattr(treasury_cli.sys, "stdin", io.StringIO(json.dumps(grant_for(keys))))
    monkeypatch.setattr(treasury_cli, "open", lambda *a, **kw: Terminal(), raising=False)
    monkeypatch.setattr(treasury_cli.getpass, "getpass", lambda *a, **kw: keys.private_key_bech32())
    calls = []

    def request(mint, method, path, envelope):
        payload, _ = verify_envelope(envelope, expected_action="cmu:create", expected_mint=mint)
        assert payload["grant_id"] == "grant-id"
        assert payload["name"] == "Community Credits"
        assert payload["unit_alias"] == "credits"
        assert keys.private_key_bech32() not in json.dumps(envelope)
        calls.append(path)
        return {"unit": "cmu-test"}

    monkeypatch.setattr(treasury_cli, "request_json", request)
    options = ["--grant-stdin"]
    if source == "file":
        path = tmp_path / "grant.json"
        path.write_text(json.dumps(grant_for(keys)), encoding="utf-8")
        options = ["--grant-file", str(path)]
        monkeypatch.setattr(treasury_cli.sys, "stdin", io.StringIO("not grant JSON"))
    args = treasury_cli.parser().parse_args(["cmu", "create", *options])
    assert args.handler(args) == 0
    assert calls == ["/v1/treasury/cmus"]
    assert json.loads(capsys.readouterr().out)["unit"] == "cmu-test"


@pytest.mark.parametrize("contents", [None, "invalid json", "[]"])
def test_grant_file_errors(monkeypatch, tmp_path, contents):
    path = tmp_path / "grant.json"
    if contents is not None:
        path.write_text(contents, encoding="utf-8")
    args = treasury_cli.parser().parse_args(["cmu", "create", "--grant-file", str(path)])
    with pytest.raises(treasury_cli.TreasuryError, match="grant JSON object"):
        args.handler(args)


def test_grant_file_cannot_be_combined_with_other_sources():
    for extra in (["--grant-stdin"], ["grant-id"]):
        with pytest.raises(SystemExit):
            treasury_cli.parser().parse_args(["cmu", "create", "--grant-file", "grant.json", *extra])


@pytest.mark.parametrize("change", [{"status": "revoked"}, {"scope": "wrong"}, {"mint_url": "file:///tmp/test"}, {"id": None}])
def test_invalid_grant_rejected_before_prompt(monkeypatch, change):
    grant = {**grant_for(Keys(priv_k="1".zfill(64))), **change}
    monkeypatch.setattr(treasury_cli.sys, "stdin", io.StringIO(json.dumps(grant)))
    args = treasury_cli.parser().parse_args(["cmu", "create", "--grant-stdin"])
    with pytest.raises(treasury_cli.TreasuryError):
        args.handler(args)


def test_piped_grant_rejects_wrong_key(monkeypatch):
    keys = Keys(priv_k="1".zfill(64))
    monkeypatch.setattr(treasury_cli.sys, "stdin", io.StringIO(json.dumps(grant_for(keys))))
    monkeypatch.setattr(treasury_cli, "open", lambda *a, **kw: Terminal(), raising=False)
    args = treasury_cli.parser().parse_args(["--nsec", Keys(priv_k="2".zfill(64)).private_key_bech32(), "cmu", "create", "--grant-stdin"])
    with pytest.raises(treasury_cli.TreasuryError, match="does not match"):
        args.handler(args)


def test_piped_grant_requires_terminal(monkeypatch):
    grant = grant_for(Keys(priv_k="1".zfill(64)))
    monkeypatch.setattr(treasury_cli.sys, "stdin", io.StringIO(json.dumps(grant)))

    def unavailable(*args, **kwargs):
        raise OSError("no controlling terminal")

    monkeypatch.setattr(treasury_cli, "open", unavailable, raising=False)
    args = treasury_cli.parser().parse_args(["cmu", "create", "--grant-stdin"])
    with pytest.raises(treasury_cli.TreasuryError, match="requires a terminal"):
        args.handler(args)


def test_piped_grant_rejects_conflicting_mint(monkeypatch):
    grant = grant_for(Keys(priv_k="1".zfill(64)))
    monkeypatch.setattr(treasury_cli.sys, "stdin", io.StringIO(json.dumps(grant)))
    args = treasury_cli.parser().parse_args(["--mint", "https://other.example", "cmu", "create", "--grant-stdin"])
    with pytest.raises(treasury_cli.TreasuryError, match="does not match"):
        args.handler(args)


@pytest.mark.parametrize("arguments", [["cmu", "create"], ["--mint", "https://clear.example", "cmu", "create"], ["cmu", "create", "grant-id", "--grant-stdin"], ["cmu", "list", "--cmu-id", "cmu-test"]])
def test_creation_parser_preserves_required_arguments(arguments):
    with pytest.raises(SystemExit):
        treasury_cli.parser().parse_args(arguments)
