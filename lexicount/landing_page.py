"""The public landing view for the existing Streamlit analyzer."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


SHARED_HEADER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,400;0,500;1,400;1,500&display=swap');

html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
  background:
    radial-gradient(circle at 17% 17%, rgba(255,255,255,.94), transparent 34%),
    radial-gradient(circle at 78% 40%, rgba(215,205,186,.54), transparent 34%),
    radial-gradient(circle at 38% 76%, rgba(226,216,198,.62), transparent 41%),
    #f4f1ea !important;
  color: #1d1d1a;
  font-family: 'DM Sans', 'Manrope', sans-serif;
}
header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stToolbar"], [data-testid="stDecoration"], footer, #MainMenu { display: none !important; }
.stMainBlockContainer, .main .block-container {
  max-width: 1606px !important;
  width: 100% !important;
  margin: 0 auto !important;
  padding: 0 3.45% 48px !important;
  background: transparent !important;
  border-radius: 0 !important;
}
.stMarkdown { margin: 0 !important; }
.stElementContainer { margin: 0 !important; }
[data-testid="stVerticalBlock"] { gap: 0.6rem; }
.lc-header, .lc-header *, .lc-page, .lc-page * { box-sizing: border-box; }
.lc-header {
  --ink: #1d1d1a;
  display: grid; grid-template-columns: 1fr auto 1fr; align-items: center;
  padding: 9px 0 0; min-height: 78px;
  font-family: 'DM Sans', 'Manrope', sans-serif;
}
.lc-header a, .lc-page a { text-decoration: none !important; }
.lc-brand { color: #1d1d1a !important; font-family: 'Manrope', sans-serif; font-size: 24px; font-weight: 700; letter-spacing: -.075em; justify-self: start; }
.lc-nav { display: flex; align-items: center; gap: 3px; padding: 7px; background: rgba(255,255,255,.74); border: 1px solid rgba(255,255,255,.85); border-radius: 999px !important; backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
.lc-nav a { display: inline-flex; align-items: center; justify-content: center; color: #2f2d29 !important; padding: 11px 24px; min-height: 44px; border-radius: 999px !important; font-size: 15px; font-weight: 600; white-space: nowrap; transition: background .2s ease, color .2s ease; }
.lc-nav a:hover { background: rgba(29,29,26,.08); border-radius: 999px !important; }
.lc-nav a.active { background: #1d1d1a; color: #fff !important; border-radius: 999px !important; }
.lc-header-action { justify-self: end; }
.lc-btn {
  display: inline-flex; align-items: center; justify-content: center; gap: 24px;
  min-height: 60px; padding: 0 27px; border-radius: 999px; font-size: 15px;
  font-weight: 600; white-space: nowrap; transition: transform .2s ease, box-shadow .2s ease;
}
.lc-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(35,30,20,.12); }
.lc-btn-dark { background: #1d1d1a; color: #fff !important; }
.lc-btn-light { color: #1d1d1a !important; background: rgba(255,255,255,.88); border: 1px solid #d9d4ca; }
.lc-btn-icon { width: 20px; height: 20px; flex: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; fill: none; }
.lc-page {
  --ink: #1d1d1a;
  --subtle: #6d6a63;
  --line: #d9d4ca;
  color: var(--ink);
  position: relative;
  font-family: 'DM Sans', 'Manrope', sans-serif;
}
.lc-shell { position: relative; z-index: 1; width: 100%; margin: 0 auto; animation: lc-view-fade .22s ease-out; }
@keyframes lc-view-fade { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
.st-key-lc_nav_hidden {
  position: fixed !important; left: -9999px !important; top: -9999px !important;
  width: 1px !important; height: 1px !important; overflow: hidden !important;
  opacity: 0 !important; pointer-events: none !important;
}
iframe[height="0"] { display: none !important; }
.lc-hero { text-align: center; padding: 77px 24px 0; }
.lc-eyebrow, .lc-mini, .lc-under, .lc-flow {
  font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .11em;
}
.lc-eyebrow { color: #88847c; font-size: 11px; letter-spacing: .24em; }
.lc-headline { margin: 34px 0 38px; font-family: 'Playfair Display', Georgia, serif !important; font-size: clamp(56px, 5.6vw, 90px) !important; font-weight: 400 !important; letter-spacing: 0 !important; line-height: 1.11 !important; text-align: center !important; }
.lc-page h1 a, [data-testid="stHeaderActionElements"] { display: none !important; }
.lc-wordmark { width: min(1050px, 88vw); display: grid; grid-template-columns: repeat(9, 1fr); gap: 10px; margin: 0 auto; }
.lc-letter { display: flex; flex-direction: column; align-items: center; min-width: 0; }
.lc-mini { color: #b3aea5; font-size: clamp(11px, 1vw, 16px); letter-spacing: 0; height: 32px; }
.lc-glyph-slot { position: relative; width: 100%; text-align: center; }
.lc-count-mask { position: absolute; inset: 0; height: 1.12em; overflow: hidden; font-family: 'DM Mono', monospace; font-size: clamp(48px, 6.45vw, 97px); line-height: 1.12; color: #9b968d; animation: lc-count-fade 2.3s both; animation-delay: calc(var(--i) * .07s); }
.lc-count-stack { display: block; animation: lc-count-roll 2s steps(19, end) both; animation-delay: calc(var(--i) * .07s); }
.lc-count-stack span { display: block; height: 1.12em; }
.lc-glyph { font-family: 'Manrope', Arial, sans-serif; font-size: clamp(48px, 6.45vw, 97px); font-weight: 400; line-height: 1.12; letter-spacing: -.03em; animation: lc-reveal .55s both; animation-delay: calc(1.95s + var(--i) * .07s); }
.lc-under { color: #9a958a; margin-top: 10px; font-size: 9px; letter-spacing: 0; }
.lc-flow { display: flex; align-items: center; justify-content: center; gap: 16px; color: #817c72; margin: 16px 0 0; font-size: 10px; }
.lc-flow b { font-size: 18px; font-family: Arial, sans-serif; font-weight: 400; }
.lc-intro { color: #77736b; font-size: clamp(17px, 1.4vw, 20px); line-height: 1.55; width: min(650px, 100%); margin: 48px auto 26px !important; text-align: center !important; }
.lc-actions { display: flex; justify-content: center; gap: 13px; }
.lc-placeholder { min-height: calc(100vh - 78px); display: grid; place-items: center; text-align: center; padding: 40px 24px 120px; }
.lc-placeholder-inner { max-width: 700px; }
.lc-placeholder h1 { font: 400 clamp(54px, 7vw, 92px)/1.12 'Playfair Display', Georgia, serif; letter-spacing: 0; margin: 16px 0; }
.lc-placeholder p { color: var(--subtle); font-size: 18px; line-height: 1.55; margin: 0 auto 30px; max-width: 520px; }
.lc-page a:focus-visible { outline: 3px solid #8e785a; outline-offset: 4px; }
@keyframes lc-reveal { from { opacity: 0; transform: translateY(15px); filter: blur(5px); } to { opacity: 1; transform: translateY(0); filter: blur(0); } }
@keyframes lc-count-roll { from { transform: translateY(0); } to { transform: translateY(-21.28em); } }
@keyframes lc-count-fade { 0%, 83% { opacity: 1; } 100% { opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .lc-glyph, .lc-count-mask, .lc-count-stack { animation: none; } .lc-count-mask { display: none; } .lc-btn { transition: none; } }
@media (max-width: 900px) {
  .lc-header { grid-template-columns: auto 1fr; gap: 18px; padding: 17px 5%; }
  .lc-nav { grid-column: 1 / -1; grid-row: 2; justify-self: center; max-width: 100%; overflow-x: auto; }
  .lc-header-action { grid-column: 2; grid-row: 1; }
  .lc-hero { padding-top: 45px; }
}
@media (max-width: 600px) {
  .lc-brand { font-size: 21px; }
  .lc-header-action .lc-btn { min-height: 44px; padding: 0 15px; gap: 9px; font-size: 12px; }
  .lc-nav { gap: 0; padding: 5px; }
  .lc-nav a { padding: 11px 12px; min-height: 40px; font-size: 12px; }
  .lc-hero { padding: 35px 15px 0; }
  .lc-headline { margin: 25px 0 30px; }
  .lc-wordmark { width: 100%; gap: 2px; }
  .lc-mini { height: 19px; font-size: 9px; }
  .lc-glyph, .lc-count-mask { font-size: clamp(30px, 8vw, 48px); }
  .lc-under { font-size: 7px; margin-top: 5px; }
  .lc-flow { gap: 7px; font-size: 7px; margin-top: 10px; }
  .lc-flow b { font-size: 12px; }
  .lc-intro { margin-top: 30px; font-size: 16px; }
  .lc-actions { flex-wrap: wrap; }
  .lc-actions .lc-btn { min-height: 50px; padding: 0 18px; gap: 12px; font-size: 13px; }
}
</style>
"""

