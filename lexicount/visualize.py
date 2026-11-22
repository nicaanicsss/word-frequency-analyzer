"""Generate PNG charts (300 dpi) from results/benchmark_results.json.

Usage:
    python visualize.py
"""

import json
import math
import os
import sys

import matplotlib

matplotlib.use("Agg")  # draw to files only; no window needed
import matplotlib.pyplot as plt  # noqa: E402

from metrics import amdahl_speedup, karp_flatt  # noqa: E402

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
RESULTS_FILE = os.path.join(RESULTS_DIR, "benchmark_results.json")
BREAKDOWN = [("pool_startup", "Pool startup"), ("partition", "Partition"),
             ("map_reduce", "Map + Reduce"), ("pool_shutdown", "Pool shutdown"),
             ("sort", "Sort")]

plt.rcParams.update({"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12,
                     "legend.fontsize": 11, "figure.figsize": (9, 5.5)})


def load_results(path: str = RESULTS_FILE) -> dict:
    """Read the benchmark JSON file."""
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def rows_for(results: dict, experiment: str) -> list[dict]:
    """All result rows of one experiment, in the order they were measured."""
    return [row for row in results["results"] if row["experiment"] == experiment]


def baseline(results: dict, size_mb: float) -> dict:
    """The sequential baseline row for a given file size."""
    return next(row for row in rows_for(results, "baseline") if row["file_mb"] == size_mb)


def save(figure: plt.Figure, name: str) -> str:
    """Save a figure as a 300-dpi PNG in results/ and close it."""
    path = os.path.join(RESULTS_DIR, name)
    figure.tight_layout()
    figure.savefig(path, dpi=300)
    plt.close(figure)
    print(f"Saved {path}")
    return path


def plot_time_vs_workers(results: dict) -> None:
    """Experiment A: parallel time per worker count, sequential as a horizontal line."""
    rows = rows_for(results, "A")
    seq = baseline(results, rows[0]["file_mb"])
    figure, axis = plt.subplots()
    axis.errorbar([r["workers"] for r in rows], [r["mean"] for r in rows],
                  yerr=[r["stdev"] for r in rows], marker="o", capsize=4, label="Parallel (mean ± std)")
    axis.axhline(seq["mean"], color="red", linestyle="--", label=f"Sequential ({seq['mean']:.2f} s)")
    axis.set(title=f"Execution Time vs Workers ({rows[0]['file_mb']:g} MB file)",
             xlabel="Number of worker processes (p)", ylabel="Execution time (s)")
    axis.set_xticks([r["workers"] for r in rows])
    axis.set_ylim(bottom=0)
    axis.grid(alpha=0.3)
    axis.legend()
    save(figure, "execution_time_vs_workers.png")


def estimated_serial_fraction(rows: list[dict]) -> float:
    """Average Karp-Flatt serial fraction over runs with p > 1 (clamped to [0, 1))."""
    values = [karp_flatt(r["speedup"], r["workers"]) for r in rows if r["workers"] > 1]
    values = [v for v in values if v is not None]
    average = sum(values) / len(values) if values else 0.0
    return min(max(average, 0.0), 0.99)


def plot_speedup(results: dict) -> None:
    """Experiment A: actual speedup vs ideal linear vs Amdahl's Law."""
    rows = rows_for(results, "A")
    workers = [r["workers"] for r in rows]
    serial = estimated_serial_fraction(rows)
    curve_x = [1 + i * (workers[-1] - 1) / 100 for i in range(101)]
    figure, axis = plt.subplots()
    axis.plot(workers, [r["speedup"] for r in rows], marker="o", linewidth=2, label="Actual speedup")
    axis.plot(workers, workers, linestyle="--", color="gray", label="Ideal (linear) S = p")
    axis.plot(curve_x, [amdahl_speedup(serial, x) for x in curve_x], color="green",
              label=f"Amdahl's Law (e = {serial:.3f}, Karp-Flatt)")
    axis.set(title="Speedup vs Workers", xlabel="Number of worker processes (p)",
             ylabel="Speedup S = T_seq / T_par")
    axis.set_xticks(workers)
    axis.grid(alpha=0.3)
    axis.legend()
    save(figure, "speedup_vs_workers.png")


def plot_efficiency(results: dict) -> None:
    """Experiment A: efficiency E = S / p as a percentage."""
    rows = rows_for(results, "A")
    workers = [r["workers"] for r in rows]
    values = [100 * r["efficiency"] for r in rows]
    figure, axis = plt.subplots()
    bars = axis.bar([str(w) for w in workers], values, color="tab:blue", label="Measured efficiency")
    axis.bar_label(bars, fmt="%.0f%%")
    axis.axhline(100, color="gray", linestyle="--", label="Ideal (100%)")
    axis.set(title="Parallel Efficiency vs Workers", xlabel="Number of worker processes (p)",
             ylabel="Efficiency E = S / p (%)")
    axis.set_ylim(0, max(110, max(values) + 10))
    axis.legend()
    save(figure, "efficiency_vs_workers.png")


