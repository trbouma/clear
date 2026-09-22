import pytest

from clear import root_cli, treasury_cli


@pytest.mark.parametrize("command,listed", [("list", True), ("publish", True), ("unlist", False), ("private", False)])
def test_root_listing_commands(command, listed, monkeypatch):
    calls = []
    monkeypatch.setattr(root_cli, "_operator_token", lambda: "test-token")
    monkeypatch.setattr(root_cli, "_api_url", lambda args: "http://localhost:3339")
    monkeypatch.setattr(root_cli, "request_json", lambda *args, **kwargs: calls.append(args) or {})
    args = root_cli.parser().parse_args(["cmu", command, "cmu-test"])
    assert args.handler(args) == 0
    assert calls[0][1:] == ("POST", "/v1/operator/cmus/cmu-test/visibility", {"public_listing": listed})


def test_root_list_without_id_keeps_inventory(monkeypatch):
    calls = []
    monkeypatch.setattr(root_cli, "_operator_token", lambda: "test-token")
    monkeypatch.setattr(root_cli, "_api_url", lambda args: "http://localhost:3339")
    monkeypatch.setattr(root_cli, "request_json", lambda *args, **kwargs: calls.append(args) or {})
    args = root_cli.parser().parse_args(["cmu", "list"])
    assert args.handler(args) == 0
    assert calls[0][1:] == ("GET", "/v1/operator/cmus")


@pytest.mark.parametrize("command,listed", [("list", True), ("publish", True), ("unlist", False), ("private", False)])
def test_treasury_listing_commands(command, listed):
    args = treasury_cli.parser().parse_args([
        "--mint", "https://clear.example", "cmu", command, "--cmu-id", "cmu-test",
    ])
    assert args.handler is treasury_cli.cmu_visibility
    assert args.public_listing is listed
    assert args.cmu_id == "cmu-test"
