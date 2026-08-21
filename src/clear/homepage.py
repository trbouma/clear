"""Server-rendered public home page for a Clear mint."""

from __future__ import annotations

from html import escape


def render_homepage(
    *,
    version: str,
    mint_url: str,
    currency_name: str,
    currency_alias: str | None,
    currency_unit_alias: str | None,
    protocol_unit: str,
    keyset_id: str,
    root_authority_configured: bool,
) -> str:
    """Render the browser-facing mint overview with escaped configuration."""

    display_name = currency_alias or currency_name
    display_unit = currency_unit_alias or "CMU"
    authority_label = (
        "Root authority configured"
        if root_authority_configured
        else "Root bootstrap mode"
    )
    values = {
        "version": escape(version),
        "mint_url": escape(mint_url),
        "currency_name": escape(currency_name),
        "display_name": escape(display_name),
        "display_unit": escape(display_unit),
        "protocol_unit": escape(protocol_unit),
        "keyset_id": escape(keyset_id),
        "authority_label": escape(authority_label),
    }

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{values['display_name']} Clear mint">
  <meta name="color-scheme" content="light dark">
  <title>{values['display_name']} | Clear Mint</title>
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
      padding: 0.7rem 0.75rem 0.7rem 1rem;
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

    button:focus-visible, a:focus-visible {{
      outline: 3px solid rgba(217, 103, 75, 0.45);
      outline-offset: 3px;
    }}

    .token {{
      display: grid;
      min-height: 18rem;
      place-items: center;
      align-content: center;
      gap: 1rem;
      border-left: 1px solid var(--line);
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
      border-left: 0.28rem solid var(--coral);
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
    .links .version {{ margin-left: auto; color: var(--muted); }}

    @media (max-width: 47rem) {{
      .shell {{ width: min(100% - 1.2rem, 68rem); }}
      .hero {{ grid-template-columns: 1fr; padding: 1.4rem; }}
      .token {{
        min-height: auto;
        padding-top: 1.5rem;
        border-top: 1px solid var(--line);
        border-left: 0;
      }}
      .token svg {{ width: 7rem; }}
      .grid {{ grid-template-columns: 1fr; }}
      .mint-address {{ align-items: stretch; flex-direction: column; }}
      button {{ width: 100%; }}
      .links .version {{ width: 100%; margin-left: 0; }}
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
        <span>Clear Mint</span>
      </div>
      <div class="online">Online</div>
    </header>

    <section class="hero">
      <div>
        <p class="eyebrow">Organization-issued transferable units</p>
        <h1>{values['display_name']}</h1>
        <p class="lede">
          Clear provides the issuance, circulation and redemption machinery for
          organization-defined transferable units using private Cashu notes.
        </p>
        <div class="mint-address">
          <code id="mint-url">{values['mint_url']}</code>
          <button id="copy-mint" type="button" aria-label="Copy mint URL">
            Copy mint URL
          </button>
        </div>
      </div>
      <div class="token" aria-label="Currency identity">
        <svg viewBox="0 0 512 512" role="img" aria-label="Clear token">
          <circle cx="256" cy="256" r="208" fill="#247c93"/>
          <circle cx="256" cy="256" r="122" fill="#f4fbfc"/>
          <path fill="#143d52"
            d="M256 48a208 208 0 0 0 0 416v-86a122 122 0 1 1 0-244z"/>
          <path fill="#e16f51" d="M222 224h168v64H222z"/>
        </svg>
        <div>
          <strong>{values['display_unit']}</strong>
          <span>Clear Mint Unit</span>
        </div>
      </div>
    </section>

    <div class="grid">
      <section class="panel">
        <h2>Mint details</h2>
        <dl>
          <div class="row"><dt>Currency</dt><dd>{values['currency_name']}</dd></div>
          <div class="row"><dt>Friendly name</dt><dd>{values['display_name']}</dd></div>
          <div class="row"><dt>Unit label</dt><dd>{values['display_unit']}</dd></div>
          <div class="row">
            <dt>Protocol unit</dt>
            <dd><code>{values['protocol_unit']}</code></dd>
          </div>
          <div class="row">
            <dt>Keyset</dt><dd><code>{values['keyset_id']}</code></dd>
          </div>
        </dl>
      </section>

      <section class="panel">
        <h2>How this mint works</h2>
        <ul class="features">
          <li>Treasurer-authorized issuance</li>
          <li>Private bearer transfers</li>
          <li>Mint-enforced double-spend protection</li>
          <li>Proof swapping and verification</li>
          <li>Explicit unit retirement</li>
          <li>{values['authority_label']}</li>
        </ul>
      </section>
    </div>

    <aside class="about">
      Clear units are organization-defined credits, vouchers, passes, or other
      transferable value. They are distinct from Bitcoin-backed cash and remain
      governed and redeemable according to the issuing organization's terms.
    </aside>

    <nav class="links" aria-label="Mint resources">
      <a href="/v1/info">Mint information</a>
      <a href="/v1/keys">Public keys</a>
      <a href="/docs">API documentation</a>
      <a href="https://trbouma.github.io/clear/">About Clear</a>
      <span class="version">
        Clear {values['version']} &middot; Developer-stage software
      </span>
    </nav>
  </main>
  <script>
    const button = document.getElementById("copy-mint");
    button.addEventListener("click", async () => {{
      try {{
        const mintUrl = document.getElementById("mint-url").textContent;
        await navigator.clipboard.writeText(mintUrl);
        button.textContent = "Copied";
      }} catch (_error) {{
        button.textContent = "Select URL to copy";
      }}
      window.setTimeout(() => {{ button.textContent = "Copy mint URL"; }}, 1800);
    }});
  </script>
</body>
</html>"""
