"""Locale selection and homepage translations owned by Clear."""

import re
from collections.abc import Callable

HOMEPAGE_TAGLINE = "Credit-Liability Ecash: Authorized and Redeemable"
HOMEPAGE_LEDE = (
    "Authorized and redeemable organization-defined value, issued as private "
    "Cashu Mint Notes."
)
HOMEPAGE_ABOUT = (
    "Clear units are organization-defined credits, vouchers, passes, or other "
    "transferable value. They are distinct from Bitcoin-backed cash and remain "
    "governed and redeemable according to the issuing organization's terms."
)


DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = {
    "en": "English",
    "fr": "Français",
}

_LANGUAGE_TAG_PATTERN = re.compile(
    r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$"
)

_FRENCH = {
    "Clear Mint": "Service Clear",
    "Online": "En ligne",
    HOMEPAGE_TAGLINE: (
        "Monnaie électronique de crédit-passif : autorisée et remboursable"
    ),
    HOMEPAGE_LEDE: (
        "Valeur définie par une organisation, autorisée et remboursable, "
        "émise sous forme de billets privés Cashu."
    ),
    "Copy mint URL": "Copier l’URL du service",
    "Currency identity": "Identité de la monnaie",
    "Clear token": "Jeton Clear",
    "Clear Mint Unit": "Unité monétaire Clear",
    "Mint details": "Détails du service",
    "Currency": "Monnaie",
    "Friendly name": "Nom usuel",
    "Unit label": "Libellé de l’unité",
    "Protocol unit": "Unité du protocole",
    "Keyset": "Jeu de clés",
    "Service identity": "Identité du service",
    "FIPS IPv6 address": "Adresse IPv6 FIPS",
    "Management": "Gestion",
    "Identity state": "État de l’identité",
    "Operator": "Exploitant",
    "How this mint works": "Fonctionnement du service",
    "Treasurer-authorized issuance": "Émission autorisée par le trésorier",
    "Private bearer transfers": "Transferts privés au porteur",
    "Mint-enforced double-spend protection": (
        "Protection contre la double dépense assurée par le service"
    ),
    "Proof swapping and verification": "Échange et vérification des preuves",
    "Explicit unit retirement": "Retrait explicite d’unités",
    "Root authority configured": "Autorité racine configurée",
    "Root bootstrap mode": "Mode d’amorçage racine",
    HOMEPAGE_ABOUT: (
        "Les unités Clear sont des crédits, bons, laissez-passer ou autres "
        "valeurs transférables définis par une organisation. Elles se "
        "distinguent des fonds adossés au bitcoin et demeurent régies et "
        "remboursables selon les conditions de l’organisation émettrice."
    ),
    "Mint resources": "Ressources du service",
    "Mint information": "Information sur le service",
    "Public keys": "Clés publiques",
    "Docs": "Documentation",
    "Developer-stage software": "Logiciel en développement",
    "Not configured": "Non configuré",
    "Not commissioned": "Non mandaté",
    "independent": "indépendant",
    "mainstay-managed": "géré par Mainstay",
    "bootstrapped": "amorcé",
    "commissioned": "mandaté",
    "uncommissioned": "non mandaté",
    "Language": "Langue",
    "Copied": "Copié",
    "Select URL to copy": "Sélectionnez l’URL à copier",
}

_CATALOGS = {
    "en": {},
    "fr": _FRENCH,
}


def normalize_language_tag(value: str) -> str:
    """Return a conservative canonical BCP 47 language tag."""

    candidate = str(value or "").strip()
    if not _LANGUAGE_TAG_PATTERN.fullmatch(candidate):
        raise ValueError("language tag is invalid")
    parts = candidate.split("-")
    normalized = [parts[0].lower()]
    for part in parts[1:]:
        if len(part) == 4 and part.isalpha():
            normalized.append(part.title())
        elif len(part) == 2 and part.isalpha():
            normalized.append(part.upper())
        else:
            normalized.append(part.lower())
    return "-".join(normalized)


def supported_language(value: str | None) -> str:
    """Resolve a supported language, falling back to English."""

    try:
        normalized = normalize_language_tag(value or DEFAULT_LANGUAGE)
    except ValueError:
        return DEFAULT_LANGUAGE
    base_language = normalized.split("-", 1)[0]
    return base_language if base_language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def resolve_language(explicit: str | None, accept_language: str | None) -> str:
    """Resolve an explicit selector or the strongest supported browser locale."""

    if explicit is not None:
        return supported_language(explicit)

    weighted: list[tuple[float, int, str]] = []
    for index, item in enumerate(str(accept_language or "").split(",")):
        language_range, separator, parameters = item.strip().partition(";")
        if not language_range or language_range == "*":
            continue
        quality = 1.0
        if separator:
            for parameter in parameters.split(";"):
                name, equals, value = parameter.strip().partition("=")
                if name.lower() == "q" and equals:
                    try:
                        quality = float(value)
                    except ValueError:
                        quality = 0.0
        if quality <= 0:
            continue
        weighted.append((quality, -index, language_range))

    for _quality, _position, language_range in sorted(weighted, reverse=True):
        language = supported_language(language_range)
        if language != DEFAULT_LANGUAGE or language_range.lower().startswith("en"):
            return language
    return DEFAULT_LANGUAGE


def translator(language: str) -> Callable[[str], str]:
    """Return an immutable message lookup bound to one supported language."""

    catalog = _CATALOGS[supported_language(language)]
    return lambda message: catalog.get(message, message)
