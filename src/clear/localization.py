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
    "es": "Español",
    "pt": "Português",
    "de": "Deutsch",
    "it": "Italiano",
    "zh-Hans": "简体中文",
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

_SPANISH = {
    "Clear Mint": "Servicio Clear",
    "Online": "En línea",
    HOMEPAGE_TAGLINE: "Dinero electrónico de crédito y pasivo: autorizado y canjeable",
    HOMEPAGE_LEDE: (
        "Valor definido por una organización, autorizado y canjeable, emitido "
        "como billetes privados de Cashu."
    ),
    "Copy mint URL": "Copiar URL del servicio",
    "Currency identity": "Identidad de la moneda",
    "Clear token": "Ficha Clear",
    "Clear Mint Unit": "Unidad monetaria Clear",
    "Mint details": "Detalles del servicio",
    "Currency": "Moneda",
    "Friendly name": "Nombre habitual",
    "Unit label": "Etiqueta de la unidad",
    "Protocol unit": "Unidad del protocolo",
    "Keyset": "Conjunto de claves",
    "Service identity": "Identidad del servicio",
    "FIPS IPv6 address": "Dirección IPv6 FIPS",
    "Management": "Gestión",
    "Identity state": "Estado de la identidad",
    "Operator": "Operador",
    "How this mint works": "Cómo funciona este servicio",
    "Treasurer-authorized issuance": "Emisión autorizada por el tesorero",
    "Private bearer transfers": "Transferencias privadas al portador",
    "Mint-enforced double-spend protection": (
        "Protección contra el doble gasto aplicada por el servicio"
    ),
    "Proof swapping and verification": "Intercambio y verificación de pruebas",
    "Explicit unit retirement": "Retiro explícito de unidades",
    "Root authority configured": "Autoridad raíz configurada",
    "Root bootstrap mode": "Modo de inicialización raíz",
    HOMEPAGE_ABOUT: (
        "Las unidades Clear son créditos, vales, pases u otros valores "
        "transferibles definidos por una organización. Son distintos del "
        "efectivo respaldado por bitcoin y se rigen y canjean según las "
        "condiciones de la organización emisora."
    ),
    "Mint resources": "Recursos del servicio",
    "Mint information": "Información del servicio",
    "Public keys": "Claves públicas",
    "Docs": "Documentación",
    "Developer-stage software": "Software en desarrollo",
    "Not configured": "No configurada",
    "Not commissioned": "No comisionado",
    "independent": "independiente",
    "mainstay-managed": "gestionado por Mainstay",
    "bootstrapped": "inicializado",
    "commissioned": "comisionado",
    "uncommissioned": "no comisionado",
    "Language": "Idioma",
    "Copied": "Copiado",
    "Select URL to copy": "Seleccione la URL que desea copiar",
}

_PORTUGUESE = {
    "Clear Mint": "Serviço Clear",
    "Online": "Online",
    HOMEPAGE_TAGLINE: (
        "Dinheiro eletrônico de crédito e passivo: autorizado e resgatável"
    ),
    HOMEPAGE_LEDE: (
        "Valor definido por uma organização, autorizado e resgatável, emitido "
        "como notas privadas Cashu."
    ),
    "Copy mint URL": "Copiar URL do serviço",
    "Currency identity": "Identidade da moeda",
    "Clear token": "Ficha Clear",
    "Clear Mint Unit": "Unidade monetária Clear",
    "Mint details": "Detalhes do serviço",
    "Currency": "Moeda",
    "Friendly name": "Nome usual",
    "Unit label": "Rótulo da unidade",
    "Protocol unit": "Unidade do protocolo",
    "Keyset": "Conjunto de chaves",
    "Service identity": "Identidade do serviço",
    "FIPS IPv6 address": "Endereço IPv6 FIPS",
    "Management": "Gestão",
    "Identity state": "Estado da identidade",
    "Operator": "Operador",
    "How this mint works": "Como este serviço funciona",
    "Treasurer-authorized issuance": "Emissão autorizada pelo tesoureiro",
    "Private bearer transfers": "Transferências privadas ao portador",
    "Mint-enforced double-spend protection": (
        "Proteção contra gasto duplo aplicada pelo serviço"
    ),
    "Proof swapping and verification": "Troca e verificação de provas",
    "Explicit unit retirement": "Retirada explícita de unidades",
    "Root authority configured": "Autoridade raiz configurada",
    "Root bootstrap mode": "Modo de inicialização raiz",
    HOMEPAGE_ABOUT: (
        "As unidades Clear são créditos, vales, passes ou outros valores "
        "transferíveis definidos por uma organização. São distintas de "
        "dinheiro respaldado por bitcoin e continuam regidas e resgatáveis "
        "conforme os termos da organização emissora."
    ),
    "Mint resources": "Recursos do serviço",
    "Mint information": "Informações do serviço",
    "Public keys": "Chaves públicas",
    "Docs": "Documentação",
    "Developer-stage software": "Software em desenvolvimento",
    "Not configured": "Não configurada",
    "Not commissioned": "Não comissionado",
    "independent": "independente",
    "mainstay-managed": "gerido pelo Mainstay",
    "bootstrapped": "inicializado",
    "commissioned": "comissionado",
    "uncommissioned": "não comissionado",
    "Language": "Idioma",
    "Copied": "Copiado",
    "Select URL to copy": "Selecione a URL que deseja copiar",
}

