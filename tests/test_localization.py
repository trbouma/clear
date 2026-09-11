from clear.localization import (
    DEFAULT_LANGUAGE,
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
    assert supported_language("de") == DEFAULT_LANGUAGE
    assert supported_language("../fr") == DEFAULT_LANGUAGE


def test_explicit_language_precedes_browser_preference() -> None:
    assert resolve_language("en", "fr-CA,fr;q=0.9") == "en"
    assert resolve_language("fr-CA", "en") == "fr"


def test_browser_language_uses_quality_and_supported_fallback() -> None:
    assert resolve_language(None, "de;q=1, fr-CA;q=0.8, en;q=0.5") == "fr"
    assert resolve_language(None, "de, es;q=0.8") == DEFAULT_LANGUAGE


def test_translation_catalog_falls_back_to_english_source_text() -> None:
    french = translator("fr")
    assert french("Mint details") == "Détails du service"
    assert french("Uncatalogued message") == "Uncatalogued message"
