"""Server-rendered public home page for a Clear mint."""

from __future__ import annotations

import json
from html import escape
from urllib.parse import quote

from clear.localization import (
    HOMEPAGE_ABOUT,
    HOMEPAGE_LEDE,
    HOMEPAGE_TAGLINE,
    SUPPORTED_LANGUAGES,
    language_direction,
    supported_language,
    translator,
)


def render_homepage(
    *,
    version: str,
    mint_url: str,
    mint_title: str,
    mint_tag_line: str,
    currency_name: str,
    currency_alias: str | None,
    currency_unit_alias: str | None,
    protocol_unit: str,
    keyset_id: str,
    service_npub: str | None,
    service_fips_ipv6_address: str | None,
    service_management: str,
    service_state: str,
    operator_npub: str | None,
    root_authority_configured: bool,
    active_keysets: list[dict] | None = None,
    language: str = "en",
) -> str:
    """Render the browser-facing mint overview with escaped configuration."""

    language = supported_language(language)
    direction = language_direction(language)
    _ = translator(language)

    def text(message: str) -> str:
        return escape(_(message))

    def configured_value(value: str) -> str:
        return f'<bdi dir="auto">{escape(value)}</bdi>'

    def identity_value(value: str | None, fallback: str) -> str:
        if value:
            return f'<code class="technical" dir="ltr">{escape(value)}</code>'
        return f'<span>{text(fallback)}</span>'

    def authority_label(item: dict) -> str:
        if item.get("authority") == "authorized-treasury" and item.get(
            "treasurer_npub"
        ):
            npub = str(item["treasurer_npub"])
            profile_url = f"v1/nostr/profiles/{quote(npub, safe='')}"
            return (
                '<button class="profile-trigger technical" type="button" '
                f'data-profile-url="{escape(profile_url)}" '
                f'data-npub="{escape(npub)}" '
                'aria-describedby="profile-card">'
                f"{escape(npub)}</button>"
            )
        return text("Operator keyset")

    def cmu_link(item: dict, label: str) -> str:
        href = f"cmus/{quote(str(item['id']), safe='')}"
        return (
            f'<a class="cmu-link" href="{escape(href)}">'
            f"{configured_value(label)}</a>"
        )

    display_name = mint_title or "Clear Mint"
    display_tag_line = mint_tag_line or HOMEPAGE_LEDE
    currency_display_name = currency_alias or currency_name
    display_unit = currency_unit_alias or "CMU"
    root_authority_label = (
        _("Root authority configured")
        if root_authority_configured
        else _("Root bootstrap mode")
    )
    language_options = "".join(
        (
            f'<option value="{escape(tag)}"'
            f'{" selected" if tag == language else ""}>'
            f"{escape(label)}</option>"
        )
        for tag, label in SUPPORTED_LANGUAGES.items()
    )

    keyset_rows = []
    for item in active_keysets or []:
        if item.get("active") is False:
            continue
        name = item.get("friendly_alias") or item.get("friendly_name") or item["unit"]
        unit_label = item.get("friendly_unit_alias") or "CMU"
        supply = item.get("supply") if isinstance(item.get("supply"), dict) else {}
        outstanding = supply.get("outstanding", supply.get("circulating", 0))
        keyset_rows.append(
            "<tr>"
            f"<td>{cmu_link(item, str(name))}</td>"
            f'<td class="unit-label">{configured_value(str(unit_label))}</td>'
            f"<td>{cmu_link(item, str(outstanding))}</td>"
            "<td>"
            f"<code class=\"technical\" dir=\"ltr\">{escape(str(item['unit']))}</code>"
            "</td>"
            "</tr>"
        )
    active_keyset_rows = "".join(keyset_rows) or (
        f'<tr><td colspan="4">{text("No active keysets")}</td></tr>'
    )

    values = {
        "language": escape(language),
        "direction": direction,
        "language_options": language_options,
        "active_keyset_rows": active_keyset_rows,
        "version": escape(version),
        "mint_url": escape(mint_url),
        "currency_name": escape(currency_name),
        "currency_name_markup": configured_value(currency_name),
        "display_name": escape(display_name),
        "display_name_markup": configured_value(display_name),
        "display_tag_line": (
            text(HOMEPAGE_LEDE)
            if display_tag_line == HOMEPAGE_LEDE
            else escape(display_tag_line)
        ),
        "currency_display_name": escape(currency_display_name),
        "currency_display_name_markup": configured_value(currency_display_name),
        "display_unit": escape(display_unit),
        "display_unit_markup": configured_value(display_unit),
        "protocol_unit": escape(protocol_unit),
        "keyset_id": escape(keyset_id),
        "service_npub_markup": identity_value(service_npub, "Not configured"),
        "service_fips_ipv6_address_markup": identity_value(
            service_fips_ipv6_address,
            "Not configured",
        ),
        "service_management": escape(_(service_management)),
        "service_state": escape(_(service_state)),
        "operator_npub_markup": identity_value(
            operator_npub,
            "Not commissioned",
        ),
        "authority_label": escape(root_authority_label),
    }

    copy_labels = {
        "copied": _("Copied"),
        "failed": _("Select URL to copy"),
        "ready": _("Copy mint URL"),
    }
    profile_labels = {
        "loading": _("Loading profile"),
        "not_found": _("No public profile found"),
        "unavailable": _("Profile unavailable"),
        "npub": "npub",
    }

    return f"""<!doctype html>
<html lang="{values['language']}" dir="{values['direction']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{values['display_name']} {text('Clear Mint')}">
  <meta name="color-scheme" content="light dark">
  <title>{values['display_name']} | {text('Clear Mint')}</title>
  <style>
    :root {{
      color-scheme: light;
      --page: #f6faf9;
      --surface: #ffffff;
      --surface-soft: #eaf6f7;
      --ink: #17313a;
      --muted: #5c6f74;
      --line: #d5e3e3;
      --teal: #247c93;
      --teal-dark: #143d52;
      --coral: #d9674b;
      --green: #237a4b;
      --shadow: 0 18px 45px rgba(20, 61, 82, 0.09);
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--page);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}

    a {{ color: var(--teal-dark); }}

    bdi {{ unicode-bidi: isolate; }}

    .technical {{
      direction: ltr;
      unicode-bidi: isolate;
      text-align: start;
    }}

    .shell {{
      width: min(100% - 2rem, 68rem);
      margin: 0 auto;
      padding: 1.25rem 0 3rem;
    }}

    .topbar {{
      display: flex;
      min-height: 2.75rem;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 1rem;
    }}

    .brand {{
      display: flex;
      align-items: center;
      gap: 0.7rem;
      color: var(--teal-dark);
      font-size: 0.82rem;
      font-weight: 760;
      text-transform: uppercase;
    }}

    .brand svg {{ width: 2rem; height: 2rem; flex: 0 0 auto; }}

    .topbar-actions {{
      display: flex;
      align-items: center;
      gap: 1rem;
    }}

    .language-form {{
      display: flex;
      align-items: center;
      gap: 0.45rem;
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 650;
    }}

    .language-form select {{
      min-height: 2.35rem;
      padding-block: 0.4rem;
      padding-inline: 0.6rem 1.8rem;
      border: 1px solid var(--line);
      border-radius: 5px;
      background: var(--surface);
      color: var(--ink);
      font: inherit;
    }}

    .online {{
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      color: var(--green);
      font-size: 0.82rem;
      font-weight: 720;
    }}

    .online::before {{
      width: 0.55rem;
      height: 0.55rem;
      border-radius: 50%;
      background: var(--green);
      content: "";
      box-shadow: 0 0 0 0.22rem rgba(35, 122, 75, 0.12);
    }}

    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(17rem, 0.65fr);
      gap: 1.5rem;
      align-items: stretch;
      padding: clamp(1.5rem, 5vw, 3.5rem);
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      box-shadow: var(--shadow);
    }}

    .eyebrow {{
      margin: 0 0 0.8rem;
      color: var(--coral);
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
    }}

    h1 {{
      max-width: 13ch;
      margin: 0;
      color: var(--teal-dark);
      font-size: clamp(2.25rem, 7vw, 4.8rem);
      line-height: 0.98;
      overflow-wrap: anywhere;
    }}

    .lede {{
      max-width: 39rem;
      margin: 1.2rem 0 1.5rem;
      color: var(--muted);
      font-size: clamp(1rem, 2vw, 1.18rem);
      line-height: 1.65;
    }}

    .mint-address {{
      display: flex;
      max-width: 40rem;
      align-items: center;
      gap: 0.75rem;
      padding-block: 0.7rem;
      padding-inline: 1rem 0.75rem;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--surface-soft);
    }}

    .mint-address code {{
      min-width: 0;
      flex: 1;
      overflow-wrap: anywhere;
      color: var(--teal-dark);
      font-size: 0.86rem;
    }}

    button {{
      flex: 0 0 auto;
      min-height: 2.35rem;
      padding: 0.55rem 0.8rem;
      border: 0;
      border-radius: 5px;
      background: var(--teal-dark);
      color: #ffffff;
      cursor: pointer;
      font: inherit;
      font-size: 0.78rem;
      font-weight: 720;
    }}

    button:focus-visible, select:focus-visible, a:focus-visible {{
      outline: 3px solid rgba(217, 103, 75, 0.45);
      outline-offset: 3px;
    }}

    .token {{
      display: grid;
      min-height: 18rem;
      place-items: center;
      align-content: center;
      gap: 1rem;
      border-inline-start: 1px solid var(--line);
      text-align: center;
    }}

    .token svg {{ width: min(12rem, 65%); height: auto; }}

    .token strong {{
      display: block;
      max-width: 17rem;
      color: var(--teal-dark);
      font-size: 1.1rem;
      overflow-wrap: anywhere;
    }}

    .token span {{
      display: block;
      margin-top: 0.25rem;
      color: var(--muted);
      font-size: 0.84rem;
    }}

    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 1rem;
      margin-top: 1rem;
    }}

    .panel {{
      padding: 1.35rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
    }}

    .panel h2 {{
      margin: 0 0 1rem;
      color: var(--teal-dark);
      font-size: 1rem;
    }}

    dl {{ margin: 0; }}

    .row {{
      display: grid;
      grid-template-columns: minmax(7.5rem, 0.4fr) minmax(0, 1fr);
      gap: 1rem;
      padding: 0.72rem 0;
      border-top: 1px solid var(--line);
    }}

    .row:first-child {{ padding-top: 0; border-top: 0; }}
    dt {{ color: var(--muted); font-size: 0.82rem; }}
    dd {{ margin: 0; overflow-wrap: anywhere; font-size: 0.86rem; font-weight: 650; }}

    .features {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 0.7rem;
      margin: 1rem 0 0;
      padding: 0;
      list-style: none;
    }}

    .features li {{
      display: flex;
      align-items: flex-start;
      gap: 0.55rem;
      color: var(--muted);
      font-size: 0.84rem;
      line-height: 1.45;
    }}

    .features li::before {{
      color: var(--green);
      content: "\\2713";
      font-weight: 850;
    }}

    .about {{
      margin-top: 1rem;
      padding: 1.2rem 1.35rem;
      border-inline-start: 0.28rem solid var(--coral);
      background: #fff7f4;
      color: #62483f;
      font-size: 0.9rem;
      line-height: 1.6;
    }}

    .keysets {{
      grid-column: 1 / -1;
      overflow-x: auto;
    }}

    .keyset-table {{
      width: 100%;
      min-width: 42rem;
      border-collapse: collapse;
      font-size: 0.84rem;
    }}

    .keyset-table th, .keyset-table td {{
      padding: 0.72rem 0.7rem;
      border-top: 1px solid var(--line);
      text-align: start;
      vertical-align: top;
    }}

    .keyset-table th {{
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 720;
    }}

    .keyset-table td {{
      font-weight: 650;
      overflow-wrap: anywhere;
    }}

    .keyset-table .unit-label {{
      white-space: nowrap;
      overflow-wrap: normal;
    }}

    .cmu-link {{
      color: var(--teal-dark);
      font-weight: 760;
      text-decoration-thickness: 1px;
      text-underline-offset: 0.18rem;
    }}

    .profile-trigger {{
      width: auto;
      margin: 0;
      padding: 0;
      border: 0;
      background: transparent;
      color: var(--teal-dark);
      cursor: help;
      font: inherit;
      text-align: start;
      text-decoration: underline;
      text-decoration-thickness: 1px;
      text-underline-offset: 0.18rem;
    }}

    .profile-trigger:focus-visible {{
      outline: 2px solid var(--coral);
      outline-offset: 0.18rem;
    }}

    .profile-card {{
      position: fixed;
      z-index: 20;
      display: none;
      width: min(22rem, calc(100vw - 2rem));
      padding: 0.9rem;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: var(--surface);
      box-shadow: var(--shadow);
      color: var(--ink);
      font-size: 0.84rem;
      line-height: 1.45;
    }}

    .profile-card[data-open="true"] {{ display: block; }}

    .profile-card-header {{
      display: flex;
      align-items: center;
      gap: 0.7rem;
      margin-bottom: 0.65rem;
    }}

    .profile-card img {{
      width: 2.8rem;
      height: 2.8rem;
      flex: 0 0 auto;
      border-radius: 50%;
      object-fit: cover;
    }}

    .profile-card strong {{
      display: block;
      font-size: 0.95rem;
    }}

    .profile-card p {{
      margin: 0.5rem 0 0;
      color: var(--muted);
    }}

    .links {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.85rem 1.25rem;
      margin-top: 1rem;
      padding: 0 0.2rem;
      font-size: 0.82rem;
    }}

    .links a {{ font-weight: 680; text-decoration-thickness: 1px; }}
    .links .version {{ margin-inline-start: auto; color: var(--muted); }}

    @media (max-width: 47rem) {{
      .shell {{ width: min(100% - 1.2rem, 68rem); }}
      .topbar {{ align-items: flex-start; }}
      .topbar-actions {{
        align-items: flex-end;
        flex-direction: column-reverse;
        gap: 0.45rem;
      }}
      .hero {{ grid-template-columns: 1fr; padding: 1.4rem; }}
      .token {{
        min-height: auto;
        padding-top: 1.5rem;
        border-top: 1px solid var(--line);
        border-inline-start: 0;
      }}
      .token svg {{ width: 7rem; }}
      .grid {{ grid-template-columns: 1fr; }}
      .mint-address {{ align-items: stretch; flex-direction: column; }}
      button {{ width: 100%; }}
      .links .version {{ width: 100%; margin-inline-start: 0; }}
    }}

    @media (prefers-color-scheme: dark) {{
      :root {{
        color-scheme: dark;
        --page: #101719;
        --surface: #182225;
        --surface-soft: #203135;
        --ink: #edf7f7;
        --muted: #adc0c1;
        --line: #34484c;
        --teal-dark: #8ecbd3;
        --coral: #f08a70;
        --green: #76c794;
        --shadow: none;
      }}
      .about {{ background: #2a211f; color: #e5c8c0; }}
      button {{ background: #8ecbd3; color: #102227; }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="brand">
        <svg viewBox="0 0 512 512" role="img" aria-label="Clear">
          <circle cx="256" cy="256" r="208" fill="#247c93"/>
          <circle cx="256" cy="256" r="122" fill="#f4fbfc"/>
          <path fill="#143d52"
            d="M256 48a208 208 0 0 0 0 416v-86a122 122 0 1 1 0-244z"/>
          <path fill="#e16f51" d="M222 224h168v64H222z"/>
        </svg>
        <span>{text('Clear Mint')}</span>
      </div>
      <div class="topbar-actions">
        <form class="language-form" method="get">
          <label for="language">{text('Language')}</label>
          <select id="language" name="lang" onchange="this.form.submit()">
            {values['language_options']}
          </select>
        </form>
        <div class="online">{text('Online')}</div>
      </div>
    </header>

    <section class="hero">
      <div>
        <p class="eyebrow">{text(HOMEPAGE_TAGLINE)}</p>
        <h1>{values['display_name_markup']}</h1>
        <p class="lede">
          {values['display_tag_line']}
        </p>
        <div class="mint-address">
          <code class="technical" id="mint-url" dir="ltr">{values['mint_url']}</code>
          <button id="copy-mint" type="button" aria-label="{text('Copy mint URL')}">
            {text('Copy mint URL')}
          </button>
        </div>
      </div>
      <div class="token">
        <svg viewBox="0 0 512 512" role="img" aria-label="{text('Clear token')}">
          <circle cx="256" cy="256" r="208" fill="#247c93"/>
          <circle cx="256" cy="256" r="122" fill="#f4fbfc"/>
          <path fill="#143d52"
            d="M256 48a208 208 0 0 0 0 416v-86a122 122 0 1 1 0-244z"/>
          <path fill="#e16f51" d="M222 224h168v64H222z"/>
        </svg>
        <div>
          <strong>{text('Private bearer notes for community-issued value.')}</strong>
        </div>
      </div>
    </section>

    <div class="grid">
      <section class="panel">
        <h2>{text('Mint details')}</h2>
        <dl>
          <div class="row">
            <dt>{text('Service identity')}</dt>
            <dd>{values['service_npub_markup']}</dd>
          </div>
          <div class="row">
            <dt>{text('FIPS IPv6 address')}</dt>
            <dd>{values['service_fips_ipv6_address_markup']}</dd>
          </div>
          <div class="row">
            <dt>{text('Management')}</dt><dd>{values['service_management']}</dd>
          </div>
          <div class="row">
            <dt>{text('Identity state')}</dt><dd>{values['service_state']}</dd>
          </div>
          <div class="row">
            <dt>{text('Operator')}</dt><dd>{values['operator_npub_markup']}</dd>
          </div>
        </dl>
      </section>

      <section class="panel keysets">
        <h2>{text('Mint Units In Circulation')}</h2>
        <table class="keyset-table">
          <thead>
            <tr>
              <th>{text('Name')}</th>
              <th>{text('Unit Label')}</th>
              <th>{text('Units Outstanding')}</th>
              <th>{text('Protocol Unit')}</th>
            </tr>
          </thead>
          <tbody>
            {values['active_keyset_rows']}
          </tbody>
        </table>
      </section>
    </div>

    <aside class="about">
      {text(HOMEPAGE_ABOUT)}
      <ul class="features">
        <li>{text('Treasurer-authorized issuance')}</li>
        <li>{text('Private bearer transfers')}</li>
        <li>{text('Mint-enforced double-spend protection')}</li>
        <li>{text('Proof swapping and verification')}</li>
        <li>{text('Explicit unit retirement')}</li>
        <li>{values['authority_label']}</li>
      </ul>
    </aside>

    <nav class="links" aria-label="{text('Mint resources')}">
      <a href="v1/info">{text('Mint information')}</a>
      <a href="v1/keys">{text('Public keys')}</a>
      <a href="https://trbouma.github.io/clear/">{text('Docs')}</a>
      <span class="version">
        Clear <bdi dir="ltr">{values['version']}</bdi>
        &middot; {text('Developer-stage software')}
      </span>
    </nav>
  </main>
  <div id="profile-card" class="profile-card" role="status" aria-live="polite"></div>
  <script>
    const button = document.getElementById("copy-mint");
    button.addEventListener("click", async () => {{
      try {{
        const mintUrl = document.getElementById("mint-url").textContent;
        await navigator.clipboard.writeText(mintUrl);
        button.textContent = {json.dumps(copy_labels['copied'], ensure_ascii=False)};
      }} catch (_error) {{
        button.textContent = {json.dumps(copy_labels['failed'], ensure_ascii=False)};
      }}
      window.setTimeout(() => {{
        button.textContent = {json.dumps(copy_labels['ready'], ensure_ascii=False)};
      }}, 1800);
    }});

    const profileCard = document.getElementById("profile-card");
    const profileCache = new Map();
    const profileLabels = {json.dumps(profile_labels, ensure_ascii=False)};

    function escapeText(value) {{
      return String(value || "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }}

    function profileMessage(npub, label) {{
      return `<strong>${{escapeText(npub)}}</strong><p>${{escapeText(label)}}</p>`;
    }}

    function renderProfile(payload, fallbackNpub) {{
      const profile = payload && payload.profile;
      if (!profile) {{
        return profileMessage(fallbackNpub, profileLabels.not_found);
      }}
      const name = profile.display_name || profile.displayName || profile.name ||
        profile.nip05 || fallbackNpub;
      const about = profile.about || profile.nip05 || "";
      const picture = profile.picture || profile.image || "";
      const pictureMarkup = picture
        ? `<img src="${{escapeText(picture)}}" alt="">`
        : "";
      const nip05 = profile.nip05
        ? `<p>${{escapeText(profile.nip05)}}</p>`
        : "";
      const aboutMarkup = about && about !== profile.nip05
        ? `<p>${{escapeText(about)}}</p>`
        : "";
      return `
        <div class="profile-card-header">
          ${{pictureMarkup}}
          <div>
            <strong>${{escapeText(name)}}</strong>
            <code class="technical" dir="ltr">${{escapeText(fallbackNpub)}}</code>
          </div>
        </div>
        ${{nip05}}
        ${{aboutMarkup}}
      `;
    }}

    function placeProfileCard(trigger) {{
      const rect = trigger.getBoundingClientRect();
      const margin = 12;
      const top = Math.min(
        rect.bottom + margin,
        window.innerHeight - profileCard.offsetHeight - margin,
      );
      const left = Math.min(
        rect.left,
        window.innerWidth - profileCard.offsetWidth - margin,
      );
      profileCard.style.top = `${{Math.max(margin, top)}}px`;
      profileCard.style.left = `${{Math.max(margin, left)}}px`;
    }}

    async function showProfile(trigger) {{
      const url = trigger.dataset.profileUrl;
      const npub = trigger.dataset.npub;
      profileCard.innerHTML = profileMessage(npub, profileLabels.loading);
      profileCard.dataset.open = "true";
      placeProfileCard(trigger);
      try {{
        if (!profileCache.has(url)) {{
          const response = await fetch(
            url,
            {{ headers: {{ "Accept": "application/json" }} }},
          );
          if (!response.ok) throw new Error("profile lookup failed");
          profileCache.set(url, await response.json());
        }}
        profileCard.innerHTML = renderProfile(profileCache.get(url), npub);
      }} catch (_error) {{
        profileCard.innerHTML = profileMessage(npub, profileLabels.unavailable);
      }}
      placeProfileCard(trigger);
    }}

    function hideProfile() {{
      profileCard.dataset.open = "false";
    }}

    document.querySelectorAll(".profile-trigger").forEach((trigger) => {{
      trigger.addEventListener("mouseenter", () => showProfile(trigger));
      trigger.addEventListener("focus", () => showProfile(trigger));
      trigger.addEventListener("click", () => showProfile(trigger));
      trigger.addEventListener("mouseleave", hideProfile);
      trigger.addEventListener("blur", hideProfile);
    }});
  </script>
</body>
</html>"""


