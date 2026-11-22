"""LexiCount command-line entry point.

Runs the sequential baseline and the parallel MapReduce version on the same
file, checks that both give identical results, and prints a performance report
(speedup, efficiency, Karp-Flatt serial fraction, Amdahl's Law prediction).

Examples:
    python main.py --file data/dataset_100MB.txt --workers 4
    python main.py --generate 100
"""

import argparse
import csv
import os
import sys
from collections import Counter

from chunker import DEFAULT_CHUNK_SIZE_MB, compute_chunks
from dataset_generator import generate_dataset
from metrics import amdahl_speedup, efficiency, karp_flatt, speedup
from parallel import MODES, parallel_count
from sequential import sequential_count

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(PROJECT_DIR, "results")
MB = 1024 * 1024
WIDTH = 50


def positive_int(text: str) -> int:
    """argparse type: an integer >= 1."""
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be an integer >= 1")
    return value


def positive_float(text: str) -> float:
    """argparse type: a number > 0."""
    value = float(text)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be a number > 0")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Define and parse the command-line options."""
    parser = argparse.ArgumentParser(description="LexiCount: Parallel Word Frequency Analyzer")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="text file to analyze")
    source.add_argument("--generate", type=positive_float, metavar="SIZE_MB",
                        help="generate data/dataset_<SIZE>MB.txt first, then analyze it")
    parser.add_argument("--workers", type=positive_int, default=os.cpu_count() or 1,
                        help="number of worker processes (default: CPU cores)")
    parser.add_argument("--chunk-size", type=positive_float, default=DEFAULT_CHUNK_SIZE_MB,
                        help=f"chunk size in MB (default: {DEFAULT_CHUNK_SIZE_MB})")
    parser.add_argument("--top", type=positive_int, default=10,
                        help="how many top words to show (default: 10)")
    parser.add_argument("--mode", choices=MODES, default="offset",
                        help="offset: send byte ranges (default); send: send chunk data")
    return parser.parse_args(argv)


def print_title(text: str) -> None:
    """Print a section title preceded by a blank line."""
    print(f"\n{text}")
    print("-" * WIDTH)


def print_header(path: str, workers: int, chunk_mb: float, num_chunks: int) -> None:
    """Print the banner and the run configuration."""
    print("=" * WIDTH)
    print("   LexiCount: Parallel Word Frequency Analyzer")
    print("=" * WIDTH)
    print(f"Input file      : {path}")
    print(f"File size       : {os.path.getsize(path) / MB:.1f} MB")
    print(f"CPU cores       : {os.cpu_count()}")
    print(f"Workers         : {workers}")
    print(f"Chunk size      : {chunk_mb:g} MB   | Chunks created: {num_chunks}")


def print_summary_lines(counts: Counter[str], seconds: float) -> None:
    """Print total words, unique words and execution time."""
    print(f"Total words     : {counts.total():,}")
    print(f"Unique words    : {len(counts):,}")
    print(f"Execution time  : {seconds:.4f} s")


def print_top_table(counts: Counter[str], top: int) -> None:
    """Print the top-N words as an aligned table."""
    total_words = counts.total() or 1  # avoid dividing by zero on empty files
    print(f"\n{'Rank':>4} | {'Word':<15} | {'Count':>12} | {'% of total':>10}")
    print(f"{'-' * 4}-+-{'-' * 15}-+-{'-' * 12}-+-{'-' * 10}")
    for rank, (word, count) in enumerate(counts.most_common(top), start=1):
        print(f"{rank:>4} | {word:<15} | {count:>12,} | {count / total_words:>9.2%}")


def print_breakdown(timings: dict[str, float]) -> None:
    """Print where the parallel run spent its time."""
    print("\nTiming breakdown:")
    print(f"  Pool startup  : {timings['pool_startup']:.4f} s")
    print(f"  Partition     : {timings['partition']:.4f} s")
    print(f"  Map + Reduce  : {timings['map_reduce']:.4f} s")
    print(f"  Pool shutdown : {timings['pool_shutdown']:.4f} s")
    print(f"  Sort          : {timings['sort']:.4f} s")


def print_load_distribution(per_worker: dict[int, dict[str, float]]) -> None:
    """LOAD BALANCING: show how many chunks and how much busy time each worker had."""
    total_busy = sum(entry["busy"] for entry in per_worker.values()) or 1.0
    print("\nLoad distribution:")
    print(f"  {'Worker PID':>10} | {'Chunks':>6} | {'Busy (s)':>9} | {'Share':>6}")
    for pid, entry in sorted(per_worker.items()):
        share = entry["busy"] / total_busy
        print(f"  {pid:>10} | {entry['chunks']:>6} | {entry['busy']:>9.4f} | {share:>6.1%}")


def find_differences(expected: Counter[str], actual: Counter[str], limit: int = 10) -> list[str]:
    """Return up to `limit` words whose counts differ between two Counters."""
    differences = []
    for word in sorted(set(expected) | set(actual)):
        if expected[word] != actual[word]:
            differences.append(f"{word!r}: sequential={expected[word]} parallel={actual[word]}")
            if len(differences) == limit:
                break
    return differences


