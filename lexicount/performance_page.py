"""The "Performance" page: presents the saved results of benchmark.py.

Nothing is measured on this page. Running `python benchmark.py` (about 8 minutes,
with other apps closed) writes results/benchmark_results.json; this page only
reads that file and shows it as four questions, each with a chart, a table and
one plain sentence:

    A  Does adding workers make it faster?          (strong scaling, Amdahl's law)
    B  When does parallel start paying off?          (data scaling)
    C  How big should each chunk be?                 (agglomeration)
    D  Does sending data between processes cost time? (communication)

Set LEXICOUNT_BENCHMARK_FILE to show a results file from somewhere else
(for example one a group member produced on another laptop).
"""

from __future__ import annotations

import html
import json
import math
import os
from datetime import datetime

import streamlit as st

from metrics import karp_flatt

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_RESULTS_FILE = os.path.join(PROJECT_DIR, "results", "benchmark_results.json")

INK, BROWN, TAN, LINE, MUTED = "#1d1d1a", "#7a5c43", "#c4ab8c", "#e6dfd4", "#6f6a62"
SAME_RANGE = 0.05  # differences under 5% are called "about the same"

PERF_CSS = """
<style>
.pf-head { padding-top:28px; margin-bottom:18px; }
.pf-title { font-family:'Playfair Display',serif; font-weight:400; font-size:3.1rem; letter-spacing:-0.02em;
  line-height:1.1; margin:0 0 8px; color:var(--ink); }
.pf-lead { font-size:0.9rem; line-height:1.55; color:var(--muted); max-width:760px; margin:0; }
.pf-machine { display:flex; flex-wrap:wrap; gap:8px; margin:18px 0 10px; }
.pf-machine span { background:rgba(255,255,255,.74); border:1px solid rgba(255,255,255,.9); border-radius:999px;
  padding:5px 12px; font-size:0.78rem; color:var(--ink); }
.pf-ok { display:inline-flex; align-items:center; gap:10px; font-size:0.84rem; color:var(--ink); margin:2px 0 6px; }
.pf-ok i { width:20px; height:20px; border-radius:50%; background:var(--ink); color:#fff; font-style:normal;
  display:inline-flex; align-items:center; justify-content:center; font-size:0.7rem; }
.pf-ok.bad i { background:#9b2c2c; }
.pf-card { background:#fff; border-radius:18px; padding:22px 24px; margin-top:14px; container-type:inline-size; }
.pf-q { font-family:'Playfair Display',serif; font-weight:400; font-size:1.5rem; margin:0; color:var(--ink); }
.pf-ref { font-size:0.78rem; color:var(--muted); margin:4px 0 16px; }
.pf-take { font-size:0.92rem; line-height:1.6; color:var(--ink); background:var(--cream); border-radius:12px;
  padding:12px 16px; margin:0 0 16px; }
.pf-body { display:grid; grid-template-columns:minmax(0,1.35fr) minmax(0,1fr); gap:26px; align-items:start; }
@container (max-width: 760px) { .pf-body { grid-template-columns:1fr; } }
.pf-chart svg { width:100%; height:auto; display:block; }
.pf-legend { display:flex; flex-wrap:wrap; gap:6px 18px; font-size:0.78rem; color:var(--muted); margin-top:6px; }
.pf-legend i { display:inline-block; width:14px; height:3px; border-radius:2px; margin-right:7px; vertical-align:middle; }
.pf-legend i.dash { background:repeating-linear-gradient(90deg, currentColor 0 4px, transparent 4px 7px) !important; }
.pf-tbl { width:100%; border-collapse:collapse; font-size:0.8rem; border:none !important; }
.pf-tbl tr, .pf-tbl th, .pf-tbl td { border:none !important; background:transparent !important; }
.pf-tbl th { text-align:right; font-weight:500; color:var(--muted); font-size:0.74rem; padding:0 0 8px 12px;
  border-bottom:1px solid var(--line) !important; white-space:nowrap; }
.pf-tbl th:first-child, .pf-tbl td:first-child { text-align:left; padding-left:0; }
.pf-tbl td { text-align:right; padding:8px 0 8px 12px; border-bottom:1px solid var(--line) !important; white-space:nowrap;
  font-family:'JetBrains Mono',monospace; font-size:0.76rem; color:var(--ink); }
.pf-tbl td small { color:#9a948a; font-size:0.68rem; }
.pf-tbl tr.best td { font-weight:700; }
.pf-none { font-size:0.86rem; color:var(--muted); }
.pf-empty { background:#fff; border-radius:18px; padding:28px 30px; margin-top:8px; max-width:820px; }
.pf-empty-title { font-family:'Playfair Display',serif; font-weight:400; font-size:1.6rem; margin:0 0 10px; color:var(--ink); }
.pf-empty p, .pf-empty li { font-size:0.9rem; line-height:1.6; color:var(--ink); }
.pf-empty code { background:var(--sand); border-radius:6px; padding:2px 8px; font-size:0.85rem; }
.pf-foot { font-size:0.74rem; color:#9a948a; margin-top:16px; }
</style>
"""