ARROW_UP_RIGHT = '<svg class="lc-btn-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19 19 5M8 5h11v11"/></svg>'
ARROW_DOWN = '<svg class="lc-btn-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v16m-7-7 7 7 7-7"/></svg>'


def _header(active: str) -> str:
    items = (
        ("Home", "home", "?view=home"),
        ("Analyzer", "analyzer", "?view=analyzer"),
        ("Analyzer (new)", "analyzer-v2", "?view=analyzer-v2"),
        ("How it works", "how-it-works", "?view=how-it-works"),
        ("About", "about", "?view=about"),
    )
    links = "".join(
        f'<a class="{"active" if active == key else ""}" data-lc-view="{key}" href="{href}" target="_self">{label}</a>'
        for label, key, href in items
    )
    cta = (
        ""
        if active in ("analyzer", "analyzer-v2")
        else f'<a class="lc-btn lc-btn-dark lc-header-action" data-lc-view="analyzer" href="?view=analyzer" target="_self">Start analyzing {ARROW_UP_RIGHT}</a>'
    )
    return f"""
    <header class="lc-header">
      <a class="lc-brand" data-lc-view="home" href="?view=home" target="_self" aria-label="LexiCount home">lexicount</a>
      <nav class="lc-nav" aria-label="Main navigation">{links}</nav>
      {cta}
    </header>"""


