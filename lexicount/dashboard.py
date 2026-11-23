"""LexiCount dashboard (OPTIONAL, for the live demo).

Run with:
    python -m streamlit run dashboard.py

Pages (top navigation): Home, Analyzer, How it works, About.
The core program (main.py, parallel.py, ...) does not need Streamlit;
this file only presents the results.
"""

import glob
import html
import io
import os
import platform

if __name__ != "__mp_main__":
    import streamlit as st

from dataset_generator import DATA_DIR
from main import find_differences, interpret
from metrics import efficiency, karp_flatt, speedup
from parallel import parallel_count
from sequential import sequential_count

MB = 1024 * 1024
CPU_COUNT = os.cpu_count() or 1
WORKER_OPTIONS = [1, 2, 4, 8]
CHUNK_OPTIONS = ["1 MB", "4 MB", "16 MB"]
STAGES = [  # (timing key, label, colour used in the stacked bar)
    ("pool_startup", "Pool start-up", "#c9b8a6"),
    ("partition", "Word-safe partitioning", "#7a5c43"),
    ("map_reduce", "Map + reduce", "#1a1a1a"),
    ("pool_shutdown", "Pool join &amp; teardown", "#e2d8cc"),
    ("sort", "Frequency sort", "#5a4636"),
]
PDC_ROWS = [
    ("Partitioning (PCAM)", "chunker.py", "compute_chunks",
     "Splits the file into contiguous byte ranges that end on a non-letter byte, so no word is cut."),
    ("Agglomeration (PCAM)", "chunker.py", "chunk size",
     "Groups bytes into MB-sized chunks so each task is big enough to outweigh its overhead."),
    ("Communication (PCAM)", "parallel.py", "build_tasks",
     "Offset mode sends only (path, start, end); send mode ships the chunk bytes through a pipe."),
    ("Mapping / Load balancing", "parallel.py", "imap_unordered",
     "Many chunks, chunksize=1: an idle worker immediately takes the next chunk."),
    ("Map phase + combiner", "parallel.py", "map_chunk",
     "Each worker counts its chunk locally and returns a small Counter, not raw words."),
    ("Reduce phase", "parallel.py", "total.update",
     "The master merges partial Counters in place as soon as each one arrives."),
    ("Synchronization", "parallel.py", "Pool / close / join",
     "Final ranking starts only after every chunk has been mapped and reduced."),
    ("GIL - processes, not threads", "parallel.py", "multiprocessing.Pool",
     "Each process has its own interpreter and GIL, so counting truly runs on several cores."),
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

:root { --ink:#1d1d1a; --muted:#6f6a62; --soft:#9a948a; --cream:#f4f1ea;
        --sand:#f1ece4; --line:#e6dfd4; --brown:#7a5c43; }

[data-testid="stMarkdownContainer"] p { margin-bottom:0; }

/* ---------- analyzer typography ---------- */
.lc-an-head { padding-top:28px; display:flex; justify-content:space-between; align-items:flex-end; flex-wrap:wrap; gap:12px; }
.lc-specs { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:22px; }
.lc-specs span { background:rgba(255,255,255,.74); border:1px solid rgba(255,255,255,.85);
  border-radius:999px; padding:5px 12px; font-family:'JetBrains Mono',monospace;
  font-size:0.7rem; color:var(--muted); white-space:nowrap; }

/* ---------- typography ---------- */
.lc-eyebrow { font-family:'JetBrains Mono',monospace; font-size:0.66rem; letter-spacing:0.22em;
  text-transform:uppercase; color:var(--soft); }
.lc-h1 { font-family:'Playfair Display',serif; font-weight:400; font-size:3.1rem;
  letter-spacing:-0.02em; line-height:1.1; margin:10px 0 8px 0; color:var(--ink); }
.lc-h1 em { color:var(--brown); font-style:italic; }
.lc-lead { font-size:0.88rem; color:var(--muted); margin-bottom:22px; }
.lc-label { font-family:'JetBrains Mono',monospace; font-size:0.62rem; letter-spacing:0.18em;
  text-transform:uppercase; color:var(--muted); line-height:1.4; margin:0; padding:0 0 12px; }
.lc-h3 { font-family:'Playfair Display',serif; font-size:1.35rem; font-weight:400; color:var(--ink); }

/* ---------- controls card ---------- */
.st-key-controls { background:#fff; border-radius:22px; padding:22px 24px 20px 24px; }
.st-key-controls [data-testid="stAlert"] { margin:14px 0 18px; }
div[data-baseweb="select"] > div, div[data-baseweb="input"], div[data-baseweb="base-input"] {
  background:var(--sand) !important; border:none !important; border-radius:10px !important; }
div[data-baseweb="select"] *, input { color:var(--ink) !important; font-size:0.82rem !important; }
[data-testid="stNumberInput"] button { background:var(--sand) !important; border:none !important; color:var(--ink) !important; }

/* IPC segmented toggle (HTML pill, 100% clickable) */
.lc-seg { display:inline-flex; align-items:center; gap:2px; background:var(--sand);
  border-radius:10px; padding:4px; }
.lc-seg a { padding:7px 16px; border-radius:7px; font-family:'JetBrains Mono',monospace;
  font-size:0.78rem; font-weight:500; color:var(--ink) !important; text-decoration:none !important;
  cursor:pointer; user-select:none; transition:background .15s ease, color .15s ease; }
.lc-seg a:hover { background:rgba(29,29,26,.06); }
.lc-seg a.on { background:var(--ink); color:#fff !important; }

/* file uploader (compact single row, text left, dark Upload button right) */
[data-testid="stFileUploaderDropzone"] {
  display:flex !important; flex-direction:row-reverse !important; justify-content:space-between !important;
  align-items:center !important; background:#fff !important; border:1px dashed #d6ccbf !important;
  border-radius:10px !important; padding:5px 8px 5px 14px !important; min-height:42px !important; }
[data-testid="stFileUploaderDropzone"] button {
  background:var(--ink) !important; color:#fff !important; border:none !important;
  border-radius:8px !important; padding:5px 14px !important; font-size:0.78rem !important;
  font-weight:600 !important; min-height:30px !important; }
[data-testid="stFileUploaderDropzone"] button:hover { background:#333 !important; }
[data-testid="stFileUploaderDropzoneInstructions"] { margin:0 !important; }
[data-testid="stFileUploaderDropzoneInstructions"] > span { display:none !important; }
[data-testid="stFileUploaderDropzoneInstructions"] small {
  color:var(--muted) !important; font-size:0.78rem !important; }

/* run button (scoped to analyzer controls card) */
.st-key-controls .stButton > button { background:var(--ink) !important; color:#fff !important; border:none !important;
  border-radius:999px !important; padding:10px 28px !important; font-weight:600 !important;
  font-size:0.84rem !important; }
.st-key-controls .stButton > button:hover { background:#333 !important; }
.st-key-controls .stButton > button p { color:#fff !important; }

/* subtabs pill (exact match to mockup: white rounded pill container + dark rounded active pill) */
.lc-subtabs { display:inline-flex; align-items:center; gap:4px; background:#fff;
  border-radius:999px; padding:5px; margin:18px 0 12px 0;
  box-shadow:0 1px 4px rgba(0,0,0,0.03); }
.lc-subtabs a { padding:10px 22px; border-radius:999px; font-family:'DM Sans',sans-serif;
  font-size:0.85rem; font-weight:500; color:var(--ink) !important; text-decoration:none !important;
  cursor:pointer; user-select:none; white-space:nowrap;
  transition:background .15s ease, color .15s ease; }
.lc-subtabs a:hover { background:rgba(29,29,26,.06); }
.lc-subtabs a.on { background:var(--ink); color:#fff !important; }
.st-key-lc_an_hidden {
  position:fixed !important; left:-9999px !important; top:-9999px !important;
  width:1px !important; height:1px !important; overflow:hidden !important;
  opacity:0 !important; pointer-events:none !important; }

/* ---------- result blocks ---------- */
.lc-run { font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:var(--brown); margin:6px 0 14px 0; }
.lc-kpis { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; }
.lc-kpi { background:#fff; border-radius:18px; padding:18px 18px 16px 18px; }
.lc-kpi.dark { background:var(--ink); }
.lc-kpi .k { font-family:'JetBrains Mono',monospace; font-size:0.62rem; letter-spacing:0.16em;
  text-transform:uppercase; color:var(--muted); }
.lc-kpi .v { font-family:'Playfair Display',serif; font-size:2.2rem; margin:14px 0 6px 0; color:var(--ink); }
.lc-kpi .s { font-size:0.72rem; color:var(--muted); }
.lc-kpi.dark .k, .lc-kpi.dark .s { color:#bdb5a9; } .lc-kpi.dark .v { color:#fff; }
.lc-ok { background:#fff; border-radius:16px; padding:14px 18px; display:flex; gap:14px;
  align-items:center; margin-top:14px; font-size:0.8rem; color:var(--ink); }
.lc-ok .dot { width:28px; height:28px; border-radius:50%; background:var(--ink); color:#fff;
  display:flex; align-items:center; justify-content:center; font-size:0.8rem; flex:none; }
.lc-ok.bad .dot { background:#9b2c2c; }
.lc-note { background:#ece5dc; border-radius:16px; padding:16px 20px; margin-top:12px; }
.lc-note p { font-size:0.86rem; line-height:1.6; color:#2d2a26; margin-top:8px; max-width:none; }
.lc-grid2 { display:grid; grid-template-columns:1.65fr 1fr; gap:12px; margin-top:14px; align-items:start; }
.lc-card { background:#fff; border-radius:18px; padding:20px 22px; }
.lc-stack { display:flex; flex-direction:column; gap:12px; }
.lc-cardhead { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:14px; }
.lc-mini { font-family:'JetBrains Mono',monospace; font-size:0.64rem; color:var(--brown); }
.lc-bar { display:grid; grid-template-columns:26px 70px 1fr 90px; align-items:center; gap:10px; margin:9px 0; }
.lc-bar .i { font-family:'JetBrains Mono',monospace; font-size:0.66rem; color:var(--soft); }
.lc-bar .w { font-family:'JetBrains Mono',monospace; font-size:0.74rem; color:var(--ink); }
.lc-bar .t { background:var(--sand); height:9px; border-radius:999px; overflow:hidden; }
.lc-bar .f { height:100%; border-radius:999px; background:var(--ink); }
.lc-bar .c { font-family:'JetBrains Mono',monospace; font-size:0.7rem; text-align:right; color:var(--ink); }
.lc-split { display:flex; height:8px; border-radius:999px; overflow:hidden; margin:4px 0 16px 0; }
.lc-tbl { width:100%; border-collapse:collapse; border:none !important; }
.lc-tbl tr { border:none !important; }
.lc-tbl th { font-family:'JetBrains Mono',monospace; font-size:0.64rem; letter-spacing:0.14em;
  text-transform:uppercase; color:var(--muted); font-weight:400; text-align:left; padding:0 0 10px 0 !important;
  border:none !important; border-bottom:1px solid var(--line) !important; background:none !important; }
.lc-tbl td { font-size:0.8rem; padding:11px 0 !important; border:none !important;
  border-bottom:1px solid var(--line) !important; color:var(--ink); background:none !important; }
.lc-tbl .r { text-align:right; font-family:'JetBrains Mono',monospace; font-size:0.76rem; padding-left:14px !important; }
.lc-tbl tr:last-child td { border-bottom:none !important; }
.lc-tbl tr.total td { font-weight:600; border-bottom:none !important; border-top:1px solid #cfc6b9 !important; padding-top:12px !important; }
.lc-sq { display:inline-block; width:8px; height:8px; border-radius:2px; margin-right:9px; }
.lc-foot2 { font-size:0.7rem; color:var(--muted); margin-top:12px; line-height:1.5; }
.lc-foot { border-top:1px solid var(--line); margin:46px 0 0 0; padding:20px 0;
  display:flex; justify-content:space-between; font-size:0.74rem; color:var(--muted); }
.lc-foot b { color:var(--ink); }
.lc-foot .m { font-family:'JetBrains Mono',monospace; font-size:0.68rem; }

/* ---------- home page ---------- */
.lc-hero { text-align:center; padding:30px 0 10px 0; }
.lc-hero .big { font-family:'Playfair Display',serif; font-size:4.6rem; letter-spacing:-0.02em; margin:16px 0 26px 0; }
.lc-letters { display:flex; justify-content:center; gap:4.2vw; }
.lc-letters div { display:flex; flex-direction:column; align-items:center; gap:10px; }
.lc-letters .code { font-family:'JetBrains Mono',monospace; font-size:0.66rem; color:var(--soft); }
.lc-letters .ch { font-family:'DM Sans',sans-serif; font-weight:300; font-size:4.2rem; line-height:1; }
.lc-flow { font-family:'JetBrains Mono',monospace; font-size:0.64rem; letter-spacing:0.18em;
  color:var(--muted); margin:26px 0 30px 0; }
.lc-hero p { color:var(--muted); font-size:0.95rem; max-width:560px; margin:0 auto 26px auto; line-height:1.6; }
.lc-btn { display:inline-block; padding:12px 24px; border-radius:999px; font-size:0.84rem; font-weight:600;
  text-decoration:none !important; margin:0 5px; }
.lc-btn.dark { background:var(--ink); color:#fff !important; }
.lc-btn.light { background:#fff; color:var(--ink) !important; }
.lc-cols3 { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin-top:44px; }
.lc-cols3 .lc-card p { font-size:0.82rem; color:var(--muted); line-height:1.6; margin-top:8px; }
.lc-pdc td { vertical-align:top; padding:12px 12px 12px 0; }
.lc-pdc td.d { color:var(--muted); }
</style>
"""


# ---------------------------------------------------------------- helpers

def extract_text(uploaded_file) -> str:
    """Return the plain text of an uploaded .txt, .pdf or .docx file."""
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".pdf"):
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith(".docx"):
        import docx
        document = docx.Document(io.BytesIO(data))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    return data.decode("utf-8", errors="ignore")


def save_upload(uploaded_file) -> None:
    """Convert an uploaded document to .txt inside data/ (once)."""
    base_name = os.path.splitext(uploaded_file.name)[0]
    path = os.path.join(DATA_DIR, f"{base_name}.txt")
    if os.path.isfile(path):
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    with st.spinner(f"Extracting text from {uploaded_file.name}..."):
        with open(path, "w", encoding="utf-8", errors="ignore") as file:
            file.write(extract_text(uploaded_file))
    st.rerun()


def list_datasets() -> list[str]:
    """All .txt files in data/, smallest first."""
    return sorted(glob.glob(os.path.join(DATA_DIR, "*.txt")), key=os.path.getsize)


def dataset_label(path: str) -> str:
    """Text shown in the dataset dropdown."""
    return f"{os.path.basename(path)} — {os.path.getsize(path) / MB:.1f} MB"


def show(markup: str) -> None:
    """Render raw HTML (lines are stripped so Markdown never treats them as code)."""
    st.markdown("".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def label(text: str) -> None:
    """Small mono caps label above a control."""
    show(f"<div class='lc-label'>{text}</div>")


# ---------------------------------------------------------------- layout pieces

def footer() -> None:
    """Bottom strip with course name and formulas."""
    show("""<div class='lc-foot'><div><b>lexicount</b> · Parallel and Distributed Computing</div>
    <div class='m'>S = T_seq / T_par · E = S / p</div></div>""")


def controls() -> dict | None:
    """The white control card. Returns the chosen settings."""
    datasets = list_datasets()
    if not datasets:
        st.warning("No datasets in data/. Run: python dataset_generator.py 1 10 100")
        return None
    default = next((i for i, p in enumerate(datasets) if "100MB" in p), 0)

    with st.container(key="controls"):
        c1, c2, c3, c4, c5 = st.columns([3.1, 1.6, 1.6, 1.5, 1.4], gap="medium")
        with c1:
            label("Source dataset")
            path = st.selectbox("dataset", datasets, index=default, format_func=dataset_label,
                                label_visibility="collapsed")
        with c2:
            label("Workers (p)")
            workers = st.slider(
                "workers",
                min_value=1,
                max_value=max(CPU_COUNT * 2, 8),
                value=min(CPU_COUNT, 4),
                label_visibility="collapsed",
            )
        with c3:
            label("Chunk size")
            chunk_mb = st.select_slider(
                "chunk",
                options=[0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0],
                value=4.0,
                format_func=lambda x: f"{x:g} MB",
                label_visibility="collapsed",
            )
        with c4:
            label("IPC channel")
            mode = st.session_state.setdefault("ipc_mode", "offset")
            show(
                f"<div class='lc-seg'>"
                f"<a class='{'on' if mode == 'offset' else ''}' data-lc-trigger='lc_ipc_offset' href='#'>Offset</a>"
                f"<a class='{'on' if mode == 'send' else ''}' data-lc-trigger='lc_ipc_send' href='#'>Send</a>"
                f"</div>"
            )
        with c5:
            label("Top N")
            top = st.number_input("top", min_value=5, max_value=25, value=10, label_visibility="collapsed")

        effective_mb = effective_chunk_size(path, int(workers), float(chunk_mb)) / MB
        if effective_mb < float(chunk_mb):
            st.warning(
                f"For this dataset and {workers} workers, the selected {chunk_mb:g} MB "
                f"chunk size will be reduced to about {effective_mb:.2f} MB per chunk."
            )

        f1, f2 = st.columns(2, gap="medium")
        with f1:
            label("Filter words")
            query = st.text_input("filter", placeholder="e.g. algorithm, data, love — leave empty for all",
                                  label_visibility="collapsed")
        with f2:
            label("Add custom dataset · .txt .pdf .docx")
            uploaded = st.file_uploader("upload", type=["txt", "pdf", "docx"], label_visibility="collapsed")
            if uploaded is not None:
                save_upload(uploaded)

        _, middle, _ = st.columns([2, 1, 2])
        with middle:
            run = st.button("▶  Run analysis", use_container_width=True)

    return {"path": path, "workers": int(workers), "chunk_mb": float(chunk_mb),
            "mode": mode.lower(), "top": int(top), "query": query, "run": run}


# ---------------------------------------------------------------- result blocks

def effective_chunk_size(path: str, workers: int, chunk_mb: float) -> int:
    """Size passed to the parallel counter after adapting to small files."""
    requested = int(chunk_mb * MB)
    file_size = os.path.getsize(path)
    return min(requested, max(32 * 1024, file_size // max(workers, 1))) if file_size > 0 else requested


def run_analysis(settings: dict) -> dict:
    """Run sequential + parallel and keep everything for display.

    The parallel run goes through parallel_count, exactly like main.py, so T_par
    is the full end-to-end time: starting the worker pool, partitioning,
    map + reduce, shutting the pool down and sorting. Leaving pool start-up out
    made efficiency look above 100% and Karp-Flatt negative. A new pool per run
    also means no idle worker processes are left behind between runs.
    """
    path = settings["path"]
    workers = settings["workers"]
    mode = settings["mode"]
    # Ensure small files (e.g. 0.6 MB books) split cleanly across all workers.
    eff_chunk = effective_chunk_size(path, workers, settings["chunk_mb"])

    with st.spinner("Running sequential baseline..."):
        seq_counts, seq_timings = sequential_count(path)

    with st.spinner(f"Running parallel MapReduce with {workers} workers..."):
        total, par_timings, stats = parallel_count(path, workers, eff_chunk, mode)

    return {"seq": seq_counts, "t_seq": seq_timings["total_time"], "par": total,
            "timings": par_timings, "stats": stats, **settings}


def kpi(title: str, value: str, sub: str, dark: bool = False) -> str:
    """One metric card."""
    return (f"<div class='lc-kpi {'dark' if dark else ''}'><div class='k'>{title}</div>"
            f"<div class='v'>{value}</div><div class='s'>{sub}</div></div>")


def kpi_row(res: dict) -> str:
    """Five metric cards; speedup is the dark highlighted one."""
    p, t_seq, t_par = res["workers"], res["t_seq"], res["timings"]["total"]
    s = speedup(t_seq, t_par)
    e = karp_flatt(s, p)
    return "<div class='lc-kpis'>" + "".join([
        kpi("Sequential · T_seq", f"{t_seq:.3f}s", "1 core reference"),
        kpi("Parallel · T_par", f"{t_par:.3f}s", f"{p} active workers"),
        kpi("Speedup · S", f"{s:.2f}×", "T_seq / T_par", dark=True),
        kpi("Efficiency · E", f"{efficiency(s, p):.1%}", "S / p"),
        kpi("Karp-Flatt · e", "n/a" if e is None else f"{e:.3f}", "estimated serial fraction"),
    ]) + "</div>"


def correctness_block(res: dict) -> str:
    """Badge saying whether the full Counters match."""
    seq, par = res["seq"], res["par"]
    if seq == par:
        return (f"<div class='lc-ok'><div class='dot'>✓</div><div><b>Correctness verified.</b> "
                f"Parallel and sequential counts match exactly across {len(seq):,} unique words "
                f"({seq.total():,} total). No words lost or duplicated at chunk boundaries.</div></div>")
    diffs = html.escape("; ".join(find_differences(seq, par, limit=5)))
    return f"<div class='lc-ok bad'><div class='dot'>✕</div><div><b>Mismatch.</b> {diffs}</div></div>"


def meaning_block(res: dict) -> str:
    """Plain-English interpretation of the numbers."""
    p = res["workers"]
    s = speedup(res["t_seq"], res["timings"]["total"])
    text = interpret(s, efficiency(s, p), p, karp_flatt(s, p))
    return f"<div class='lc-note'><div class='lc-eyebrow'>What this means</div><p>{text}</p></div>"


def word_bars(res: dict) -> str:
    """Top-N words (or the filtered words) as horizontal bars."""
    words = [w.strip().lower() for w in res["query"].replace(",", " ").split() if w.strip()]
    if words:
        rows, title = [(w, res["par"].get(w, 0)) for w in words], f"{len(words)} selected words"
    else:
        rows, title = res["par"].most_common(res["top"]), f"Top {res['top']} words"
    largest = max((count for _, count in rows), default=0) or 1
    bars = ""
    for rank, (word, count) in enumerate(rows, start=1):
        colour = "#7a5c43" if rank == 1 else "#1a1a1a"
        bars += (f"<div class='lc-bar'><span class='i'>{rank:02d}</span><span class='w'>{html.escape(word)}</span>"
                 f"<div class='t'><div class='f' style='width:{100 * count / largest:.1f}%;background:{colour}'></div></div>"
                 f"<span class='c'>{count:,}</span></div>")
    return (f"<div class='lc-card'><div class='lc-cardhead'><span class='lc-h3'>{title}</span>"
            f"<span class='lc-mini'>occurrences</span></div>{bars}</div>")


def time_card(res: dict) -> str:
    """Stacked bar + table of where the parallel run spent its time."""
    timings, total = res["timings"], res["timings"]["total"] or 1
    split = "".join(f"<div style='width:{100 * timings[k] / total:.2f}%;background:{c}'></div>"
                    for k, _, c in STAGES)
    rows = "".join(
        f"<tr><td><span class='lc-sq' style='background:{c}'></span>{name}</td>"
        f"<td class='r'>{timings[k]:.4f} s</td><td class='r'>{100 * timings[k] / total:.1f}%</td></tr>"
        for k, name, c in STAGES)
    rows += f"<tr class='total'><td>Total wall time</td><td class='r'>{total:.4f} s</td><td class='r'>100%</td></tr>"
    return (f"<div class='lc-card'><div class='lc-h3' style='margin-bottom:12px'>Where the time went</div>"
            f"<div class='lc-split'>{split}</div><table class='lc-tbl'><tr><th>Stage</th>"
            f"<th class='r'>Time</th><th class='r'>Share</th></tr>{rows}</table></div>")


def load_card(res: dict) -> str:
    """Chunks and busy time per worker process (LOAD BALANCING)."""
    stats = res["stats"]
    workers = sorted(stats["per_worker"].items())
    total_busy = sum(entry["busy"] for _, entry in workers) or 1
    rows = "".join(
        f"<tr><td>Worker {i} <span style='color:#9a948a;font-size:0.66rem'>pid {pid}</span></td>"
        f"<td class='r'>{entry['chunks']}</td><td class='r'>{entry['busy']:.2f}s</td>"
        f"<td class='r'>{100 * entry['busy'] / total_busy:.1f}%</td></tr>"
        for i, (pid, entry) in enumerate(workers, start=1))
    return (f"<div class='lc-card'><div class='lc-cardhead'><span class='lc-h3'>Load balancing</span>"
            f"<span class='lc-mini'>{stats['num_chunks']} chunks</span></div><table class='lc-tbl'>"
            f"<tr><th>Worker</th><th class='r'>Chunks</th><th class='r'>Busy</th><th class='r'>Share</th></tr>"
            f"{rows}</table><div class='lc-foot2'>Filled per run from worker PIDs. Chunks are handed out "
            f"with imap_unordered, so a free worker takes the next one.</div></div>")


def results_view(res: dict) -> None:
    """Everything shown after a run."""
    actual_mb = res["stats"]["chunk_size"] / MB
    show(f"<div class='lc-run'>Last run · {html.escape(os.path.basename(res['path']))} · p = {res['workers']}"
         f" · {actual_mb:.2f} MB chunks · {res['mode']} IPC</div>")
    show(kpi_row(res) + correctness_block(res) + meaning_block(res))
    show(f"<div class='lc-grid2'>{word_bars(res)}<div class='lc-stack'>{time_card(res)}{load_card(res)}</div></div>")


def pdc_table() -> str:
    """Concept -> file -> function table."""
    rows = "".join(f"<tr><td><b>{c}</b></td><td class='r' style='text-align:left'>{f}</td>"
                   f"<td class='r' style='text-align:left'>{fn}</td><td class='d'>{d}</td></tr>"
                   for c, f, fn, d in PDC_ROWS)
    return (f"<div class='lc-card'><table class='lc-tbl lc-pdc'><tr><th>Concept</th><th>File</th>"
            f"<th>Function</th><th>What it does</th></tr>{rows}</table></div>")


# ---------------------------------------------------------------- pages

def analyzer_page() -> None:
    """Controls + live experiment + PDC architecture tabs."""
    show(f"""
    <div class='lc-an-head'>
      <div>
        <div class='lc-eyebrow'>Analyzer</div>
        <div class='lc-h1'>Parallel word frequency, <em>measured.</em></div>
        <div class='lc-lead'>Data decomposition and MapReduce over a multi-core process pool.</div>
      </div>
      <div class='lc-specs'>
        <span>{platform.system()} · {platform.machine()}</span>
        <span>{CPU_COUNT} logical cores</span>
        <span>Python {platform.python_version()}</span>
      </div>
    </div>""")
    with st.container(key="lc_an_hidden"):
        st.button("ipc_offset", key="lc_ipc_offset", on_click=lambda: st.session_state.__setitem__("ipc_mode", "offset"))
        st.button("ipc_send", key="lc_ipc_send", on_click=lambda: st.session_state.__setitem__("ipc_mode", "send"))
        st.button("subtab_live", key="lc_subtab_live", on_click=lambda: st.session_state.__setitem__("an_tab", "live"))
        st.button("subtab_theory", key="lc_subtab_theory", on_click=lambda: st.session_state.__setitem__("an_tab", "theory"))

    settings = controls()
    if settings is None:
        return
    if settings["run"]:
        st.session_state["results"] = run_analysis(settings)

    active_tab = st.session_state.setdefault("an_tab", "live")
    show(
        f"<div class='lc-subtabs'>"
        f"<a class='{'on' if active_tab == 'live' else ''}' data-lc-trigger='lc_subtab_live' href='#'>Live experiment</a>"
        f"<a class='{'on' if active_tab == 'theory' else ''}' data-lc-trigger='lc_subtab_theory' href='#'>PDC architecture</a>"
        f"</div>"
    )
    if active_tab == "live":
        res = st.session_state.get("results")
        if res:
            res["query"] = settings["query"]  # filter can change without re-running
            results_view(res)
        else:
            show("<div class='lc-note'><div class='lc-eyebrow'>Ready</div>"
                 "<p>Choose a dataset, workers and chunk size, then press <b>Run analysis</b>.</p></div>")
    else:
        show(pdc_table())


def home_page() -> None:
    """Landing hero."""
    letters = "".join(
        f"<div><span class='code'>{code}</span><span class='ch'>{ch}</span>"
        f"<span class='code'>{i:02d} / {len(ch) + i % 6}</span></div>"
        for i, (ch, code) in enumerate(zip("LEXICOUNT", ["02", "e7", "19", "x4", "03", "n8", "11", "t2", "09"]), 1))
    show(f"""
    <div class='lc-hero'>
      <div class='lc-eyebrow'>Less noise. More meaning.</div>
      <div class='big'>Every word counts.</div>
      <div class='lc-letters'>{letters}</div>
      <div class='lc-flow'>CHARACTERS &nbsp;⟶&nbsp; PARALLEL COUNTS &nbsp;⟶&nbsp; CLARITY</div>
      <p>Turn text into perspective. Explore word frequencies with parallel processing,
         and see the patterns hiding in plain sight.</p>
      <a class='lc-btn dark' href='?page=analyzer' target='_self'>Start analyzing &nbsp;↗</a>
      <a class='lc-btn light' href='?page=how' target='_self'>See how it works &nbsp;↓</a>
    </div>
    <div class='lc-cols3'>
      <div class='lc-card'><div class='lc-eyebrow'>01 · Partition</div><div class='lc-h3'>Word-safe chunks</div>
        <p>The file is cut into byte ranges that always end on a non-letter, so no word is ever split.</p></div>
      <div class='lc-card'><div class='lc-eyebrow'>02 · Map</div><div class='lc-h3'>Many cores at once</div>
        <p>Worker processes count their chunks in parallel and return small partial counts.</p></div>
      <div class='lc-card'><div class='lc-eyebrow'>03 · Reduce</div><div class='lc-h3'>One verified answer</div>
        <p>The master merges the counts and checks them word-for-word against the sequential run.</p></div>
    </div>""")


def how_page() -> None:
    """PDC concepts explained."""
    show("<div class='lc-eyebrow'>How it works</div><div class='lc-h1'>MapReduce, <em>step by step.</em></div>"
         "<div class='lc-lead'>How each Parallel and Distributed Computing concept maps to the code.</div>")
    show(pdc_table())
    show("""<div class='lc-cols3' style='margin-top:12px'>
      <div class='lc-card'><div class='lc-eyebrow'>Speedup</div><div class='lc-h3'>S = T_seq / T_par</div>
        <p>How many times faster the parallel version is than one core.</p></div>
      <div class='lc-card'><div class='lc-eyebrow'>Efficiency</div><div class='lc-h3'>E = S / p</div>
        <p>How well the p workers are used; 100% would be perfect linear scaling.</p></div>
      <div class='lc-card'><div class='lc-eyebrow'>Karp-Flatt</div><div class='lc-h3'>e = (1/S − 1/p) / (1 − 1/p)</div>
        <p>The measured serial fraction; by Amdahl's Law the speedup can never exceed 1 / e.</p></div>
    </div>""")


def about_page() -> None:
    """Short project description."""
    show("<div class='lc-eyebrow'>About</div><div class='lc-h1'>A PDC final project, <em>explained.</em></div>"
         "<div class='lc-lead'>LexiCount: A Parallel Word Frequency Analyzer Using Data Decomposition and MapReduce.</div>")
    show("""<div class='lc-cols3' style='margin-top:0'>
      <div class='lc-card'><div class='lc-eyebrow'>Problem</div><div class='lc-h3'>Big text is slow</div>
        <p>Counting words in hundreds of megabytes on a single core leaves the rest of the CPU idle.</p></div>
      <div class='lc-card'><div class='lc-eyebrow'>Solution</div><div class='lc-h3'>Split, count, merge</div>
        <p>Data decomposition plus MapReduce on Python's multiprocessing pool, standard library only.</p></div>
      <div class='lc-card'><div class='lc-eyebrow'>Evidence</div><div class='lc-h3'>Measured, not assumed</div>
        <p>Execution time, speedup, efficiency, Karp-Flatt and a full correctness check on every run.</p></div>
    </div>""")


def main() -> None:
    """Page router with one shared header and smooth no-reload tab switching."""
    from landing_page import render_header, render_landing_body

    st.set_page_config(page_title="lexicount", layout="wide", initial_sidebar_state="collapsed")
    active = render_header()
    if active == "analyzer":
        st.markdown(CSS, unsafe_allow_html=True)
        analyzer_page()
        footer()
    else:
        render_landing_body(active)


if __name__ == "__main__":
    main()