# ---------------------------------------------------------------- loading

def results_file() -> str:
    """Where the results are read from (benchmark.py writes the default location)."""
    return os.environ.get("LEXICOUNT_BENCHMARK_FILE", DEFAULT_RESULTS_FILE)


def load_results() -> dict | None:
    """The saved benchmark results, or None if benchmark.py has not been run yet."""
    try:
        with open(results_file(), encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as error:
        st.error(f"Could not read {results_file()}: {error}")
        return None


def rows_for(data: dict, experiment: str) -> list[dict]:
    """All result rows of one experiment (A, B, C or D)."""
    return [row for row in data["results"] if row["experiment"] == experiment]


def baseline_time(data: dict, size_mb: float) -> float | None:
    """Mean sequential time for one file size."""
    for row in data["results"]:
        if row["experiment"] == "baseline" and row["file_mb"] == size_mb:
            return row["mean"]
    return None


# ---------------------------------------------------------------- small helpers

def show(markup: str) -> None:
    """Render raw HTML (lines stripped so Markdown never treats them as code)."""
    st.markdown("".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def size_label(mb: float) -> str:
    return f"{mb:g} MB"


def seconds(row: dict) -> str:
    """Mean time with its run-to-run spread, e.g. '1.21 s ± 0.02'."""
    spread = f" <small>± {row['stdev']:.2f}</small>" if row.get("runs", 1) > 1 else ""
    return f"{row['mean']:.2f} s{spread}"


def compare_words(a: float, b: float) -> str:
    """How b compares with a: '23% slower', '5% faster' or 'about the same'."""
    change = b / a - 1 if a else 0.0
    if abs(change) < SAME_RANGE:
        return "about the same"
    return f"{abs(change):.0%} {'slower' if change > 0 else 'faster'}"


def table(headers: list[str], rows: list[list[str]], best: int | None = None) -> str:
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(f"<tr class='{'best' if i == best else ''}'>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
                   for i, row in enumerate(rows))
    return f"<table class='pf-tbl'><tr>{head}</tr>{body}</table>"


def legend(items: list[tuple[str, str, bool]]) -> str:
    """Legend entries as (label, colour, dashed)."""
    return "<div class='pf-legend'>" + "".join(
        f"<span style='color:{colour}'><i class='{'dash' if dashed else ''}' style='background:{colour}'></i>"
        f"<span style='color:{MUTED}'>{label}</span></span>" for label, colour, dashed in items) + "</div>"


# ---------------------------------------------------------------- charts (plain SVG in the page's colours)

W, H = 640, 270
LEFT, RIGHT, TOP, BOTTOM = 66, 16, 20, 46


def nice_top(value: float) -> float:
    """Round an axis maximum up to 1, 2, 2.5 or 5 times a power of ten (e.g. 3.7 -> 5, 0.36 -> 0.5)."""
    if value <= 0:
        return 1.0
    power = 10 ** math.floor(math.log10(value))
    for step in (1, 2, 2.5, 5, 10):
        if value <= step * power:
            return step * power
    return 10 * power


def frame(x_labels: list[str], top: float, y_format, x_title: str, y_title: str) -> tuple[str, callable, callable]:
    """Axes, grid lines and labels. Returns (svg, x position of category i, y position of a value)."""
    plot_w, plot_h = W - LEFT - RIGHT, H - TOP - BOTTOM
    n = len(x_labels)

    def x(i: int) -> float:
        return LEFT + (i + 0.5) * plot_w / n

    def y(v: float) -> float:
        return TOP + plot_h * (1 - v / top)

    parts = []
    for k in range(6):  # gridlines at fifths of a "nice" maximum give round labels
        value = round(top * k / 5, 6)
        parts.append(f"<line x1='{LEFT}' x2='{W - RIGHT}' y1='{y(value):.1f}' y2='{y(value):.1f}' "
                     f"stroke='{LINE}' stroke-width='1'/>"
                     f"<text x='{LEFT - 8}' y='{y(value) + 4:.1f}' text-anchor='end' font-size='11' "
                     f"fill='{MUTED}'>{y_format(value)}</text>")
    for i, label_text in enumerate(x_labels):
        parts.append(f"<text x='{x(i):.1f}' y='{H - BOTTOM + 18}' text-anchor='middle' font-size='11' "
                     f"fill='{MUTED}'>{html.escape(label_text)}</text>")
    parts.append(f"<text x='{LEFT + plot_w / 2:.1f}' y='{H - 6}' text-anchor='middle' font-size='11' "
                 f"fill='{MUTED}'>{html.escape(x_title)}</text>")
    parts.append(f"<text transform='translate(12 {TOP + plot_h / 2:.1f}) rotate(-90)' text-anchor='middle' "
                 f"font-size='11' fill='{MUTED}'>{html.escape(y_title)}</text>")
    return "".join(parts), x, y


def svg(content: str, title: str) -> str:
    return (f"<div class='pf-chart'><svg viewBox='0 0 {W} {H}' role='img' aria-label='{html.escape(title)}' "
            f"font-family='JetBrains Mono, monospace'>{content}</svg></div>")


def line_chart(x_labels: list[str], series: list[dict], y_format, x_title: str, y_title: str,
               title: str, reference: float | None = None) -> str:
    """Lines through categories. Each series: label, colour, values, optional dashed / value labels."""
    top = nice_top(max(max(s["values"]) for s in series) * 1.12)
    body, x, y = frame(x_labels, top, y_format, x_title, y_title)
    if reference is not None:  # a horizontal guide, e.g. "same speed as sequential" at 1x
        body += (f"<line x1='{LEFT}' x2='{W - RIGHT}' y1='{y(reference):.1f}' y2='{y(reference):.1f}' "
                 f"stroke='{BROWN}' stroke-width='1.2' stroke-dasharray='5 4'/>")
    for s in series:
        points = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(s["values"]))
        dash = " stroke-dasharray='6 5'" if s.get("dashed") else ""
        body += (f"<polyline points='{points}' fill='none' stroke='{s['colour']}' stroke-width='2.2' "
                 f"stroke-linejoin='round'{dash}/>")
        if not s.get("dashed"):
            for i, v in enumerate(s["values"]):
                body += f"<circle cx='{x(i):.1f}' cy='{y(v):.1f}' r='4' fill='#fff' stroke='{s['colour']}' stroke-width='2'/>"
                if s.get("value_format"):
                    body += (f"<text x='{x(i):.1f}' y='{y(v) - 10:.1f}' text-anchor='middle' font-size='11' "
                             f"font-weight='700' fill='{s['colour']}'>{s['value_format'](v)}</text>")
    return svg(body, title)


def bar_chart(x_labels: list[str], series: list[dict], y_format, x_title: str, y_title: str, title: str) -> str:
    """Bars per category, side by side when there is more than one series.
    Each series: label, values, colours (one colour per bar), value_format."""
    top = nice_top(max(max(s["values"]) for s in series) * 1.15)
    body, x, y = frame(x_labels, top, y_format, x_title, y_title)
    slot = (W - LEFT - RIGHT) / len(x_labels)
    bar_w = min(46, slot * 0.7 / len(series))
    for k, s in enumerate(series):
        for i, v in enumerate(s["values"]):
            left = x(i) - bar_w * len(series) / 2 + k * bar_w + 1
            body += (f"<rect x='{left:.1f}' y='{y(v):.1f}' width='{bar_w - 2:.1f}' height='{y(0) - y(v):.1f}' "
                     f"rx='4' fill='{s['colours'][i]}'/>"
                     f"<text x='{left + (bar_w - 2) / 2:.1f}' y='{y(v) - 6:.1f}' text-anchor='middle' "
                     f"font-size='10.5' fill='{INK}'>{s['value_format'](v)}</text>")
    return svg(body, title)


# ---------------------------------------------------------------- the four questions

def card(question: str, reference: str, takeaway: str, chart: str, side: str) -> str:
    return (f"<div class='pf-card'><div class='pf-q'>{question}</div><div class='pf-ref'>{reference}</div>"
            f"<div class='pf-take'>{takeaway}</div>"
            f"<div class='pf-body'><div>{chart}</div><div>{side}</div></div></div>")


def not_measured(question: str, reference: str, experiment: str) -> str:
    return (f"<div class='pf-card'><div class='pf-q'>{question}</div><div class='pf-ref'>{reference}</div>"
            f"<div class='pf-none'>Not measured in these results (experiment {experiment} was skipped).</div></div>")


def workers_card(data: dict) -> str:
    """A: same file, 1, 2, 4, ... workers."""
    question, ref = "Does adding workers make it faster?", "Objective 7 · strong scaling · Amdahl's law"
    rows = sorted(rows_for(data, "A"), key=lambda r: r["workers"])
    if not rows:
        return not_measured(question, ref, "A")
    workers = [r["workers"] for r in rows]
    chart = line_chart(
        [str(p) for p in workers],
        [{"label": "ideal", "colour": TAN, "values": [float(p) for p in workers], "dashed": True},
         {"label": "measured", "colour": INK, "values": [r["speedup"] for r in rows],
          "value_format": lambda v: f"{v:.1f}×"}],
        lambda v: f"{v:g}×", "number of workers", "speedup", "Speedup by number of workers")
    chart += legend([("measured speedup", INK, False), ("ideal (twice the workers, twice as fast)", TAN, True)])

    last = rows[-1]
    take = (f"On the {size_label(last['file_mb'])} file, <b>{last['workers']} workers were "
            f"{last['speedup']:.2f}× faster</b> than one, using {last['efficiency']:.0%} of the ideal.")
    if len(rows) > 2 and rows[-1]["efficiency"] < rows[1]["efficiency"]:
        take += " Each extra worker helps a little less than the one before."
    serial = karp_flatt(last["speedup"], last["workers"])
    if serial is not None and 0 < serial < 1:
        take += (f" About {serial:.0%} of the work still behaves as if it can't be split, which would cap the "
                 f"speedup near {1 / serial:.0f}× however many workers are added (Amdahl's law).")
    side = table(["Workers", "Time", "Speedup", "Efficiency"],
                 [[str(r["workers"]), seconds(r), f"{r['speedup']:.2f}×", f"{r['efficiency']:.0%}"] for r in rows])
    return card(question, ref, take, chart, side)


def sizes_card(data: dict) -> str:
    """B: all cores, growing file sizes."""
    question, ref = "When does parallel start paying off?", "Objective 7 · data scaling"
    rows = sorted(rows_for(data, "B"), key=lambda r: r["file_mb"])
    if not rows:
        return not_measured(question, ref, "B")
    chart = line_chart(
        [size_label(r["file_mb"]) for r in rows],
        [{"label": "speedup", "colour": INK, "values": [r["speedup"] for r in rows],
          "value_format": lambda v: f"{v:.1f}×"}],
        lambda v: f"{v:g}×", "file size", "speedup", "Speedup by file size", reference=1.0)
    chart += legend([("speedup", INK, False), ("1× = same speed as sequential", BROWN, True)])

    first_win = next((r for r in rows if r["speedup"] > 1), None)
    p = rows[0]["workers"]
    if first_win is None:
        take = f"With {p} workers, parallel was <b>slower at every file size tested</b>."
    elif first_win is rows[0]:
        take = (f"With {p} workers, parallel was <b>already faster at {size_label(first_win['file_mb'])}</b>, "
                f"the smallest size tested.")
    else:
        take = (f"With {p} workers, parallel <b>starts paying off at {size_label(first_win['file_mb'])}</b>. "
                f"On smaller files, starting the worker processes costs more time than the counting itself.")
    take += f" At {size_label(rows[-1]['file_mb'])} it was {rows[-1]['speedup']:.2f}× faster."
    side = table(["File", "Sequential", "Parallel", "Speedup"],
                 [[size_label(r["file_mb"]), f"{baseline_time(data, r['file_mb']) or 0:.2f} s", seconds(r),
                   f"{r['speedup']:.2f}×"] for r in rows])
    return card(question, ref, take, chart, side)


def chunks_card(data: dict) -> str:
    """C: same file and workers, different chunk sizes."""
    question, ref = "How big should each chunk be?", "Objective 8 · workload distribution · agglomeration"
    rows = sorted(rows_for(data, "C"), key=lambda r: r["chunk_mb"])
    if not rows:
        return not_measured(question, ref, "C")
    best = min(range(len(rows)), key=lambda i: rows[i]["mean"])
    worst = max(range(len(rows)), key=lambda i: rows[i]["mean"])
    chart = bar_chart(
        [size_label(r["chunk_mb"]) for r in rows],
        [{"label": "time", "values": [r["mean"] for r in rows],
          "colours": [INK if i == best else TAN for i in range(len(rows))],
          "value_format": lambda v: f"{v:.2f}"}],
        lambda v: f"{v:g} s", "chunk size", "parallel time", "Parallel time by chunk size")
    chart += legend([("fastest", INK, False), ("other sizes", TAN, False)])

    b, w = rows[best], rows[worst]
    take = (f"<b>{size_label(b['chunk_mb'])} chunks were fastest</b> ({b['mean']:.2f} s, {b['num_chunks']} chunks); "
            f"{size_label(w['chunk_mb'])} was slowest ({w['mean']:.2f} s, {w['num_chunks']} chunks). Very small chunks "
            f"mean many hand-offs between processes; very large ones leave some workers with nothing to do at the end.")
    side = table(["Chunk size", "Chunks", "Time", "Speedup"],
                 [[size_label(r["chunk_mb"]), str(r["num_chunks"]), seconds(r), f"{r['speedup']:.2f}×"] for r in rows],
                 best=best)
    return card(question, ref, take, chart, side)


def communication_card(data: dict) -> str:
    """D: offset mode (workers read their own part) vs send mode (master sends the data)."""
    question, ref = "Does sending data between processes cost time?", "Objective 8 · communication overhead"
    rows = rows_for(data, "D")
    workers = sorted({r["workers"] for r in rows})
    pairs = [(next((r for r in rows if r["workers"] == p and r["mode"] == "offset"), None),
              next((r for r in rows if r["workers"] == p and r["mode"] == "send"), None)) for p in workers]
    pairs = [(p, o, s) for p, (o, s) in zip(workers, pairs) if o and s]
    if not pairs:
        return not_measured(question, ref, "D")
    chart = bar_chart(
        [f"{p} workers" for p, _, _ in pairs],
        [{"label": "Offset", "values": [o["mean"] for _, o, _ in pairs], "colours": [INK] * len(pairs),
          "value_format": lambda v: f"{v:.2f}"},
         {"label": "Send", "values": [s["mean"] for _, _, s in pairs], "colours": [TAN] * len(pairs),
          "value_format": lambda v: f"{v:.2f}"}],
        lambda v: f"{v:g} s", "workers", "parallel time", "Offset versus Send by number of workers")
    chart += legend([("Offset: each worker reads its own part of the file", INK, False),
                     ("Send: the main process sends each chunk's data", TAN, False)])

    average = sum(s["mean"] / o["mean"] for _, o, s in pairs) / len(pairs)
    verdict = compare_words(1.0, average)
    if verdict == "about the same":
        take = "<b>Sending the data made almost no difference</b> here (under 5% on average)."
    else:
        take = (f"Having the main process send each chunk's data (Send) was <b>{verdict} on average</b> than "
                f"letting each worker read its own part of the file (Offset), because the data has to be "
                f"copied between processes.")
    side = table(["Workers", "Offset", "Send", "Send vs Offset"],
                 [[str(p), seconds(o), seconds(s), compare_words(o["mean"], s["mean"])] for p, o, s in pairs])
    return card(question, ref, take, chart, side)


# ---------------------------------------------------------------- page

def empty_state() -> str:
    return (f"<div class='pf-empty'><div class='pf-empty-title'>No benchmark results yet</div>"
            f"<p>This page shows the results of <code>benchmark.py</code>, which runs the analyzer many times "
            f"with different settings and saves the averages. To create them, close other apps, then run this "
            f"in the <code>lexicount</code> folder (about 8 minutes) and refresh this page:</p>"
            f"<p><code>python benchmark.py</code></p>"
            f"<p>It answers four questions:</p><ul>"
            f"<li>Does adding workers make it faster?</li><li>When does parallel start paying off?</li>"
            f"<li>How big should each chunk be?</li><li>Does sending data between processes cost time?</li></ul>"
            f"<p class='pf-foot'>Looking for: {html.escape(os.path.relpath(results_file(), PROJECT_DIR))}</p></div>")


def os_name(text: str) -> str:
    """'Darwin 24.1.0 (...)' -> 'macOS' (Darwin is the macOS kernel); others keep their name and version."""
    name = text.split(" (")[0]
    return "macOS" if name.startswith("Darwin") else name


def header(data: dict | None) -> str:
    lead = ("Results of <code>benchmark.py</code>: every setting was run several times and the numbers below are "
            "averages, so they are steadier than a single run in the Analyzer.")
    if data is None:
        return f"<div class='pf-head'><div class='pf-title'>Performance</div><p class='pf-lead'>{lead}</p></div>"
    machine, settings = data.get("machine", {}), data.get("settings", {})
    try:
        measured = datetime.strptime(machine.get("timestamp", ""), "%Y-%m-%d %H:%M:%S").strftime("%d %b %Y, %H:%M")
    except ValueError:
        measured = machine.get("timestamp", "unknown date")
    chips = [machine.get("cpu_model"), f"{machine.get('logical_cores')} cores",
             f"{machine.get('ram_gb')} GB RAM" if machine.get("ram_gb") else None,
             os_name(machine.get("os") or ""), f"Python {machine.get('python')}",
             f"measured {measured}", f"{settings.get('runs', '?')} run{'' if settings.get('runs') == 1 else 's'} per setting"]
    chip_html = "".join(f"<span>{html.escape(str(c))}</span>" for c in chips if c)
    bad = [r for r in data["results"] if not r.get("correct", True)]
    check = ("<div class='pf-ok'><i>✓</i>Every run gave exactly the same word counts as the sequential version.</div>"
             if not bad else f"<div class='pf-ok bad'><i>✕</i>{len(bad)} result rows did not match the sequential "
             f"counts. Check the CSV before using these numbers.</div>")
    return (f"<div class='pf-head'><div class='pf-title'>Performance</div><p class='pf-lead'>{lead}</p>"
            f"<div class='pf-machine'>{chip_html}</div>{check}</div>")


def performance_page() -> None:
    """Show the saved benchmark results, or how to create them."""
    data = load_results()
    show(PERF_CSS + header(data))
    if data is None:
        show(empty_state())
        return
    show(workers_card(data))
    show(sizes_card(data))
    show(chunks_card(data))
    show(communication_card(data))
    show(f"<div class='pf-foot'>Source: {html.escape(os.path.relpath(results_file(), PROJECT_DIR))} · "
         f"times are the mean of the measured runs (± is the standard deviation). The full numbers, including "
         f"every single run, are in benchmark_results.csv.</div>")
