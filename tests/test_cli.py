from __future__ import annotations

from clear import cli
from clear.config import Settings


def _settings(tmp_path, mint_url: str) -> Settings:
    return Settings(
        database_path=tmp_path / "clear.sqlite3",
        master_secret="11" * 32,
        operator_token="operator-token-that-is-long-enough",
        currency_name="Example Credits",
        mint_url=mint_url,
    )


def _run_cli(monkeypatch, configured: Settings, *arguments: str) -> dict:
    captured = {}
    monkeypatch.setattr(
        cli.Settings,
        "from_env",
        classmethod(lambda cls: configured),
    )
    def fake_create_app(settings, **kwargs):
        captured["surface"] = kwargs.get("surface")
        return settings

    monkeypatch.setattr(cli, "create_app", fake_create_app)
    monkeypatch.setattr(
        cli.uvicorn,
        "run",
        lambda app, **kwargs: captured.setdefault("settings", app),
    )
    monkeypatch.setattr("sys.argv", ["clear", *arguments])

    cli.main()

    return captured


def test_cli_preserves_explicit_public_mint_url(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CLEAR_MINT_URL", "https://clear.example")

    captured = _run_cli(
        monkeypatch,
        _settings(tmp_path, "https://clear.example"),
        "--host",
        "0.0.0.0",
        "--port",
        "3339",
    )

    configured = captured["settings"]
    assert configured.mint_url == "https://clear.example"
    assert captured["surface"] == "all"


def test_cli_derives_local_url_when_public_url_is_unset(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("CLEAR_MINT_URL", raising=False)

    captured = _run_cli(
        monkeypatch,
        _settings(tmp_path, "http://127.0.0.1:3339"),
        "--host",
        "127.0.0.1",
        "--port",
        "4444",
    )

    configured = captured["settings"]
    assert configured.mint_url == "http://127.0.0.1:4444"
    assert captured["surface"] == "all"


def test_cli_passes_selected_surface(tmp_path, monkeypatch) -> None:
    captured = _run_cli(
        monkeypatch,
        _settings(tmp_path, "http://127.0.0.1:3339"),
        "--surface",
        "public",
    )

    configured = captured["settings"]
    assert configured.mint_url == "http://127.0.0.1:3339"
    assert captured["surface"] == "public"
