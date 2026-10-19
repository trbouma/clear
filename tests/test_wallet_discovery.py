from copy import deepcopy
from unittest.mock import Mock

import pytest
from stroma import Keys

from clear import root_delivery
from clear import wallet_discovery as discovery

KEY = Keys(priv_k="01" * 32).public_key_hex()
SOCIAL = Keys(priv_k="02" * 32).public_key_hex()
ADDRESS = "alice@example.com"


def document():
    return {
        "version": 1,
        "address": ADDRESS,
        "pubkey": KEY,
        "relays": ["wss://wallet.example"],
        "capabilities": {
            "clear-token-transfer": {"transports": ["nip59"], "kinds": [7379]}
        },
    }


def test_wallet_key_only_and_no_mint_restriction(monkeypatch):
    payload = document()
    payload["names"] = {"alice": SOCIAL}
    payload["capabilities"]["clear-token-transfer"].update(
        pubkey=SOCIAL,
        relays=["wss://social.example"],
        mints=["https://different.example"],
    )
    fetch = Mock(return_value=payload)
    monkeypatch.setattr(discovery, "fetch_directory", fetch)
    result = root_delivery.discover_clear_support(
        "Alice@EXAMPLE.COM", mint_url="https://mint.example", unit="credits"
    )
    assert result["supported"] and result["source"] == "safebox-v1"
    assert result["recipient_pubkey"] == KEY
    assert result["relays"] == ["wss://wallet.example"]
    fetch.assert_called_once_with(ADDRESS)


@pytest.mark.parametrize(
    "cap", [None, {"transports": ["nip59"], "kinds": [7379], "units": ["other"]}]
)
def test_missing_support_never_falls_back(monkeypatch, cap):
    payload = document()
    if cap is None:
        payload["capabilities"] = {
            "safebox-wallet-message": {"transports": ["nip17"], "kinds": [14]}
        }
    else:
        payload["capabilities"]["clear-token-transfer"] = cap
    fetch = Mock(return_value=payload)
    monkeypatch.setattr(discovery, "fetch_directory", fetch)
    assert not root_delivery.discover_clear_support(
        ADDRESS, mint_url="https://mint.example", unit="credits"
    )["supported"]
    assert fetch.call_count == 1


@pytest.mark.parametrize(
    "change",
    [
        {"version": 2},
        {"version": True},
        {"address": "bob@example.com"},
        {"pubkey": SOCIAL.upper()},
        {"relays": []},
        {"relays": ["ws://wallet.example"]},
        {"relays": ["wss://127.0.0.1"]},
        {"relays": ["wss://wallet.example", "wss://wallet.example"]},
        {"capabilities": {}},
        {"capabilities": {"clear-token-transfer": {}}},
        {
            "capabilities": {
                "clear-token-transfer": {
                    "transports": ["nip59"],
                    "kinds": [7379],
                    "units": [],
                }
            }
        },
    ],
)
def test_invalid_directory_fails_closed(monkeypatch, change):
    payload = deepcopy(document())
    payload.update(change)
    fetch = Mock(return_value=payload)
    monkeypatch.setattr(discovery, "fetch_directory", fetch)
    with pytest.raises(root_delivery.DeliveryError):
        root_delivery.discover_clear_support(
            ADDRESS, mint_url="https://mint.example", unit="credits"
        )
    assert fetch.call_count == 1


@pytest.mark.parametrize("status", [301, 302, 404, 410, 429, 500, 503])
def test_http_failure_never_falls_back(monkeypatch, status):
    requests = []

    class Response:
        def read(self, n):
            pytest.fail("Do not read error as discovery")

    Response.status = status

    class Connection:
        def __init__(self, *a, **kw):
            pass

        def request(self, method, path, headers):
            requests.append(path)

        def getresponse(self):
            return Response()

        def close(self):
            pass

    monkeypatch.setattr(
        discovery.socket,
        "getaddrinfo",
        lambda *a, **kw: [(2, 1, 6, "", ("8.8.8.8", 443))],
    )
    monkeypatch.setattr(discovery.http.client, "HTTPSConnection", Connection)
    with pytest.raises(root_delivery.DeliveryError):
        root_delivery.discover_clear_support(
            ADDRESS, mint_url="https://mint.example", unit="credits"
        )
    assert requests == ["/.well-known/safebox.json?name=alice"]


def test_private_dns_and_duplicate_json_rejected(monkeypatch):
    monkeypatch.setattr(
        discovery.socket,
        "getaddrinfo",
        lambda *a, **kw: [(2, 1, 6, "", ("127.0.0.1", 443))],
    )
    with pytest.raises(ValueError):
        discovery.fetch_directory(ADDRESS)
    with pytest.raises(ValueError):
        discovery.unique_object([("version", 1), ("version", 2)])


@pytest.mark.parametrize(
    "address",
    [
        "alice@example.com/path",
        "alice@user@example.com",
        "a?b@example.com",
        "alice@localhost",
    ],
)
def test_invalid_address_never_fetches(monkeypatch, address):
    fetch = Mock()
    monkeypatch.setattr(discovery, "fetch_directory", fetch)
    with pytest.raises(root_delivery.DeliveryError):
        root_delivery.discover_clear_support(
            address, mint_url="https://mint.example", unit="credits"
        )
    fetch.assert_not_called()


def test_treasury_stops_before_export_when_wallet_discovery_fails(monkeypatch):
    from types import SimpleNamespace

    from clear import treasury_cli

    monkeypatch.setattr(treasury_cli, "_treasurer_nsec", lambda a: "test-key")
    monkeypatch.setattr(treasury_cli, "_resolve_keyset_id", lambda *a: "id")
    monkeypatch.setattr(treasury_cli, "_cmu_info", lambda *a, **kw: {"unit": "credits"})
    fetch = Mock(side_effect=ValueError("404"))
    monkeypatch.setattr(discovery, "fetch_directory", fetch)
    export = Mock(side_effect=AssertionError("Must not remove or swap proofs"))
    deliver = Mock(side_effect=AssertionError("Must not publish"))
    monkeypatch.setattr(treasury_cli, "_export_or_swap", export)
    monkeypatch.setattr(treasury_cli, "deliver_clear_token", deliver)
    with pytest.raises(root_delivery.DeliveryError):
        treasury_cli.send(
            SimpleNamespace(mint="https://mint.example", lifetime=300, address=ADDRESS)
        )
    export.assert_not_called()
    deliver.assert_not_called()


def test_fetch_pins_public_ip_and_retains_tls_hostname(monkeypatch):
    calls = []
    sock = Mock()
    monkeypatch.setattr(
        discovery.socket,
        "getaddrinfo",
        lambda *a, **kw: [(2, 1, 6, "", ("8.8.8.8", 443))],
    )
    monkeypatch.setattr(
        discovery.socket,
        "create_connection",
        lambda address, timeout: calls.append(address) or sock,
    )
    context = Mock()
    monkeypatch.setattr(discovery.ssl, "create_default_context", lambda: context)

    def request(self, *a, **kw):
        self.connect()

    monkeypatch.setattr(discovery.http.client.HTTPSConnection, "request", request)
    response = Mock(status=200)
    import json

    response.read.return_value = json.dumps(document()).encode()
    monkeypatch.setattr(
        discovery.http.client.HTTPSConnection, "getresponse", lambda self: response
    )
    assert discovery.fetch_directory(ADDRESS) == document()
    assert calls == [("8.8.8.8", 443)]
    context.wrap_socket.assert_called_once_with(sock, server_hostname="example.com")
    response.read.assert_called_once_with(discovery.MAX_BYTES + 1)