_GERMAN = {
    "Clear Mint": "Clear-Dienst",
    "Online": "Online",
    HOMEPAGE_TAGLINE: (
        "Elektronisches Kredit- und Verbindlichkeitsgeld: autorisiert und "
        "einlösbar"
    ),
    HOMEPAGE_LEDE: (
        "Von einer Organisation definierter, autorisierter und einlösbarer "
        "Wert, ausgegeben als private Cashu-Noten."
    ),
    "Copy mint URL": "Dienst-URL kopieren",
    "Currency identity": "Währungsidentität",
    "Clear token": "Clear-Token",
    "Clear Mint Unit": "Clear-Währungseinheit",
    "Mint details": "Dienstdetails",
    "Currency": "Währung",
    "Friendly name": "Anzeigename",
    "Unit label": "Einheitenbezeichnung",
    "Protocol unit": "Protokolleinheit",
    "Keyset": "Schlüsselsatz",
    "Service identity": "Dienstidentität",
    "FIPS IPv6 address": "FIPS-IPv6-Adresse",
    "Management": "Verwaltung",
    "Identity state": "Identitätsstatus",
    "Operator": "Betreiber",
    "How this mint works": "So funktioniert dieser Dienst",
    "Treasurer-authorized issuance": "Vom Schatzmeister autorisierte Ausgabe",
    "Private bearer transfers": "Private Inhaberübertragungen",
    "Mint-enforced double-spend protection": (
        "Vom Dienst durchgesetzter Schutz vor Doppelausgaben"
    ),
    "Proof swapping and verification": "Austausch und Prüfung von Nachweisen",
    "Explicit unit retirement": "Ausdrückliche Stilllegung von Einheiten",
    "Root authority configured": "Stammautorität konfiguriert",
    "Root bootstrap mode": "Stamm-Initialisierungsmodus",
    HOMEPAGE_ABOUT: (
        "Clear-Einheiten sind von einer Organisation definierte Guthaben, "
        "Gutscheine, Berechtigungen oder andere übertragbare Werte. Sie "
        "unterscheiden sich von bitcoin-gedecktem Bargeld und bleiben nach "
        "den Bedingungen der ausgebenden Organisation geregelt und einlösbar."
    ),
    "Mint resources": "Dienstressourcen",
    "Mint information": "Dienstinformationen",
    "Public keys": "Öffentliche Schlüssel",
    "Docs": "Dokumentation",
    "Developer-stage software": "Software in Entwicklung",
    "Not configured": "Nicht konfiguriert",
    "Not commissioned": "Nicht beauftragt",
    "independent": "unabhängig",
    "mainstay-managed": "von Mainstay verwaltet",
    "bootstrapped": "initialisiert",
    "commissioned": "beauftragt",
    "uncommissioned": "nicht beauftragt",
    "Language": "Sprache",
    "Copied": "Kopiert",
    "Select URL to copy": "Zu kopierende URL auswählen",
}

