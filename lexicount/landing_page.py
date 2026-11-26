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
.lc-doc { padding: 28px 0 36px; }
.lc-doc-hero { display: grid; grid-template-columns: 1.25fr 1fr; gap: 24px; align-items: center; margin-bottom: 12px; }
.lc-doc-h1 { font-family: 'Playfair Display', Georgia, serif !important; font-weight: 400 !important; font-size: clamp(38px, 4vw, 54px) !important; letter-spacing: -.02em !important; line-height: 1.1 !important; margin: 10px 0 12px !important; color: var(--ink) !important; }
.lc-doc-h1 em { color: #7a5c43; font-style: italic; }
.lc-doc-lead { color: var(--subtle); font-size: 15.5px; line-height: 1.65; max-width: 620px; margin: 0 !important; }
.lc-doc-sec { font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: .18em; text-transform: uppercase; color: #88847c; margin: 34px 0 14px; }
.lc-grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.lc-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.lc-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.lc-dcard { background: #fff; border-radius: 22px; padding: 24px 26px; border: 1px solid rgba(29,29,26,.06); box-shadow: 0 4px 18px rgba(35,30,20,.03); transition: transform .2s ease, box-shadow .2s ease; }
.lc-dcard:hover { transform: translateY(-2px); box-shadow: 0 10px 26px rgba(35,30,20,.06); }
.lc-dcard.dark { background: #1d1d1a; color: #fff; border-color: #1d1d1a; }
.lc-dcard.sand { background: #ece5dc; border-color: rgba(122,92,67,.14); }
.lc-dcard .k { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: #88847c; margin-bottom: 8px; }
.lc-dcard.dark .k { color: #bdb5a9; }
.lc-dcard .t { font-family: 'Playfair Display', Georgia, serif; font-size: 22px; font-weight: 400; color: var(--ink); margin-bottom: 8px; line-height: 1.25; }
.lc-dcard.dark .t { color: #fff; }
.lc-dcard .f { font-family: 'DM Mono', monospace; font-size: 14.5px; color: #7a5c43; background: #f4f1ea; display: inline-block; padding: 5px 11px; border-radius: 8px; margin: 8px 0 12px; }
.lc-dcard.dark .f { color: #f4f1ea; background: rgba(255,255,255,.11); }
.lc-dcard p { color: var(--subtle); font-size: 14px; line-height: 1.6; margin: 0; }
.lc-dcard.dark p { color: #cfc9be; }
.lc-step-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.lc-step-num { font-family: 'Playfair Display', Georgia, serif; font-size: 32px; line-height: 1; color: #c9b8a6; }
.lc-step-ico { width: 36px; height: 36px; border-radius: 11px; background: #f4f1ea; display: flex; align-items: center; justify-content: center; color: #7a5c43; }
.lc-step-ico svg { width: 18px; height: 18px; stroke: currentColor; stroke-width: 1.8; fill: none; stroke-linecap: round; stroke-linejoin: round; }
.lc-pipe-box { background: #1d1d1a; color: #fff; border-radius: 22px; padding: 22px 24px; box-shadow: 0 14px 32px rgba(29,29,26,.14); }
.lc-pipe-label { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: #bdb5a9; margin-bottom: 14px; }
.lc-pipe-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.lc-pipe-node { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.12); border-radius: 10px; padding: 9px 12px; font-family: 'DM Mono', monospace; font-size: 11.5px; color: #f4f1ea; text-align: center; flex: 1; }
.lc-pipe-node.accent { background: #7a5c43; border-color: #7a5c43; color: #fff; }
.lc-pipe-workers { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 10px 0; }
.lc-pipe-w { background: rgba(255,255,255,.06); border: 1px dashed rgba(255,255,255,.2); border-radius: 9px; padding: 8px 6px; text-align: center; font-family: 'DM Mono', monospace; font-size: 10.5px; color: #e2d8cc; }
.lc-pipe-arrow { text-align: center; color: #8c877d; font-size: 12px; line-height: 1; margin: 4px 0; }
.lc-stats-2x2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.lc-stat-tile { background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.1); border-radius: 14px; padding: 14px 16px; }
.lc-stat-tile .sv { font-family: 'Playfair Display', Georgia, serif; font-size: 28px; color: #fff; line-height: 1.1; }
.lc-stat-tile .sk { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: #bdb5a9; margin-top: 6px; }
.lc-dtbl { width: 100%; border-collapse: collapse; border: none !important; }
.lc-dtbl thead, .lc-dtbl tbody, .lc-dtbl tr { border: none !important; }
.lc-dtbl th { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: .16em; text-transform: uppercase; color: #88847c; font-weight: 400; text-align: left; padding: 0 14px 12px 0 !important; border: none !important; border-bottom: 1px solid #e6dfd4 !important; background: none !important; }
.lc-dtbl td { font-size: 14px; padding: 13px 14px 13px 0 !important; border: none !important; border-bottom: 1px solid #ece5dc !important; color: var(--ink); vertical-align: middle; line-height: 1.5; background: none !important; }
.lc-dtbl tr:last-child td { border-bottom: none !important; }
.lc-pill-code { display: inline-block; background: #f4f1ea; color: #7a5c43; font-family: 'DM Mono', monospace; font-size: 12px; padding: 3px 9px; border-radius: 7px; white-space: nowrap; }
.lc-dtbl td.d { color: var(--subtle); }
.lc-team-card { background: #fff; border-radius: 20px; padding: 22px 24px; border: 1px solid rgba(29,29,26,.06); display: flex; align-items: center; gap: 16px; box-shadow: 0 4px 16px rgba(35,30,20,.03); transition: transform .2s ease; }
.lc-team-card:hover { transform: translateY(-2px); }
.lc-avatar { width: 50px; height: 50px; border-radius: 50%; background: #1d1d1a; color: #f4f1ea; display: flex; align-items: center; justify-content: center; font-family: 'Playfair Display', Georgia, serif; font-size: 18px; flex: none; }
.lc-avatar.brown { background: #7a5c43; }
.lc-avatar.sand { background: #d9cfc2; color: #1d1d1a; }
.lc-team-name { font-family: 'Playfair Display', Georgia, serif; font-size: 20px; color: var(--ink); line-height: 1.2; }
.lc-team-sub { font-family: 'DM Mono', monospace; font-size: 10.5px; letter-spacing: .12em; text-transform: uppercase; color: #88847c; margin-top: 4px; }
.lc-meta-row { display: flex; justify-content: space-between; gap: 16px; padding: 12px 0; border-bottom: 1px solid rgba(29,29,26,.08); font-size: 14px; }
.lc-meta-row:last-child { border-bottom: none; padding-bottom: 2px; }
.lc-meta-row .mk { font-family: 'DM Mono', monospace; font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: #736d64; }
.lc-meta-row .mv { color: var(--ink); font-weight: 600; text-align: right; }
.lc-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.lc-chips span { background: #f4f1ea; border: 1px solid #e6dfd4; border-radius: 999px; padding: 6px 14px; font-family: 'DM Mono', monospace; font-size: 12px; color: var(--ink); }
.lc-doc-cta { display: flex; gap: 12px; margin-top: 30px; flex-wrap: wrap; }
.lc-doc-foot { border-top: 1px solid #e6dfd4; margin-top: 44px; padding-top: 20px; display: flex; justify-content: space-between; font-size: 13px; color: var(--subtle); flex-wrap: wrap; gap: 10px; }
.lc-doc-foot b { color: var(--ink); }
.lc-doc-foot .m { font-family: 'DM Mono', monospace; font-size: 12px; }
@media (max-width: 980px) { .lc-doc-hero, .lc-grid-4, .lc-grid-3, .lc-grid-2 { grid-template-columns: 1fr; } }
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
        ("Performance", "performance", "?view=performance"),
        ("How it works", "how-it-works", "?view=how-it-works"),
        ("About", "about", "?view=about"),
    )
    links = "".join(
        f'<a class="{"active" if active == key else ""}" data-lc-view="{key}" href="{href}" target="_self">{label}</a>'
        for label, key, href in items
    )
    cta = (
        ""
        if active == "analyzer"
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
        for target in ("home", "analyzer", "performance", "how-it-works", "about"):
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
        st.session_state["view"] = qp if qp in {"home", "analyzer", "performance", "how-it-works", "about"} else "home"
    current = active if active is not None else st.session_state["view"]
    st.markdown(SHARED_HEADER_CSS + _compact(_header(current)), unsafe_allow_html=True)
    _mount_smooth_nav()
    return current


def _how_it_works_html() -> str:
    """Visual MapReduce + PCAM walkthrough and performance formulas."""
    pdc_rows = (
        ("Partitioning (PCAM)", "chunker.py", "compute_chunks",
         "Splits the file into pieces that always end on a space or symbol, so no word is ever cut in half."),
        ("Agglomeration (PCAM)", "chunker.py", "chunk_size_bytes",
         "Groups text into megabyte-sized chunks (default 4 MB) so workers spend more time counting than waiting."),
        ("Communication (PCAM)", "parallel.py", "build_tasks",
         "Offset mode sends only the start and end positions of each chunk; send mode copies the full text bytes to compare speed."),
        ("Load Balancing", "parallel.py", "imap_unordered",
         "Creates more chunks than workers so any worker that finishes early immediately grabs the next piece."),
        ("Map Phase (+ Combiner)", "parallel.py", "map_chunk",
         "Each worker counts words in its chunk and sends back a short summary dictionary instead of millions of raw words."),
        ("Reduce Phase", "parallel.py", "total.update",
         "The main process combines each worker's counts into one final total as soon as results arrive."),
        ("Synchronization", "parallel.py", "Pool / close / join",
         "Waits until every worker has finished its chunks before sorting the final Top-N words."),
        ("Why Processes, Not Threads", "parallel.py", "multiprocessing.Pool",
         "Python's GIL lets only one thread run Python code at a time. Separate processes run truly in parallel on multiple CPU cores."),
    )
    rows_html = "".join(
        f'<tr><td><b>{concept}</b></td><td><span class="lc-pill-code">{fname}</span></td>'
        f'<td><span class="lc-pill-code">{func}</span></td><td class="d">{desc}</td></tr>'
        for concept, fname, func, desc in pdc_rows
    )
    return f"""
    <main class="lc-doc">
      <div class="lc-eyebrow">HOW IT WORKS</div>
      <h1 class="lc-doc-h1">MapReduce, <em>step by step.</em></h1>
      <p class="lc-doc-lead">LexiCount counts every word twice: first with one core (sequential), then with multiple cores at the same time (parallel), and checks that both give the exact same answer.</p>

      <div class="lc-doc-sec">01 · The 4-stage pipeline</div>
      <div class="lc-grid-4">
        <div class="lc-dcard">
          <div class="lc-step-top"><span class="lc-step-num">01</span></div>
          <div class="k">Partition</div>
          <div class="t">Split without cutting words</div>
          <p>The file is divided into chunks that always stop at a space or punctuation mark, so no word is ever split in two.</p>
        </div>
        <div class="lc-dcard">
          <div class="lc-step-top"><span class="lc-step-num">02</span></div>
          <div class="k">Map</div>
          <div class="t">Count at the same time</div>
          <p>Each worker reads its own chunk, counts the words inside it, and sends back a compact word-count list.</p>
        </div>
        <div class="lc-dcard">
          <div class="lc-step-top"><span class="lc-step-num">03</span></div>
          <div class="k">Reduce</div>
          <div class="t">Combine the totals</div>
          <p>As each worker finishes, the main process adds its counts into one shared total.</p>
        </div>
        <div class="lc-dcard">
          <div class="lc-step-top"><span class="lc-step-num">04</span></div>
          <div class="k">Verify</div>
          <div class="t">Check every word</div>
          <p>Every single word count is checked against the single-core run to prove both versions match 100%.</p>
        </div>
      </div>

      <div class="lc-doc-sec">02 · How PDC concepts map to the codebase</div>
      <div class="lc-dcard">
        <table class="lc-dtbl">
          <tr><th>PDC Concept</th><th>File</th><th>Function</th><th>What it does</th></tr>
          {rows_html}
        </table>
      </div>

      <div class="lc-doc-sec">03 · Performance metrics &amp; formulas</div>
      <div class="lc-grid-4">
        <div class="lc-dcard dark">
          <div class="k">Speedup · S</div>
          <div class="t">How much faster</div>
          <div class="f">S = T_seq / T_par</div>
          <p>Compares single-core time to parallel time. Above 1.0× means the parallel run was faster.</p>
        </div>
        <div class="lc-dcard">
          <div class="k">Efficiency · E</div>
          <div class="t">How well cores are used</div>
          <div class="f">E = S / p</div>
          <p>Shows how close we got to ideal speedup across p workers. 100% is perfect; real runs are lower due to overhead.</p>
        </div>
        <div class="lc-dcard">
          <div class="k">Karp-Flatt · e</div>
          <div class="t">Serial portion</div>
          <div class="f">e = (1/S − 1/p) / (1 − 1/p)</div>
          <p>Estimates how much of the run could not be split across cores, such as starting workers and merging counts.</p>
        </div>
        <div class="lc-dcard">
          <div class="k">Amdahl's Law</div>
          <div class="t">Maximum speedup</div>
          <div class="f">S_max(p) = 1 / (e + (1 − e)/p)</div>
          <p>Shows the highest speedup possible for p workers. Even with infinite cores, speedup cannot pass 1 / e.</p>
        </div>
      </div>

      <div class="lc-doc-cta">
        <a class="lc-btn lc-btn-dark" data-lc-view="analyzer" href="?view=analyzer" target="_self">Try it in the Analyzer {ARROW_UP_RIGHT}</a>
        <a class="lc-btn lc-btn-light" data-lc-view="performance" href="?view=performance" target="_self">View Benchmark Results {ARROW_UP_RIGHT}</a>
      </div>

      <div class="lc-doc-foot">
        <div><b>lexicount</b> · BCS43 Parallel and Distributed Computing</div>
        <div class="m">S = T_seq / T_par · E = S / p</div>
      </div>
    </main>"""


def _about_html() -> str:
    """Rich editorial About page with monogram team cards and course details."""
    return f"""
    <main class="lc-doc">
      <div class="lc-eyebrow">ABOUT LEXICOUNT</div>
      <h1 class="lc-doc-h1">A PDC final project, <em>built for clarity.</em></h1>
      <p class="lc-doc-lead">LexiCount is a parallel word frequency analyzer built with data decomposition and MapReduce to show real multi-core speedup, exact correctness checks, and clear performance metrics.</p>

      <div class="lc-doc-sec">01 · Project overview</div>
      <div class="lc-grid-3">
        <div class="lc-dcard">
          <div class="k">01 · Problem</div>
          <div class="t">Large text is slow on one core</div>
          <p>Counting words across hundreds of megabytes of text on a single CPU core is slow and leaves the rest of the computer's cores idle.</p>
        </div>
        <div class="lc-dcard">
          <div class="k">02 · Solution</div>
          <div class="t">Data decomposition + MapReduce</div>
          <p>LexiCount splits files at safe word boundaries and counts chunks in parallel using Python's built-in multiprocessing library, with no external packages in the core engine.</p>
        </div>
        <div class="lc-dcard">
          <div class="k">03 · Evidence</div>
          <div class="t">Measured &amp; verified</div>
          <p>Every run checks that parallel and sequential counts match word-for-word, then reports execution time, speedup, efficiency, and serial overhead.</p>
        </div>
      </div>

      <div class="lc-doc-sec">02 · Development team</div>
      <div class="lc-grid-3">
        <div class="lc-team-card">
          <div class="lc-avatar">HB</div>
          <div><div class="lc-team-name">Harlene J. Bautista</div><div class="lc-team-sub">Member 01 · BCS43</div></div>
        </div>
        <div class="lc-team-card">
          <div class="lc-avatar brown">TD</div>
          <div><div class="lc-team-name">Timothy Rhine L. De Castro</div><div class="lc-team-sub">Member 02 · BCS43</div></div>
        </div>
        <div class="lc-team-card">
          <div class="lc-avatar sand">ND</div>
          <div><div class="lc-team-name">Nica Estelle R. Desacola</div><div class="lc-team-sub">Member 03 · BCS43</div></div>
        </div>
      </div>

      <div class="lc-doc-sec">03 · Course details &amp; tech stack</div>
      <div class="lc-grid-2">
        <div class="lc-dcard sand">
          <div class="k">Academic Details</div>
          <div class="t" style="margin-bottom: 12px;">Course &amp; Institution</div>
          <div class="lc-meta-row"><span class="mk">University</span><span class="mv">De La Salle University - Dasmariñas</span></div>
          <div class="lc-meta-row"><span class="mk">Department</span><span class="mv">CICS · Computer Science Department</span></div>
          <div class="lc-meta-row"><span class="mk">Course</span><span class="mv">BCS43 · Parallel and Distributed Computing</span></div>
          <div class="lc-meta-row"><span class="mk">Instructor</span><span class="mv">Sir Joseph Allen Ong</span></div>
          <div class="lc-meta-row"><span class="mk">Project Topic</span><span class="mv">Topic #8 · Word Frequency Analyzer</span></div>
        </div>
        <div class="lc-dcard">
          <div class="k">Core &amp; Presentation Layers</div>
          <div class="t" style="margin-bottom: 10px;">Technology Stack</div>
          <p>The parallel engine uses only Python's standard library so every step from splitting files to merging counts is easy to follow. Matplotlib draws the benchmark charts, and Streamlit powers this live-demo interface.</p>
          <div class="lc-chips">
            <span>Python 3.10+</span>
            <span>multiprocessing.Pool</span>
            <span>collections.Counter</span>
            <span>re (bytes)</span>
            <span>time.perf_counter</span>
            <span>unittest</span>
            <span>matplotlib</span>
            <span>Streamlit (UI)</span>
          </div>
        </div>
      </div>

      <div class="lc-doc-cta">
        <a class="lc-btn lc-btn-dark" data-lc-view="analyzer" href="?view=analyzer" target="_self">Open Analyzer {ARROW_UP_RIGHT}</a>
        <a class="lc-btn lc-btn-light" data-lc-view="how-it-works" href="?view=how-it-works" target="_self">See How it works {ARROW_UP_RIGHT}</a>
      </div>

      <div class="lc-doc-foot">
        <div><b>lexicount</b> · De La Salle University - Dasmariñas · CICS</div>
        <div class="m">BCS43 · Parallel and Distributed Computing</div>
      </div>
    </main>"""


def render_landing_body(view: str) -> None:
    """Render the landing hero, How it works, or About page below the shared header."""
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
    elif view == "how-it-works":
        content = _how_it_works_html()
    else:
        content = _about_html()

    st.markdown(f'<div class="lc-page"><div class="lc-shell">{_compact(content)}</div></div>', unsafe_allow_html=True)


def render_landing(view: str) -> None:
    """Render the shared header + landing body."""
    render_header(view)
    render_landing_body(view)