def render_cmu_metrics_page(
    *,
    mint_title: str,
    mint_url: str,
    metrics: dict,
    language: str = "en",
) -> str:
    """Render a browser-facing CMU metrics page."""

    language = supported_language(language)
    direction = language_direction(language)
    cmu = metrics["cmus"][0]

    def value(content) -> str:
        return f'<bdi dir="auto">{escape(str(content))}</bdi>'

    def code(content) -> str:
        return f'<code class="technical" dir="ltr">{escape(str(content))}</code>'

    def metric_rows(items: dict) -> str:
        if not items:
            return '<tr><td colspan="3">None recorded</td></tr>'
        return "".join(
            "<tr>"
            f"<td>{value(label)}</td>"
            f"<td>{value(item.get('amount', 0))}</td>"
            f"<td>{value(item.get('count', 0))}</td>"
            "</tr>"
            for label, item in sorted(items.items())
        )

    def definition_row(label: str, content: str) -> str:
        return (
            '<div class="row">'
            f"<dt>{escape(label)}</dt>"
            f"<dd>{content}</dd>"
            "</div>"
        )

    display_name = cmu.get("friendly_name") or cmu["unit"]
    supply = cmu["supply"]
    proof_state = cmu["proof_state"]
    quotes = cmu["quotes"]
    methodology = metrics.get("methodology", {})
    treasurer_npub = cmu.get("treasurer_npub") or ""
    description = cmu.get("description") or ""
    description_markup = (
        '<p class="lede" id="cmu-description" dir="auto" '
        'style="white-space: pre-wrap; overflow-wrap: anywhere">'
        f'{escape(description)}</p>'
        if description else ""
    )
    treasurer_profile_url = (
        f"../v1/nostr/profiles/{quote(treasurer_npub, safe='')}"
        if treasurer_npub else ""
    )
    return f"""<!doctype html>
<html lang="{escape(language)}" dir="{direction}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{escape(str(display_name))} | CMU Metrics</title>
  <style>
    :root {{
      color-scheme: light;
      --page: #f6faf9;
      --surface: #ffffff;
      --surface-soft: #eaf6f7;
      --ink: #17313a;
      --muted: #5c6f74;
      --line: #d5e3e3;
      --teal: #247c93;
      --teal-dark: #143d52;
      --coral: #d9674b;
      --green: #237a4b;
      --shadow: 0 18px 45px rgba(20, 61, 82, 0.09);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--page);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
        "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    a {{ color: var(--teal-dark); }}
    bdi {{ unicode-bidi: isolate; }}
    .technical {{ direction: ltr; unicode-bidi: isolate; }}
    .shell {{
      width: min(100% - 2rem, 68rem);
      margin: 0 auto;
      padding: 1.25rem 0 3rem;
    }}
    .topbar {{
      display: flex;
      min-height: 2.75rem;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      margin-bottom: 1rem;
    }}
    .brand {{
      color: var(--teal-dark);
      font-size: 0.82rem;
      font-weight: 760;
      text-transform: uppercase;
    }}
    .hero {{
      padding: clamp(1.5rem, 5vw, 3.2rem);
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      box-shadow: var(--shadow);
    }}
    .eyebrow {{
      margin: 0 0 0.8rem;
      color: var(--coral);
      font-size: 0.78rem;
      font-weight: 800;
      text-transform: uppercase;
    }}
    h1 {{
      max-width: 18ch;
      margin: 0;
      color: var(--teal-dark);
      font-size: clamp(2rem, 6vw, 4rem);
      line-height: 1;
      overflow-wrap: anywhere;
    }}
    .lede {{
      max-width: 46rem;
      margin: 1rem 0 0;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.6;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }}
    .panel {{
      padding: 1.35rem;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
    }}
    .wide {{ grid-column: 1 / -1; }}
    .panel h2 {{
      margin: 0 0 1rem;
      color: var(--teal-dark);
      font-size: 1rem;
    }}
    dl {{ margin: 0; }}
    .row {{
      display: grid;
      grid-template-columns: minmax(9rem, 0.36fr) minmax(0, 1fr);
      gap: 1rem;
      padding: 0.72rem 0;
      border-top: 1px solid var(--line);
    }}
    .row:first-child {{ padding-top: 0; border-top: 0; }}
    dt {{ color: var(--muted); font-size: 0.82rem; }}
    dd {{ margin: 0; overflow-wrap: anywhere; font-size: 0.86rem; font-weight: 650; }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 0.75rem;
    }}
    .metric {{
      padding: 1rem;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: var(--surface-soft);
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 0.76rem;
      font-weight: 720;
      text-transform: uppercase;
    }}
    .metric strong {{
      display: block;
      margin-top: 0.35rem;
      color: var(--teal-dark);
      font-size: 1.65rem;
      overflow-wrap: anywhere;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.84rem;
    }}
    th, td {{
      padding: 0.72rem 0.7rem;
      border-top: 1px solid var(--line);
      text-align: start;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 0.78rem;
      font-weight: 720;
    }}
    td {{ font-weight: 650; overflow-wrap: anywhere; }}
    .note {{
      margin: 0;
      color: var(--muted);
      font-size: 0.86rem;
      line-height: 1.55;
    }}
    .links {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.85rem 1.25rem;
      margin-top: 1rem;
      padding: 0 0.2rem;
      font-size: 0.82rem;
    }}
    .links a {{ font-weight: 680; text-decoration-thickness: 1px; }}
    @media (max-width: 47rem) {{
      .shell {{ width: min(100% - 1.2rem, 68rem); }}
      .grid, .metric-grid {{ grid-template-columns: 1fr; }}
      .row {{ grid-template-columns: 1fr; gap: 0.35rem; }}
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        color-scheme: dark;
        --page: #101719;
        --surface: #182225;
        --surface-soft: #203135;
        --ink: #edf7f7;
        --muted: #adc0c1;
        --line: #34484c;
        --teal-dark: #8ecbd3;
        --coral: #f08a70;
        --green: #76c794;
        --shadow: none;
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="topbar">
      <div class="brand">Clear Mint</div>
      <a href="../">Mint Home</a>
    </header>
    <section class="hero">
      <p class="eyebrow">CMU metrics</p>
      <h1>{value(display_name)}</h1>
      {description_markup}
    </section>
    <div class="grid">
      <section class="panel">
        <h2>Supply</h2>
        <div class="metric-grid">
          <div class="metric"><span>Issued</span><strong>{value(supply["issued"])}</strong></div>
          <div class="metric"><span>Retired</span><strong>{value(supply["retired"])}</strong></div>
          <div class="metric"><span>Outstanding</span><strong>{value(supply["outstanding"])}</strong></div>
        </div>
        <h3>Treasurer</h3>
        <div id="treasurer-profile" data-profile-url="{escape(treasurer_profile_url)}" aria-live="polite" style="overflow-wrap: anywhere">
          <p class="note">No Social Profile</p>
        </div>
      </section>
      <section class="panel">
        <h2>CMU identity</h2>
        <dl>
          {definition_row("Mint", value(mint_title))}
          {definition_row("Mint URL", code(mint_url))}
          {definition_row("Protocol unit", code(cmu["unit"]))}
          {definition_row("Keyset ID", code(cmu["keyset_id"]))}
          {definition_row("Fingerprint", code(cmu["keyset_fingerprint"]))}
          {definition_row("Status", value(cmu["status"]))}
          {definition_row("Home page listing", value("Listed" if cmu.get("public_listing", True) else "Unlisted"))}
          {definition_row("Treasurer", code(cmu["treasurer_npub"]) if cmu.get("treasurer_npub") else value("Operator keyset"))}
          {definition_row("Material", value(cmu["material_kind"]))}
        </dl>
      </section>
      <section class="panel">
        <h2>Quote pipeline</h2>
        <dl>
          {definition_row("Quotes", value(quotes["count"]))}
          {definition_row("Requested", value(quotes["requested"]))}
          {definition_row("Authorized", value(quotes["authorized"]))}
          {definition_row("Issued", value(quotes["issued"]))}
          {definition_row("Authorized, unissued", value(quotes["authorized_unissued"]))}
          {definition_row("Requested, unauthorized", value(quotes["requested_unauthorized"]))}
        </dl>
      </section>
      <section class="panel">
        <h2>Proof-state diagnostics</h2>
        <dl>
          {definition_row("Signed output amount", value(proof_state["signed_outputs_amount"]))}
          {definition_row("Signed output count", value(proof_state["signed_outputs_count"]))}
          {definition_row("Spent proof amount", value(proof_state["spent_proofs_amount"]))}
          {definition_row("Spent proof count", value(proof_state["spent_proofs_count"]))}
          {definition_row("Unspent signed-output estimate", value(proof_state["unspent_signed_outputs_estimate"]))}
        </dl>
      </section>
      <section class="panel wide">
        <h2>Audit actions</h2>
        <table>
          <thead><tr><th>Action</th><th>Amount</th><th>Count</th></tr></thead>
          <tbody>{metric_rows(cmu["activity"]["audit_actions"])}</tbody>
        </table>
      </section>
      <section class="panel">
        <h2>Signed outputs by operation</h2>
        <table>
          <thead><tr><th>Operation</th><th>Amount</th><th>Count</th></tr></thead>
          <tbody>{metric_rows(proof_state["signed_outputs_by_operation"])}</tbody>
        </table>
      </section>
      <section class="panel">
        <h2>Spent proofs by reason</h2>
        <table>
          <thead><tr><th>Reason</th><th>Amount</th><th>Count</th></tr></thead>
          <tbody>{metric_rows(proof_state["spent_proofs_by_reason"])}</tbody>
        </table>
      </section>
      <section class="panel wide">
        <h2>Methodology</h2>
        <p class="note">{escape(str(methodology.get("supply", "")))}</p>
        <p class="note">{escape(str(methodology.get("proof_state", "")))}</p>
        <p class="note">{escape(str(methodology.get("quotes", "")))}</p>
      </section>
    </div>
    <nav class="links" aria-label="CMU resources">
      <a href="../v1/keysets">Keysets JSON</a>
      <a href="../v1/info">Mint information</a>
      <a href="https://trbouma.github.io/clear/">Docs</a>
    </nav>
  </main>
  <script>
    const treasurerProfile = document.getElementById("treasurer-profile");
    const profileUrl = treasurerProfile.dataset.profileUrl;
    if (profileUrl) {{
      treasurerProfile.textContent = "Loading profile...";
      fetch(profileUrl, {{ headers: {{ Accept: "application/json" }} }})
        .then(response => {{
          if (!response.ok) throw new Error("Profile lookup failed");
          return response.json();
        }})
        .then(payload => {{
          const profile = payload && payload.profile;
          const fields = profile && [
            profile.display_name || profile.displayName || profile.name,
            profile.nip05,
            profile.about,
          ].filter(field => typeof field === "string" && field.trim());
          treasurerProfile.replaceChildren();
          const picture = profile && (profile.picture || profile.image);
          if (typeof picture === "string" &&
              ["https://", "http://"].some(prefix => picture.toLowerCase().startsWith(prefix))) {{
            const image = document.createElement("img");
            image.src = picture;
            image.alt = "Treasurer profile picture";
            image.referrerPolicy = "no-referrer";
            image.width = 64;
            image.height = 64;
            image.style.objectFit = "cover";
            image.addEventListener("error", () => {{
              image.remove();
              if (!fields || !fields.length) treasurerProfile.textContent = "No Social Profile";
            }});
            treasurerProfile.append(image);
          }}
          for (const field of fields || []) {{
            const line = document.createElement("p");
            line.textContent = field;
            treasurerProfile.append(line);
          }}
          if (!treasurerProfile.childElementCount) {{
            treasurerProfile.textContent = "No Social Profile";
          }}
        }})
        .catch(() => {{ treasurerProfile.textContent = "No Social Profile"; }});
    }}
  </script>
</body>
</html>"""
