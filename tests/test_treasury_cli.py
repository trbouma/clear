from __future__ import annotations

import json

from stroma import Event, Keys

from clear import treasury_cli
from clear.treasury_auth import TREASURY_EVENT_KIND


def test_treasury_cli_cmu_create_signs_and_posts_envelope(monkeypatch, capsys) -> None:
    calls = []
    treasurer = Keys(priv_k="1".zfill(64))

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        event = Event.load(payload["event"], validate=True)
        assert event is not None
        content = json.loads(event.content)
        assert event.kind == TREASURY_EVENT_KIND
        assert event.pub_key == treasurer.public_key_hex()
        assert content["action"] == "cmu:create"
        assert content["grant_id"] == "grant-id"
        assert content["mint"] == "https://clear.example"
        assert content["name"] == "Gym Guest Passes"
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "friendly_name": content["name"],
            "status": "active",
        }

    monkeypatch.setattr(treasury_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example/",
            "--nsec",
            treasurer.private_key_bech32(),
            "cmu",
            "create",
            "grant-id",
            "--name",
            "Gym Guest Passes",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["unit"] == "cmu-created"
    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert calls[0][:3] == (
        "https://clear.example",
        "POST",
        "/v1/treasury/cmus",
    )
    assert calls[0][4] is None


def test_treasury_cli_cmu_info_signs_and_posts_envelope(monkeypatch, capsys) -> None:
    calls = []
    treasurer = Keys(priv_k="1".zfill(64))

    def fake_request_json(mint_url, method, path, payload=None, *, token=None):
        calls.append((mint_url, method, path, payload, token))
        event = Event.load(payload["event"], validate=True)
        assert event is not None
        content = json.loads(event.content)
        assert event.kind == TREASURY_EVENT_KIND
        assert event.pub_key == treasurer.public_key_hex()
        assert content["action"] == "cmu:info"
        assert content["mint"] == "https://clear.example"
        return {
            "unit": "cmu-created",
            "keyset_id": "keyset-created",
            "friendly_name": "Gym Guest Passes",
            "status": "active",
            "treasurer_npub": treasurer.public_key_bech32(),
        }

    monkeypatch.setattr(treasury_cli, "request_json", fake_request_json)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example/",
            "--nsec",
            treasurer.private_key_bech32(),
            "cmu",
            "info",
        ],
    )

    assert treasury_cli.main() == 0
    output = json.loads(capsys.readouterr().out)

    assert output["unit"] == "cmu-created"
    assert output["treasurer_npub"] == treasurer.public_key_bech32()
    assert calls[0][:3] == (
        "https://clear.example",
        "POST",
        "/v1/treasury/cmus/info",
    )
    assert calls[0][4] is None


def test_treasury_cli_requires_nsec(monkeypatch, capsys) -> None:
    monkeypatch.delenv("CLEAR_TREASURER_NSEC", raising=False)
    monkeypatch.setattr(
        "sys.argv",
        [
            "clear-treasury",
            "--mint",
            "https://clear.example",
            "cmu",
            "create",
            "grant-id",
        ],
    )

    assert treasury_cli.main() == 1
    assert "treasurer nsec must be supplied" in capsys.readouterr().err
