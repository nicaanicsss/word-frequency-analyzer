"""LexiCount - Modern Full-Width Top-Control Dashboard.
No sidebar: clean top control panel, balanced grid proportions, zero emojis,
crisp typography, and clear responsive visual hierarchy.
"""

import glob
import os
import platform

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import streamlit as st  # noqa: E402

from dataset_generator import DATA_DIR, generate_dataset  # noqa: E402
from main import find_differences  # noqa: E402
from metrics import amdahl_speedup, efficiency, karp_flatt, speedup  # noqa: E402
from parallel import MODES, parallel_count  # noqa: E402
from sequential import sequential_count  # noqa: E402

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
MB = 1024 * 1024
CPU_COUNT = os.cpu_count() or 1
CHART_FILES = [
    ("Execution Time vs Workers", "execution_time_vs_workers.png"),
    ("Speedup vs Workers (Amdahl Curve)", "speedup_vs_workers.png"),
    ("Parallel Efficiency", "efficiency_vs_workers.png"),
    ("Execution Time vs File Size", "time_vs_file_size.png"),
    ("Agglomeration: Chunk Size Effect", "chunk_size_effect.png"),
    ("Communication Overhead: Offset vs Send", "offset_vs_send.png"),
    ("Parallel Time Breakdown", "time_breakdown_stacked.png"),
]

st.set_page_config(
    page_title="LexiCount Analyzer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

/* Base Styles */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #090d16 !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', -apple-system, sans-serif !important;
}

/* Completely remove sidebar and unnecessary spacing */
[data-testid="stSidebar"] {
    display: none !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
}
header[data-testid="stHeader"] {
    display: none !important;
}
.main .block-container {
    max-width: 1440px !important;
    padding: 2.2rem 3rem 4rem 3rem !important;
}

/* Header Banner */
.brand-bar {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 1.4rem;
    margin-bottom: 1.8rem;
}
.brand-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0;
    letter-spacing: -0.03em;
}
.brand-subtitle {
    font-size: 0.88rem;
    color: #64748b;
    margin-top: 0.25rem;
}
.brand-meta {
    font-size: 0.78rem;
    color: #475569;
    text-align: right;
    line-height: 1.5;
}

/* Top Control Console */
.control-panel {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.25rem 1.6rem;
    margin-bottom: 1.8rem;
}
.control-heading {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #94a3b8;
    margin-bottom: 0.85rem;
}

/* Metric Cards */
.metric-card {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 8px;
    padding: 1.1rem 1.3rem;
    height: 100%;
}
.metric-header {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b;
}
.metric-stat {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    color: #f8fafc;
    margin: 0.35rem 0 0.15rem 0;
}
.metric-detail {
    font-size: 0.78rem;
    color: #475569;
}

/* Status Callouts */
.callout-success {
    background-color: #064e3b;
    border: 1px solid #059669;
    color: #a7f3d0;
    padding: 0.9rem 1.25rem;
    border-radius: 6px;
    font-size: 0.88rem;
    margin: 1.4rem 0;
}
.callout-danger {
    background-color: #7f1d1d;
    border: 1px solid #dc2626;
    color: #fecaca;
    padding: 0.9rem 1.25rem;
    border-radius: 6px;
    font-size: 0.88rem;
    margin: 1.4rem 0;
}

/* Tab Styling */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    border-bottom: 1px solid #1e293b !important;
    gap: 1.8rem !important;
    padding: 0 !important;
    margin-bottom: 1.4rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: #64748b !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    padding: 0.65rem 0 !important;
}
.stTabs [aria-selected="true"] {
    color: #38bdf8 !important;
    border-bottom: 2px solid #38bdf8 !important;
}

/* Button */
.stButton > button {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.65rem 1.4rem !important;
    transition: background 0.15s ease !important;
    width: 100% !important;
    margin-top: 1.7rem !important;
}
.stButton > button:hover {
    background-color: #1d4ed8 !important;
}

