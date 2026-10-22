from unittest.mock import Mock

from clear import wallet_labels


def test_labels_are_scoped_by_mint_and_cached_per_command(monkeypatch):
    fetch = Mock(side_effect=lambda mint: [{"unit":"unit", "friendly_alias":mint,
                                          "friendly_unit_alias":"shares"}])
    monkeypatch.setattr(wallet_labels,"fetch_keysets",fetch)
    summary={"balances":[{"mint":mint,"unit":"unit","amount":2}
                         for mint in ["https://one.example","https://two.example","https://one.example"]]}
    result=wallet_labels.with_friendly_labels(summary)
    assert fetch.call_count == 2
    for row in result["balances"]:
        assert row["friendly_alias"] == row["mint"]
        assert row["amount"] == 2 and row["unit"] == "unit"


def test_offline_keeps_local_balance(monkeypatch):
    monkeypatch.setattr(wallet_labels,"fetch_keysets",Mock(side_effect=OSError("offline")))
    summary={"balances":[{"mint":"https://mint.example","unit":"cmu-id","amount":100}]}
    row=wallet_labels.with_friendly_labels(summary)["balances"][0]
    assert row["amount"] == 100
    assert row["friendly_alias"] == row["friendly_unit_alias"] == "cmu-id"
