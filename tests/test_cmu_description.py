import pytest

from clear import root_cli, treasury_cli
from clear.cmu_description import read_description


@pytest.mark.parametrize("cli", [root_cli, treasury_cli])
def test_description_cli_sources(cli, tmp_path):
    prefix = ["cmu", "describe"]
    if cli is treasury_cli:
        prefix = ["--mint", "https://clear.example"] + prefix
    selector = ["cmu-test"] if cli is root_cli else ["--cmu-id", "cmu-test"]
    parse = cli.parser().parse_args
    description_file = tmp_path / "description.txt"
    description_file.write_text("First paragraph.\n\nSecond paragraph.", encoding="utf-8")
    args = parse(prefix + selector + ["--description-file", str(description_file)])
    assert read_description(args) == "First paragraph.\n\nSecond paragraph."
    assert read_description(parse(prefix + selector + ["--clear"])) == ""
    assert read_description(parse(prefix + selector + ["--description", "Meals"])) == "Meals"
    with pytest.raises(SystemExit):
        parse(prefix + selector)
    with pytest.raises(SystemExit):
        parse(prefix + selector + ["--clear", "--description", "Meals"])
    with pytest.raises(ValueError, match="10000"):
        read_description(parse(prefix + selector + ["--description", "x" * 10001]))
    with pytest.raises(ValueError, match="could not read"):
        read_description(parse(prefix + selector + ["--description-file", str(tmp_path / "missing")]))


def test_description_requires_explicit_treasury_cmu():
    with pytest.raises(SystemExit):
        treasury_cli.parser().parse_args(["--mint", "https://clear.example", "cmu", "describe", "--description", "Meals"])


def test_treasury_description_resolves_cmu_and_signs(monkeypatch):
    from stroma import Keys
    from clear.treasury_auth import verify_envelope

    treasurer = Keys(priv_k="1".zfill(64))
    calls = []

    def request(mint, method, path, payload=None):
        calls.append(path)
        if method == "GET":
            return {"keysets": [{"unit": "cmu-test", "id": "keyset-test"}]}
        content, _ = verify_envelope(payload, expected_action="cmu:description", expected_mint=mint)
        assert content["keyset_id"] == "keyset-test"
        assert content["description"] == "Meals"
        return {"description": "Meals"}

    monkeypatch.setattr(treasury_cli, "request_json", request)
    args = treasury_cli.parser().parse_args([
        "--mint", "https://clear.example", "--nsec", treasurer.private_key_bech32(),
        "cmu", "describe", "--cmu-id", "cmu-test", "--description", "Meals",
    ])
    assert args.handler(args) == 0
    assert calls == ["/v1/keysets", "/v1/treasury/cmus/description"]
