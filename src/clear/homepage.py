"""Server-rendered public home page for a Clear mint."""

from __future__ import annotations

import json
from html import escape

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

    display_name = currency_alias or currency_name
    display_unit = currency_unit_alias or "CMU"
    authority_label = (
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
    values = {
        "language": escape(language),
        "direction": direction,
        "language_options": language_options,
        "version": escape(version),
        "mint_url": escape(mint_url),
        "currency_name": escape(currency_name),
        "currency_name_markup": configured_value(currency_name),
        "display_name": escape(display_name),
        "display_name_markup": configured_value(display_name),
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
        "authority_label": escape(authority_label),
    }

    copy_labels = {
        "copied": _("Copied"),
        "failed": _("Select URL to copy"),
        "ready": _("Copy mint URL"),
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
      margin: 0;
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
          {text(HOMEPAGE_LEDE)}
        </p>
        <div class="mint-address">
          <code class="technical" id="mint-url" dir="ltr">{values['mint_url']}</code>
          <button id="copy-mint" type="button" aria-label="{text('Copy mint URL')}">
            {text('Copy mint URL')}
          </button>
        </div>
      </div>
      <div class="token" aria-label="{text('Currency identity')}">
        <svg viewBox="0 0 512 512" role="img" aria-label="{text('Clear token')}">
          <circle cx="256" cy="256" r="208" fill="#247c93"/>
          <circle cx="256" cy="256" r="122" fill="#f4fbfc"/>
          <path fill="#143d52"
            d="M256 48a208 208 0 0 0 0 416v-86a122 122 0 1 1 0-244z"/>
          <path fill="#e16f51" d="M222 224h168v64H222z"/>
        </svg>
        <div>
          <strong>{values['display_unit_markup']}</strong>
          <span>{text('Clear Mint Unit')}</span>
        </div>
      </div>
    </section>

    <div class="grid">
      <section class="panel">
        <h2>{text('Mint details')}</h2>
        <dl>
          <div class="row">
            <dt>{text('Currency')}</dt><dd>{values['currency_name_markup']}</dd>
          </div>
          <div class="row">
            <dt>{text('Friendly name')}</dt><dd>{values['display_name_markup']}</dd>
          </div>
          <div class="row">
            <dt>{text('Unit label')}</dt><dd>{values['display_unit_markup']}</dd>
          </div>
          <div class="row">
            <dt>{text('Protocol unit')}</dt>
            <dd><code class="technical" dir="ltr">{values['protocol_unit']}</code></dd>
          </div>
          <div class="row">
            <dt>{text('Keyset')}</dt>
            <dd>
              <code class="technical" dir="ltr">{values['keyset_id']}</code>
            </dd>
          </div>
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

      <section class="panel">
        <h2>{text('How this mint works')}</h2>
        <ul class="features">
          <li>{text('Treasurer-authorized issuance')}</li>
          <li>{text('Private bearer transfers')}</li>
          <li>{text('Mint-enforced double-spend protection')}</li>
          <li>{text('Proof swapping and verification')}</li>
          <li>{text('Explicit unit retirement')}</li>
          <li>{values['authority_label']}</li>
        </ul>
      </section>
    </div>

    <aside class="about">
      {text(HOMEPAGE_ABOUT)}
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
  </script>
</body>
</html>"""
