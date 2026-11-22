"""Automated performance experiments for LexiCount.

Experiments
-----------
A  Strong scaling : fixed file (100 MB), workers = 1, 2, 4, ... cpu_count
B  Data scaling   : workers = cpu_count, file sizes = 1, 10, 50, 100, 500 MB
C  Agglomeration  : fixed file and workers, chunk sizes = 0.25, 1, 4, 16, 64 MB
D  Communication  : "offset" mode vs "send" mode

Every configuration runs one discarded warm-up run, then N measured runs
(default 5). Mean, median and standard deviation are reported, and every run
is checked against the sequential result.

Usage:
    python benchmark.py                 # all experiments, 5 runs each
    python benchmark.py --runs 3 --experiments A B
"""

import argparse
import csv
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from collections import Counter
from typing import Callable

from dataset_generator import generate_dataset
from metrics import efficiency, speedup
from parallel import parallel_count
from sequential import sequential_count

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
MB = 1024 * 1024
CPU_COUNT = os.cpu_count() or 1
BREAKDOWN_KEYS = ("pool_startup", "partition", "map_reduce", "pool_shutdown", "sort")

# A run function returns (counts, total_seconds, timings, num_chunks).
RunResult = tuple[Counter[str], float, dict[str, float], int]


# --- Machine information ----------------------------------------------------

def cpu_model() -> str:
    """Best-effort CPU model name (falls back to platform information)."""
    if os.path.isfile("/proc/cpuinfo"):  # Linux
        with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as file:
            for line in file:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    if sys.platform == "win32":  # Windows keeps the marketing name in the registry
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
        except OSError:
            pass
    if sys.platform == "darwin":  # macOS
        result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                capture_output=True, text=True, check=False)
        if result.stdout.strip():
            return result.stdout.strip()
    return platform.processor() or platform.machine() or "unknown"