/* Clean Tables */
[data-testid="stTable"] {
    border: 1px solid #1e293b !important;
    border-radius: 6px !important;
    overflow: hidden !important;
}
table {
    font-size: 0.85rem !important;
    color: #cbd5e1 !important;
}
th {
    background-color: #131d33 !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    border-bottom: 1px solid #1e293b !important;
}
td {
    border-bottom: 1px solid #0f172a !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def list_datasets() -> list[str]:
    files = glob.glob(os.path.join(DATA_DIR, "*.txt"))
    return sorted(files, key=os.path.getsize)


def render_header():
    st.markdown(
        f"""
        <div class="brand-bar">
            <div>
                <h1 class="brand-title">LexiCount: Parallel Word Frequency Analyzer</h1>
                <div class="brand-subtitle">
                    Data Decomposition & MapReduce Architecture over Multi-Core Process Pools
                </div>
            </div>
            <div class="brand-meta">
                <b>Host Architecture:</b> {platform.system()} ({platform.machine()})<br>
                <b>Compute Nodes:</b> {CPU_COUNT} Logical Cores | Python {platform.python_version()}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_control_panel():
    datasets = list_datasets()
    if not datasets:
        st.error("No test datasets available in data/ directory. Please generate one.")
        return None

    default_idx = 0
    for idx, path in enumerate(datasets):
        if "100MB" in path:
            default_idx = idx
            break

    col1, col2, col3, col4, col5, col6 = st.columns([2.4, 1.6, 1.6, 1.8, 1.2, 1.4])

    with col1:
        selected_file = st.selectbox(
            "Source Dataset",
            datasets,
            index=default_idx,
            format_func=lambda p: f"{os.path.basename(p)} ({os.path.getsize(p) / MB:.1f} MB)"
        )

    with col2:
        workers = st.slider(
            "Workers (p)",
            min_value=1,
            max_value=max(CPU_COUNT * 2, 8),
            value=min(CPU_COUNT, 4),
            help="Number of parallel worker processes."
        )

    with col3:
        chunk_mb = st.select_slider(
            "Chunk Size",
            options=[0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0],
            value=4.0,
            format_func=lambda x: f"{x:g} MB"
        )

    with col4:
        mode = st.selectbox(
            "IPC Channel",
            MODES,
            index=0,
            format_func=lambda m: "Offset (Zero-Copy)" if m == "offset" else "Send (Data Copy)"
        )

    with col5:
        top_n = st.number_input("Top N", min_value=5, max_value=25, value=10)

    with col6:
        run_clicked = st.button("Run Analysis")

    # Row 2: Search Query on Left, File Management (Upload / Generate) on Right (50/50 split)
    col_search, col_manage = st.columns([1, 1], gap="medium")

    with col_search:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        search_query = st.text_input(
            "Search or Filter Specific Words",
            placeholder="Type words (e.g. 'algorithm, data, love') or leave empty for all",
            help="Filter the analysis to specific target keywords."
        )

    with col_manage:
        st.markdown("<p style='font-size:0.875rem; font-weight:400; color:#cbd5e1; margin-bottom:8px;'>Add Custom Dataset (.txt)</p>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload Book (.txt)",
            type=["txt"],
            label_visibility="collapsed",
            help="Upload any text file or book to analyze."
        )
        if uploaded_file is not None:
            save_path = os.path.join(DATA_DIR, uploaded_file.name)
            if not os.path.isfile(save_path):
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"Added {uploaded_file.name}")
                st.rerun()

    return {
        "path": selected_file,
        "workers": workers,
        "chunk_mb": chunk_mb,
        "mode": mode,
        "top": top_n,
        "search_query": search_query.strip(),
        "run": run_clicked
    }


def plot_top_words(counts: dict[str, int], top: int) -> plt.Figure:
    words, values = zip(*list(counts.items())[:top]) if counts else ((), ())
    figure, axis = plt.subplots(figsize=(8.2, 4.2), facecolor="#090d16")
    axis.set_facecolor("#090d16")

    words_rev = list(reversed(words))
    values_rev = list(reversed(values))

    bars = axis.barh(
        words_rev,
        values_rev,
        color="#2563eb",
        edgecolor="#3b82f6",
        height=0.6,
        linewidth=0.7
    )

    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["left"].set_color("#1e293b")
    axis.spines["bottom"].set_color("#1e293b")
    axis.tick_params(colors="#94a3b8", labelsize=9)
    axis.grid(axis="x", color="#1e293b", linestyle="--", alpha=0.6)

    for bar in bars:
        width = bar.get_width()
        axis.text(
            width + (max(values_rev) * 0.015 if values_rev else 1),
            bar.get_y() + bar.get_height() / 2,
            f"{int(width):,}",
            va="center",
            ha="left",
            color="#e2e8f0",
            fontsize=8.5,
            fontweight="500"
        )

    axis.set_title(f"Top {top} Lexical Frequencies", color="#f8fafc", fontsize=11, fontweight="600", pad=10)
    axis.set_xlabel("Occurrences", color="#64748b", fontsize=8.5, labelpad=8)
    figure.tight_layout()
    return figure


def main():
    render_header()
    controls = render_control_panel()
    if not controls:
        return

    tab_experiment, tab_architecture = st.tabs([
        "Live Experiment",
        "Theoretical PDC Architecture"
    ])

    with tab_experiment:
        # Initialize session state for persistent results across reruns
        if "results" not in st.session_state:
            st.session_state["results"] = None

        if controls["run"]:
            with st.spinner("Executing Sequential baseline (Single Core)..."):
                seq_counts, seq_timings = sequential_count(controls["path"])

            with st.spinner(f"Spawning {controls['workers']} MapReduce Worker Processes..."):
                chunk_bytes = int(controls["chunk_mb"] * MB)
                par_counts, par_timings, stats = parallel_count(
                    controls["path"], controls["workers"], chunk_bytes, controls["mode"]
                )

            st.session_state["results"] = {
                "seq_counts": seq_counts,
                "seq_timings": seq_timings,
                "par_counts": par_counts,
                "par_timings": par_timings,
                "stats": stats,
                "workers": controls["workers"],
                "top": controls["top"]
            }

        res = st.session_state["results"]

        if res:
            seq_counts = res["seq_counts"]
            seq_timings = res["seq_timings"]
            par_counts = res["par_counts"]
            par_timings = res["par_timings"]
            stats = res["stats"]
            p = res["workers"]
            top_n = res["top"]

            t_seq = seq_timings["total_time"]
            t_par = par_timings["total"]
            s = speedup(t_seq, t_par)
            eff = efficiency(s, p)
            serial = karp_flatt(s, p)

            # Row 1: Balanced KPI Metrics
            k1, k2, k3, k4, k5 = st.columns(5)
            with k1:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-header">Sequential (T_seq)</div>
                        <div class="metric-stat">{t_seq:.3f}s</div>
                        <div class="metric-detail">1 Core Reference</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with k2:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-header">Parallel (T_par)</div>
                        <div class="metric-stat">{t_par:.3f}s</div>
                        <div class="metric-detail">{p} Active Workers</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with k3:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-header">Speedup (S)</div>
                        <div class="metric-stat">{s:.2f}x</div>
                        <div class="metric-detail">T_seq / T_par</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with k4:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-header">Efficiency (E)</div>
                        <div class="metric-stat">{eff * 100:.1f}%</div>
                        <div class="metric-detail">S / p Ratio</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            with k5:
                e_val = f"{serial:.3f}" if serial is not None else "N/A"
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-header">Karp-Flatt (e)</div>
                        <div class="metric-stat">{e_val}</div>
                        <div class="metric-detail">Serial Fraction</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Row 2: Verification Banner
            if seq_counts == par_counts:
                st.markdown(
                    f"""
                    <div class="callout-success">
                        <b>Correctness Verified:</b> 100% dictionary equivalence across {len(seq_counts):,} unique words ({seq_counts.total():,} total words). Zero partitioning boundary loss.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                diffs = find_differences(seq_counts, par_counts, limit=5)
                st.markdown(
                    f"""
                    <div class="callout-danger">
                        <b>Correctness Alert:</b> Discrepancies detected: {'; '.join(diffs)}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Performance Interpretation (Rubric Requirement: Brief explanation of results)
            from main import interpret
            explanation_text = interpret(s, eff, p, serial)
            st.markdown(
                f"""
                <div style="background-color: #0f172a; border-left: 3px solid #38bdf8; border-radius: 4px; padding: 12px 18px; margin-bottom: 22px;">
                    <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #38bdf8; margin-bottom: 4px;">
                        Performance Evaluation & Analysis
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                        {explanation_text}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Row 3: Visual Analytics & Tabular Breakdowns
            col_left, col_right = st.columns([1.1, 0.9])

            with col_left:
                search_q = controls.get("search_query", "")
                if search_q:
                    # Filter dictionary to user-specified words
                    target_words = [w.strip().lower() for w in search_q.replace(",", " ").split() if w.strip()]
                    filtered_counts = {w: par_counts.get(w, 0) for w in target_words}
                    st.markdown(f"<p style='font-size:0.85rem; font-weight:600; color:#38bdf8; margin-bottom:6px;'>Specific Word Counts ({len(target_words)} selected)</p>", unsafe_allow_html=True)
                    st.pyplot(plot_top_words(filtered_counts, len(filtered_counts)))
                else:
                    st.pyplot(plot_top_words(par_counts, controls["top"]))

            with col_right:
                st.markdown("<p style='font-size:0.85rem; font-weight:600; color:#f8fafc; margin-bottom:6px;'>Stage Breakdown</p>", unsafe_allow_html=True)
                stages = [
                    ("Pool Initialization", f"{par_timings['pool_startup']:.4f} s"),
                    ("Word-Safe Partitioning", f"{par_timings['partition']:.4f} s"),
                    ("Map + Reduce Compute", f"{par_timings['map_reduce']:.4f} s"),
                    ("Pool Join & Teardown", f"{par_timings['pool_shutdown']:.4f} s"),
                    ("Frequency Sort", f"{par_timings['sort']:.4f} s"),
                    ("Total Clock Time", f"{par_timings['total']:.4f} s"),
                ]
                st.table({
                    "Pipeline Stage": [s[0] for s in stages],
                    "Duration": [s[1] for s in stages]
                })

                st.markdown(f"<p style='font-size:0.85rem; font-weight:600; color:#f8fafc; margin-top:14px; margin-bottom:6px;'>Load Balancing ({stats['num_chunks']} Chunks)</p>", unsafe_allow_html=True)
                worker_table = []
                total_busy = sum(e["busy"] for e in stats["per_worker"].values()) or 1.0
                for pid, entry in sorted(stats["per_worker"].items()):
                    share = entry["busy"] / total_busy
                    worker_table.append({
                        "Worker Process": f"PID {pid}",
                        "Chunks": entry["chunks"],
                        "Busy Time": f"{entry['busy']:.3f} s",
                        "Load Share": f"{share * 100:.1f}%"
                    })
                st.table(worker_table)
        else:
            st.info("Adjust the parameters in the top console and click 'Run Analysis' to execute the comparison.")

    with tab_architecture:
        st.markdown("<p style='font-size:0.95rem; font-weight:600; color:#f8fafc; margin-bottom:12px;'>PDC Methodology & Implementation</p>", unsafe_allow_html=True)
        st.markdown(
            """
            | PDC Principle | Module | Technical Implementation |
            | :--- | :--- | :--- |
            | **Partitioning (PCAM)** | `chunker.py` | Data decomposition dividing files into contiguous byte ranges at non-letter boundaries without word loss. |
            | **Agglomeration (PCAM)** | `chunk_size_bytes` | Agglomerates small token tasks into megabyte blocks to mitigate inter-process communication overhead. |
            | **Communication (PCAM)** | `parallel.py` | Compares zero-copy IPC (passing byte boundaries) against raw buffer copying (send mode). |
            | **Load Balancing** | `parallel.py` | Employs `imap_unordered(chunksize=1)` for dynamic task scheduling across worker nodes. |
            | **Map Phase & Combiner**| `map_chunk` | Workers execute local token counting and return aggregate frequency counters rather than full word streams. |
            | **Reduce Phase** | `parallel_count` | Master process merges partial frequency counters in place as worker tasks complete. |
            | **Synchronization** | `multiprocessing.Pool` | Barrier synchronization ensuring all tasks complete before executing final serial frequency ranking. |
            | **Amdahl's Law** | `metrics.py` | Formulates theoretical speedup limits based on Karp-Flatt estimated serial fraction ($e$). |
            """
        )


if __name__ == "__main__":
    main()