def print_correctness(seq_counts: Counter[str], par_counts: Counter[str]) -> bool:
    """Compare the FULL Counters (every word, not only the top N)."""
    print_title("[3] CORRECTNESS CHECK")
    if seq_counts == par_counts:
        print(f"MATCH ✔  ({len(seq_counts):,} unique words compared, all counts identical)")
        return True
    print("MISMATCH ✘  First differing words:")
    for line in find_differences(seq_counts, par_counts):
        print(f"  {line}")
    return False


def interpret(s: float, e: float, p: int, serial_fraction: float | None) -> str:
    """Build a plain-English paragraph explaining the measured numbers."""
    if s >= 1:
        text = f"The parallel version was {s:.2f}x faster than the sequential version using {p} workers. "
    else:
        text = (f"The parallel version was SLOWER ({s:.2f}x) than the sequential version: the fixed "
                f"cost of starting {p} processes and merging results outweighed the small amount "
                "of work, so parallelism does not pay off for this input size. ")
    if e < 1:
        text += (f"Efficiency was {e:.0%}, below the ideal 100% because of process start-up, "
                 "partitioning, inter-process communication and the serial merge/sort done by "
                 "the master, as predicted by Amdahl's Law. ")
    else:
        text += (f"Efficiency was {e:.0%} (superlinear), usually caused by better cache use when "
                 "each worker handles a small chunk. ")
    if serial_fraction is not None and serial_fraction > 0:
        text += (f"The Karp-Flatt metric estimates that about {serial_fraction:.1%} of the work "
                 f"behaves serially, which caps the speedup at about {1 / serial_fraction:.1f}x "
                 "no matter how many workers are added.")
    return text


def print_amdahl_predictions(serial_fraction: float, p: int) -> None:
    """Amdahl's Law: theoretical speedup for several worker counts using the measured e.

    At p itself the prediction equals the measured speedup (that is how e was
    computed), so the useful information is what happens with MORE workers.
    """
    cores = os.cpu_count() or 1
    print(f"Amdahl theoretical speedup with e = {serial_fraction:.4f}:")
    for workers in sorted({2, p, cores, 2 * cores}):
        print(f"  p = {workers:<3}: {amdahl_speedup(serial_fraction, workers):.2f}x")
    print(f"  p -> inf : {1 / serial_fraction:.2f}x  (upper limit = 1 / e)")


def print_performance(t_seq: float, t_par: float, p: int) -> None:
    """Print speedup, efficiency, Karp-Flatt, Amdahl and an interpretation."""
    print_title("[4] PERFORMANCE SUMMARY")
    s = speedup(t_seq, t_par)
    e = efficiency(s, p)
    serial_fraction = karp_flatt(s, p)
    print(f"Sequential time : {t_seq:.4f} s")
    print(f"Parallel time   : {t_par:.4f} s")
    print(f"Speedup     S = T_seq / T_par = {s:.2f}x")
    print(f"Efficiency  E = S / p         = {e:.1%}")
    if serial_fraction is None:
        print("Karp-Flatt  e                 = n/a (needs p > 1)")
    else:
        print(f"Karp-Flatt  e = (1/S - 1/p) / (1 - 1/p) = {serial_fraction:.4f}")
        if 0 < serial_fraction < 1:
            print_amdahl_predictions(serial_fraction, p)
    print("\nInterpretation:")
    print(interpret(s, e, p, serial_fraction))


def save_top_words(counts: Counter[str], top: int) -> str:
    """Write the top-N words to results/top_words.csv and return the path."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, "top_words.csv")
    total_words = counts.total() or 1
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["rank", "word", "count", "percent_of_total"])
        for rank, (word, count) in enumerate(counts.most_common(top), start=1):
            writer.writerow([rank, word, count, round(100 * count / total_words, 4)])
    return path


def run(args: argparse.Namespace) -> int:
    """Execute the full analysis; return a process exit code."""
    path = generate_dataset(args.generate) if args.generate else args.file
    if not os.path.isfile(path):
        raise FileNotFoundError(f"input file not found: {path}")
    chunk_bytes = max(1, int(args.chunk_size * MB))

    print_header(path, args.workers, args.chunk_size, len(compute_chunks(path, chunk_bytes)))

    print_title("[1] SEQUENTIAL ANALYSIS")
    seq_counts, seq_timings = sequential_count(path)
    print_summary_lines(seq_counts, seq_timings["total_time"])
    print_top_table(seq_counts, args.top)

    print_title("[2] PARALLEL ANALYSIS (MapReduce, Master-Worker)")
    par_counts, par_timings, stats = parallel_count(path, args.workers, chunk_bytes, args.mode)
    print(f"Mode            : {args.mode}")
    print_summary_lines(par_counts, par_timings["total"])
    print_top_table(par_counts, args.top)
    print_breakdown(par_timings)
    print_load_distribution(stats["per_worker"])

    matched = print_correctness(seq_counts, par_counts)
    print_performance(seq_timings["total_time"], par_timings["total"], args.workers)

    print(f"\nTop {args.top} words saved to: {save_top_words(par_counts, args.top)}")
    return 0 if matched else 2


def main() -> int:
    """Parse arguments and run, turning expected errors into friendly messages."""
    # Avoid crashes when printing symbols like ✔ to a console that cannot show them.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = parse_args()
    try:
        return run(args)
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