def total_ram_gb() -> float | None:
    """Total physical memory in GB, or None if it cannot be determined."""
    try:
        if hasattr(os, "sysconf"):  # Linux / macOS
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
        import ctypes  # Windows only, standard library

        class MemoryStatus(ctypes.Structure):
            """Layout of the Windows MEMORYSTATUSEX structure."""
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        status = MemoryStatus()
        status.dwLength = ctypes.sizeof(MemoryStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        return status.ullTotalPhys / 1024**3
    except (ValueError, OSError, AttributeError):
        return None


def machine_info() -> dict:
    """Collect the hardware/software details needed to reproduce the results."""
    ram = total_ram_gb()
    return {
        "cpu_model": cpu_model(),
        "logical_cores": CPU_COUNT,
        "ram_gb": round(ram, 1) if ram else None,
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python": platform.python_version(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


# --- Measurement helpers ------------------------------------------------------

def run_sequential(path: str) -> RunResult:
    """One sequential run in the common RunResult format."""
    counts, timings = sequential_count(path)
    return counts, timings["total_time"], timings, 1


def make_parallel_runner(workers: int, chunk_mb: float, mode: str) -> Callable[[str], RunResult]:
    """Return a function that performs one parallel run with fixed settings."""
    def run_parallel(path: str) -> RunResult:
        counts, timings, stats = parallel_count(path, workers, int(chunk_mb * MB), mode)
        return counts, timings["total"], timings, stats["num_chunks"]
    return run_parallel


def repeat_runs(run: Callable[[str], RunResult], path: str, runs: int,
                reference: Counter[str]) -> dict:
    """Warm up once (discarded), then time `runs` runs and check each result."""
    run(path)  # WARM-UP: loads the file into the OS cache, imports, etc.
    times, breakdowns, all_correct, num_chunks = [], [], True, 0
    for _ in range(runs):
        counts, seconds, timings, num_chunks = run(path)
        times.append(seconds)
        breakdowns.append(timings)
        all_correct = all_correct and counts == reference
    row = {
        "runs": runs,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if runs > 1 else 0.0,
        "min": min(times),
        "correct": all_correct,
        "num_chunks": num_chunks,
        "times": times,
    }
    for key in BREAKDOWN_KEYS:  # average timing breakdown (parallel runs only)
        if key in breakdowns[0]:
            row[key] = statistics.mean(b[key] for b in breakdowns)
    return row


class Benchmark:
    """Runs experiments, caching one sequential baseline per file size."""

    def __init__(self, runs: int) -> None:
        """Store settings and create empty result containers."""
        self.runs = runs
        self.rows: list[dict] = []
        self.baselines: dict[float, dict] = {}
        self.references: dict[float, Counter[str]] = {}

    def baseline(self, size_mb: float) -> dict:
        """Return (measuring once if needed) the sequential row for a file size."""
        if size_mb not in self.baselines:
            path = generate_dataset(size_mb)
            print(f"  sequential baseline  {size_mb:g} MB ...", flush=True)
            self.references[size_mb] = sequential_count(path)[0]
            row = repeat_runs(run_sequential, path, self.runs, self.references[size_mb])
            row.update(experiment="baseline", file_mb=size_mb, implementation="sequential",
                       workers=1, chunk_mb=None, mode=None, speedup=1.0, efficiency=1.0)
            self.baselines[size_mb] = row
            self.rows.append(row)
        return self.baselines[size_mb]

    def measure(self, experiment: str, size_mb: float, workers: int,
                chunk_mb: float, mode: str = "offset") -> dict:
        """Measure one parallel configuration and record speedup/efficiency."""
        base = self.baseline(size_mb)
        print(f"  [{experiment}] {size_mb:g} MB | p={workers} | chunk={chunk_mb:g} MB | {mode} ...",
              flush=True)
        runner = make_parallel_runner(workers, chunk_mb, mode)
        row = repeat_runs(runner, generate_dataset(size_mb), self.runs, self.references[size_mb])
        s = speedup(base["mean"], row["mean"])
        row.update(experiment=experiment, file_mb=size_mb, implementation="parallel",
                   workers=workers, chunk_mb=chunk_mb, mode=mode,
                   speedup=s, efficiency=efficiency(s, workers))
        self.rows.append(row)
        return row


# --- Experiments --------------------------------------------------------------

def worker_counts(max_workers: int) -> list[int]:
    """1, 2, 4, 8, ... up to max_workers (max_workers itself always included)."""
    counts, p = [], 1
    while p < max_workers:
        counts.append(p)
        p *= 2
    return counts + [max_workers]


def experiment_a(bench: Benchmark, size_mb: float, chunk_mb: float) -> None:
    """Strong scaling: same file, increasing number of workers."""
    for workers in worker_counts(CPU_COUNT):
        bench.measure("A", size_mb, workers, chunk_mb)


def experiment_b(bench: Benchmark, sizes: list[float], chunk_mb: float) -> None:
    """Data scaling: all cores, increasing file size."""
    for size_mb in sizes:
        bench.measure("B", size_mb, CPU_COUNT, chunk_mb)


def experiment_c(bench: Benchmark, size_mb: float, chunk_sizes: list[float]) -> None:
    """Agglomeration: all cores, different chunk sizes."""
    for chunk_mb in chunk_sizes:
        bench.measure("C", size_mb, CPU_COUNT, chunk_mb)


def experiment_d(bench: Benchmark, size_mb: float, chunk_mb: float) -> None:
    """Communication: offset mode vs send mode for a few worker counts."""
    for workers in sorted({2, max(2, CPU_COUNT // 2), CPU_COUNT}):
        for mode in ("offset", "send"):
            bench.measure("D", size_mb, workers, chunk_mb, mode)


# --- Output ---------------------------------------------------------------------

def save_results(rows: list[dict], info: dict, settings: dict) -> tuple[str, str]:
    """Write benchmark_results.json (full) and benchmark_results.csv (flat)."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    json_path = os.path.join(RESULTS_DIR, "benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump({"machine": info, "settings": settings, "results": rows}, file, indent=2)

    csv_path = os.path.join(RESULTS_DIR, "benchmark_results.csv")
    columns = ["experiment", "implementation", "file_mb", "workers", "chunk_mb", "mode",
               "num_chunks", "runs", "mean", "median", "stdev", "min", "speedup",
               "efficiency", "correct", *BREAKDOWN_KEYS, "times"]
    with open(csv_path, "w", newline="", encoding="utf-8") as file:
        file.write("# machine: " + json.dumps(info) + "\n")
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            flat = dict(row, times=";".join(f"{t:.6f}" for t in row["times"]))
            writer.writerow(flat)
    return json_path, csv_path


def print_table(title: str, rows: list[dict], label: str, key: str) -> None:
    """Print one experiment as: <label> | Time (s) | Speedup | Efficiency."""
    if not rows:
        return
    print(f"\n{title}")
    print(f"{label:>14} | {'Time (s)':>9} | {'Std dev':>8} | {'Speedup':>7} | {'Efficiency':>10}")
    print("-" * 61)
    for row in rows:
        print(f"{str(row[key]):>14} | {row['mean']:>9.4f} | {row['stdev']:>8.4f} | "
              f"{row['speedup']:>6.2f}x | {row['efficiency']:>9.1%}")


def print_summary(rows: list[dict]) -> None:
    """Print a summary table for every experiment that was run."""
    def pick(experiment: str) -> list[dict]:
        return [r for r in rows if r["experiment"] == experiment]

    print_table("Experiment A - strong scaling", pick("A"), "Workers", "workers")
    print_table("Experiment B - data scaling (all cores)", pick("B"), "File (MB)", "file_mb")
    print_table("Experiment C - chunk size (all cores)", pick("C"), "Chunk (MB)", "chunk_mb")
    for row in pick("D"):
        row["label"] = f"p={row['workers']} {row['mode']}"
    print_table("Experiment D - communication mode", pick("D"), "Config", "label")
    baseline_rows = pick("baseline")
    print("\nSequential baselines: " + ", ".join(
        f"{r['file_mb']:g} MB = {r['mean']:.4f} s" for r in baseline_rows))
    print("All runs correct:", all(r["correct"] for r in rows))


def parse_args() -> argparse.Namespace:
    """Command-line options for the benchmark."""
    parser = argparse.ArgumentParser(description="Run LexiCount performance experiments.")
    parser.add_argument("--runs", type=int, default=5, help="measured runs per configuration")
    parser.add_argument("--experiments", nargs="+", default=["A", "B", "C", "D"],
                        choices=["A", "B", "C", "D"], help="which experiments to run")
    parser.add_argument("--file-size", type=float, default=100, help="file size (MB) for A, C, D")
    parser.add_argument("--sizes", nargs="+", type=float, default=[1, 10, 50, 100, 500],
                        help="file sizes (MB) for experiment B")
    parser.add_argument("--chunk-sizes", nargs="+", type=float, default=[0.25, 1, 4, 16, 64],
                        help="chunk sizes (MB) for experiment C")
    parser.add_argument("--chunk-size", type=float, default=4, help="chunk size (MB) for A, B, D")
    args = parser.parse_args()
    if args.runs < 1 or args.file_size <= 0 or args.chunk_size <= 0:
        parser.error("--runs, --file-size and --chunk-size must be positive")
    return args


def main() -> int:
    """Run the selected experiments, save results and print the summary."""
    args = parse_args()
    info = machine_info()
    print(f"Machine: {info['cpu_model']} | {info['logical_cores']} cores | "
          f"{info['ram_gb']} GB RAM | {info['os']} | Python {info['python']}")
    bench = Benchmark(args.runs)
    started = time.perf_counter()
    try:
        if "A" in args.experiments:
            experiment_a(bench, args.file_size, args.chunk_size)
        if "B" in args.experiments:
            experiment_b(bench, args.sizes, args.chunk_size)
        if "C" in args.experiments:
            experiment_c(bench, args.file_size, args.chunk_sizes)
        if "D" in args.experiments:
            experiment_d(bench, args.file_size, args.chunk_size)
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    json_path, csv_path = save_results(bench.rows, info, vars(args))
    print_summary(bench.rows)
    print(f"\nBenchmark finished in {time.perf_counter() - started:.1f} s")
    print(f"Saved: {json_path}\n       {csv_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