def crossover_size(sizes: list[float], seq: list[float], par: list[float]) -> float | None:
    """File size where parallel starts beating sequential (log-interpolated)."""
    for i in range(1, len(sizes)):
        if par[i - 1] >= seq[i - 1] and par[i] < seq[i]:
            before = math.log(par[i - 1] / seq[i - 1])
            after = math.log(par[i] / seq[i])
            fraction = before / (before - after)
            log_size = math.log(sizes[i - 1]) + fraction * math.log(sizes[i] / sizes[i - 1])
            return math.exp(log_size)
    return None


def plot_time_vs_size(results: dict) -> None:
    """Experiment B: sequential vs parallel time over file size, with crossover."""
    rows = rows_for(results, "B")
    sizes = [r["file_mb"] for r in rows]
    par = [r["mean"] for r in rows]
    seq = [baseline(results, s)["mean"] for s in sizes]
    figure, axis = plt.subplots()
    axis.plot(sizes, seq, marker="o", color="red", label="Sequential")
    axis.plot(sizes, par, marker="s", color="tab:blue", label=f"Parallel (p = {rows[0]['workers']})")
    crossover = crossover_size(sizes, seq, par)
    if crossover:
        axis.axvline(crossover, color="gray", linestyle=":",
                     label=f"Crossover ≈ {crossover:.1f} MB")
    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set(title="Execution Time vs File Size", xlabel="File size (MB, log scale)",
             ylabel="Execution time (s, log scale)")
    axis.grid(alpha=0.3, which="both")
    axis.legend()
    save(figure, "time_vs_file_size.png")


def plot_chunk_size(results: dict) -> None:
    """Experiment C: effect of chunk size (agglomeration) on parallel time."""
    rows = rows_for(results, "C")
    figure, axis = plt.subplots()
    labels = [f"{r['chunk_mb']:g} MB\n({r['num_chunks']} chunks)" for r in rows]
    bars = axis.bar(labels, [r["mean"] for r in rows], yerr=[r["stdev"] for r in rows],
                    capsize=4, color="tab:purple", label=f"Parallel (p = {rows[0]['workers']})")
    axis.bar_label(bars, fmt="%.2f s", padding=3)
    axis.axhline(baseline(results, rows[0]["file_mb"])["mean"], color="red", linestyle="--",
                 label="Sequential")
    axis.set(title=f"Effect of Chunk Size ({rows[0]['file_mb']:g} MB file)",
             xlabel="Chunk size (number of chunks)", ylabel="Execution time (s)")
    axis.legend()
    save(figure, "chunk_size_effect.png")


def plot_offset_vs_send(results: dict) -> None:
    """Experiment D: communication cost of sending offsets vs sending data."""
    rows = rows_for(results, "D")
    workers = sorted({r["workers"] for r in rows})
    width = 0.38
    figure, axis = plt.subplots()
    for shift, mode, color in ((-width / 2, "offset", "tab:green"), (width / 2, "send", "tab:orange")):
        times = [next(r["mean"] for r in rows if r["workers"] == w and r["mode"] == mode)
                 for w in workers]
        bars = axis.bar([i + shift for i in range(len(workers))], times, width, color=color,
                        label=f"{mode} mode")
        axis.bar_label(bars, fmt="%.2f", padding=2)
    axis.set_xticks(range(len(workers)), [f"p = {w}" for w in workers])
    axis.set(title="Communication Overhead: Offset vs Send Mode",
             xlabel="Number of worker processes", ylabel="Execution time (s)")
    axis.legend()
    save(figure, "offset_vs_send.png")


def plot_breakdown(results: dict) -> None:
    """Experiment A: stacked bars of where parallel time is spent."""
    rows = rows_for(results, "A")
    labels = [str(r["workers"]) for r in rows]
    bottom = [0.0] * len(rows)
    figure, axis = plt.subplots()
    for key, name in BREAKDOWN:
        values = [r.get(key, 0.0) for r in rows]
        axis.bar(labels, values, bottom=bottom, label=name)
        bottom = [b + v for b, v in zip(bottom, values)]
    axis.set(title="Parallel Time Breakdown vs Workers", xlabel="Number of worker processes (p)",
             ylabel="Mean time (s)")
    axis.legend()
    save(figure, "time_breakdown_stacked.png")


def main() -> int:
    """Create every chart whose experiment data is available."""
    if not os.path.isfile(RESULTS_FILE):
        print(f"ERROR: {RESULTS_FILE} not found. Run 'python benchmark.py' first.", file=sys.stderr)
        return 1
    results = load_results()
    charts = [("A", plot_time_vs_workers), ("A", plot_speedup), ("A", plot_efficiency),
              ("B", plot_time_vs_size), ("C", plot_chunk_size), ("D", plot_offset_vs_send),
              ("A", plot_breakdown)]
    for experiment, plot in charts:
        if rows_for(results, experiment):
            plot(results)
        else:
            print(f"Skipping {plot.__name__}: no data for experiment {experiment}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