_ITALIAN = {
    "Clear Mint": "Servizio Clear",
    "Online": "Online",
    HOMEPAGE_TAGLINE: (
        "Moneta elettronica di credito e passività: autorizzata e riscattabile"
    ),
    HOMEPAGE_LEDE: (
        "Valore definito da un’organizzazione, autorizzato e riscattabile, "
        "emesso come banconote private Cashu."
    ),
    "Copy mint URL": "Copia URL del servizio",
    "Currency identity": "Identità della valuta",
    "Clear token": "Gettone Clear",
    "Clear Mint Unit": "Unità monetaria Clear",
    "Mint details": "Dettagli del servizio",
    "Currency": "Valuta",
    "Friendly name": "Nome comune",
    "Unit label": "Etichetta dell’unità",
    "Protocol unit": "Unità del protocollo",
    "Keyset": "Set di chiavi",
    "Service identity": "Identità del servizio",
    "FIPS IPv6 address": "Indirizzo IPv6 FIPS",
    "Management": "Gestione",
    "Identity state": "Stato dell’identità",
    "Operator": "Operatore",
    "How this mint works": "Come funziona questo servizio",
    "Treasurer-authorized issuance": "Emissione autorizzata dal tesoriere",
    "Private bearer transfers": "Trasferimenti privati al portatore",
    "Mint-enforced double-spend protection": (
        "Protezione dalla doppia spesa applicata dal servizio"
    ),
    "Proof swapping and verification": "Scambio e verifica delle prove",
    "Explicit unit retirement": "Ritiro esplicito delle unità",
    "Root authority configured": "Autorità radice configurata",
    "Root bootstrap mode": "Modalità di inizializzazione radice",
    HOMEPAGE_ABOUT: (
        "Le unità Clear sono crediti, buoni, pass o altri valori trasferibili "
        "definiti da un’organizzazione. Sono distinte dal denaro garantito da "
        "bitcoin e rimangono regolate e riscattabili secondo le condizioni "
        "dell’organizzazione emittente."
    ),
    "Mint resources": "Risorse del servizio",
    "Mint information": "Informazioni sul servizio",
    "Public keys": "Chiavi pubbliche",
    "Docs": "Documentazione",
    "Developer-stage software": "Software in fase di sviluppo",
    "Not configured": "Non configurata",
    "Not commissioned": "Non commissionato",
    "independent": "indipendente",
    "mainstay-managed": "gestito da Mainstay",
    "bootstrapped": "inizializzato",
    "commissioned": "commissionato",
    "uncommissioned": "non commissionato",
    "Language": "Lingua",
    "Copied": "Copiato",
    "Select URL to copy": "Seleziona l’URL da copiare",
}

_SIMPLIFIED_CHINESE = {
    "Clear Mint": "Clear 服务",
    "Online": "在线",
    HOMEPAGE_TAGLINE: "信用与负债电子现金：经授权且可兑付",
    HOMEPAGE_LEDE: "由组织定义、授权并可兑付的价值，以私密 Cashu 票据发行。",
    "Copy mint URL": "复制服务网址",
    "Currency identity": "货币标识",
    "Clear token": "Clear 代币",
    "Clear Mint Unit": "Clear 货币单位",
    "Mint details": "服务详情",
    "Currency": "货币",
    "Friendly name": "常用名称",
    "Unit label": "单位标签",
    "Protocol unit": "协议单位",
    "Keyset": "密钥集",
    "Service identity": "服务标识",
    "FIPS IPv6 address": "FIPS IPv6 地址",
    "Management": "管理方式",
    "Identity state": "标识状态",
    "Operator": "运营方",
    "How this mint works": "此服务如何运作",
    "Treasurer-authorized issuance": "经财务主管授权发行",
    "Private bearer transfers": "私密持有人转移",
    "Mint-enforced double-spend protection": "由服务实施双花防护",
    "Proof swapping and verification": "凭证交换与验证",
    "Explicit unit retirement": "明确注销单位",
    "Root authority configured": "已配置根授权方",
    "Root bootstrap mode": "根初始化模式",
    HOMEPAGE_ABOUT: (
        "Clear 单位是由组织定义的信用、代金券、通行证或其他可转移价值。"
        "它们不同于由比特币支持的现金，并继续按照发行组织的条款管理和兑付。"
    ),
    "Mint resources": "服务资源",
    "Mint information": "服务信息",
    "Public keys": "公钥",
    "Docs": "文档",
    "Developer-stage software": "开发阶段软件",
    "Not configured": "未配置",
    "Not commissioned": "未委任",
    "independent": "独立",
    "mainstay-managed": "由 Mainstay 管理",
    "bootstrapped": "已初始化",
    "commissioned": "已委任",
    "uncommissioned": "未委任",
    "Language": "语言",
    "Copied": "已复制",
    "Select URL to copy": "请选择要复制的网址",
}

_CATALOGS = {
    "en": {},
    "fr": _FRENCH,
    "es": _SPANISH,
    "pt": _PORTUGUESE,
    "de": _GERMAN,
    "it": _ITALIAN,
    "zh-Hans": _SIMPLIFIED_CHINESE,
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
    if normalized in SUPPORTED_LANGUAGES:
        return normalized
    if normalized in {"zh", "zh-CN", "zh-SG"} or normalized.startswith(
        "zh-Hans-"
    ):
        return "zh-Hans"
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
