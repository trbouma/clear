import pytest

from clear.localization import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    normalize_language_tag,
    resolve_language,
    supported_language,
    translator,
)


def test_language_tags_are_canonicalized() -> None:
    assert normalize_language_tag("FR-ca") == "fr-CA"
    assert normalize_language_tag("en") == "en"


def test_supported_language_uses_base_language_and_english_fallback() -> None:
    assert supported_language("fr-CA") == "fr"
    assert supported_language("de-AT") == "de"
    assert supported_language("zh-CN") == "zh-Hans"
    assert supported_language("zh-Hans-CN") == "zh-Hans"
    assert supported_language("zh-TW") == DEFAULT_LANGUAGE
    assert supported_language("../fr") == DEFAULT_LANGUAGE


def test_explicit_language_precedes_browser_preference() -> None:
    assert resolve_language("en", "fr-CA,fr;q=0.9") == "en"
    assert resolve_language("fr-CA", "en") == "fr"


def test_browser_language_uses_quality_and_supported_fallback() -> None:
    assert resolve_language(None, "nl;q=1, de-AT;q=0.8, en;q=0.5") == "de"
    assert resolve_language(None, "nl, es-MX;q=0.8") == "es"
    assert resolve_language(None, "zh-CN, en;q=0.5") == "zh-Hans"


def test_translation_catalog_falls_back_to_english_source_text() -> None:
    french = translator("fr")
    assert french("Mint details") == "Détails du service"
    assert french("Uncatalogued message") == "Uncatalogued message"


@pytest.mark.parametrize(
    ("language", "translated_label"),
    [
        ("fr", "Détails du service"),
        ("es", "Detalles del servicio"),
        ("pt", "Detalhes do serviço"),
        ("de", "Dienstdetails"),
        ("it", "Dettagli del servizio"),
        ("zh-Hans", "服务详情"),
    ],
)
def test_each_catalog_translates_the_homepage(language, translated_label) -> None:
    assert translator(language)("Mint details") == translated_label
    assert language in SUPPORTED_LANGUAGES