def _compact(markup: str) -> str:
    """Strip indentation so Markdown never interprets HTML lines as a code block."""
    return "".join(line.strip() for line in markup.splitlines())


def _set_view(target: str) -> None:
    """Update active view in session state without triggering a full page reload."""
    st.session_state["view"] = target
    st.query_params["view"] = target


def _mount_smooth_nav() -> None:
    """Intercept header/CTA link clicks so they trigger Streamlit reruns (no browser blink)."""
    with st.container(key="lc_nav_hidden"):
        for target in ("home", "analyzer", "analyzer-v2", "how-it-works", "about"):
            key_name = "lc_nav_" + target.replace("-", "_")
            st.button(target, key=key_name, on_click=_set_view, args=(target,))
    components.html(
        """<script>
        (function() {
          try {
            const doc = window.parent.document;
            if (doc._lcSmoothNavBound) return;
            doc._lcSmoothNavBound = true;
            doc.addEventListener("click", function(e) {
              const link = e.target && e.target.closest ? e.target.closest("[data-lc-view], [data-lc-trigger]") : null;
              if (!link) return;
              const trigger = link.getAttribute("data-lc-trigger");
              const view = link.getAttribute("data-lc-view");
              const cls = trigger
                ? ".st-key-" + trigger + " button"
                : ".st-key-lc_nav_" + view.replace(/-/g, "_") + " button";
              const btn = doc.querySelector(cls);
              if (btn) {
                e.preventDefault();
                btn.click();
              }
            }, true);
          } catch (err) {}
        })();
        </script>""",
        height=0,
    )


def render_header(active: str | None = None) -> str:
    """Render the single shared header used across every view (smooth SPA switching)."""
    if "view" not in st.session_state:
        qp = st.query_params.get("view", "home")
        st.session_state["view"] = qp if qp in {"home", "analyzer", "analyzer-v2", "how-it-works", "about"} else "home"
    current = active if active is not None else st.session_state["view"]
    st.markdown(SHARED_HEADER_CSS + _compact(_header(current)), unsafe_allow_html=True)
    _mount_smooth_nav()
    return current


def render_landing_body(view: str) -> None:
    """Render the landing hero or placeholder body below the shared header."""
    if view == "home":
        letters = "LEXICOUNT"
        codes = ("02", "e7", "19", "x4", "03", "n8", "11", "t2", "09")
        letter_html = "".join(
            f'<div class="lc-letter"><div class="lc-mini">{code}</div>'
            f'<div class="lc-glyph-slot" style="--i:{i}">'
            f'<div class="lc-count-mask" aria-hidden="true"><div class="lc-count-stack">'
            + "".join(f"<span>{(i * 7 + step * 3) % 10}</span>" for step in range(20))
            + '</div></div>'
            f'<div class="lc-glyph">{letter}</div></div>'
            f'<div class="lc-under">{i + 1:02d} / {((i * 3) % 5) + 2}</div></div>'
            for i, (letter, code) in enumerate(zip(letters, codes))
        )
        content = f"""
        <main class="lc-hero">
          <div class="lc-eyebrow">LESS NOISE. MORE MEANING.</div>
          <h1 class="lc-headline">Every word counts.</h1>
          <div class="lc-wordmark" aria-label="LEXICOUNT">{letter_html}</div>
          <div class="lc-flow">CHARACTERS <b aria-hidden="true">→</b> PARALLEL COUNTS <b aria-hidden="true">→</b> CLARITY</div>
          <p class="lc-intro">Turn text into perspective. Explore word frequencies with parallel processing, and see the patterns hiding in plain sight.</p>
          <div class="lc-actions">
            <a class="lc-btn lc-btn-dark" data-lc-view="analyzer" href="?view=analyzer" target="_self">Start analyzing {ARROW_UP_RIGHT}</a>
            <a class="lc-btn lc-btn-light" data-lc-view="how-it-works" href="?view=how-it-works" target="_self">See how it works {ARROW_DOWN}</a>
          </div>
        </main>"""
    else:
        title = "How it works" if view == "how-it-works" else "About LexiCount"
        content = f"""
        <main class="lc-placeholder"><div class="lc-placeholder-inner">
          <div class="lc-eyebrow">LEXICOUNT</div>
          <h1>{title}</h1>
          <p>This page is coming soon. The analyzer is ready to use now.</p>
          <a class="lc-btn lc-btn-dark" data-lc-view="analyzer" href="?view=analyzer" target="_self">Open analyzer {ARROW_UP_RIGHT}</a>
        </div></main>"""

    st.markdown(f'<div class="lc-page"><div class="lc-shell">{_compact(content)}</div></div>', unsafe_allow_html=True)


def render_landing(view: str) -> None:
    """Render the shared header + landing body."""
    render_header(view)
    render_landing_body(view)
