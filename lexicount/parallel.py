"""Parallel word counting with MapReduce on a master-worker process pool.

Roles
-----
MASTER (this process): partitions the file, hands out tasks, merges results.
WORKERS (Pool processes): each counts the words of one chunk at a time.

Why processes and not threads? In CPython the Global Interpreter Lock (GIL)
lets only one thread run Python bytecode at a time, so CPU-bound counting
would not speed up with threads. Separate processes each have their own
interpreter and their own GIL, so they truly run on different CPU cores.

Communication modes (to measure communication overhead)
------------------------------------------------------
"offset" (default): the master sends only (path, start, end). Each worker
    opens the file, seeks and reads its own range. Very little IPC.
"send": the master reads the chunk bytes and sends the data itself through
    the inter-process pipe. Much more IPC; used only for comparison.
"""

import os
import sys
import time
from collections import Counter
from multiprocessing import Pool
from typing import Iterator, Optional

from chunker import compute_chunks
from sequential import sort_by_frequency
from tokenizer import count_words

MODES = ("offset", "send")

# A task is (path, start, end, data). In "offset" mode data is None and the
# worker reads the bytes itself; in "send" mode data holds the chunk bytes.
Task = tuple[str, int, int, Optional[bytes]]
# A map result is (partial counts, seconds the worker spent, worker PID).
MapResult = tuple[Counter[str], float, int]


def read_range(path: str, start: int, end: int) -> bytes:
    """Read bytes [start, end) of a file."""
    with open(path, "rb") as file:
        file.seek(start)
        return file.read(end - start)


def map_chunk(task: Task) -> MapResult:
    """MAP PHASE: count the words of one chunk inside a worker process.

    The worker returns a Counter (local aggregation, the MapReduce "combiner"),
    never a raw list of words, so only a few thousand (word, count) pairs travel
    back to the master instead of millions of words.
    """
    started = time.perf_counter()
    path, start, end, data = task
    if data is None:  # "offset" mode: COMMUNICATION is just three numbers
        data = read_range(path, start, end)
    partial_counts = count_words(data)
    busy_seconds = time.perf_counter() - started
    return partial_counts, busy_seconds, os.getpid()


def build_tasks(path: str, chunks: list[tuple[int, int]], mode: str) -> Iterator[Task]:
    """Yield one task per chunk.

    A generator is used so that in "send" mode the master reads chunk data
    lazily, one chunk at a time, instead of loading the whole file at once.
    """
    for start, end in chunks:
        if mode == "send":
            yield (path, start, end, read_range(path, start, end))
        else:
            yield (path, start, end, None)


def validate_arguments(path: str, workers: int, chunk_size: int, mode: str) -> Optional[str]:
    """Raise ValueError/FileNotFoundError for bad input; return a warning or None."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"input file not found: {path}")
    if workers < 1:
        raise ValueError("workers must be at least 1")
    if chunk_size <= 0:
        raise ValueError("chunk size must be greater than 0")
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")

    cpu_count = os.cpu_count() or 1
    if workers > cpu_count:
        return (f"{workers} workers requested but only {cpu_count} CPU cores exist; "
                "extra workers will compete for the same cores.")
    return None


def summarize_workers(chunk_records: list[dict]) -> dict[int, dict[str, float]]:
    """LOAD BALANCING report: number of chunks and total busy time per worker PID."""
    per_worker: dict[int, dict[str, float]] = {}
    for record in chunk_records:
        entry = per_worker.setdefault(record["pid"], {"chunks": 0, "busy": 0.0})
        entry["chunks"] += 1
        entry["busy"] += record["seconds"]
    return per_worker


def parallel_count(path: str, workers: int, chunk_size: int,
                   mode: str = "offset") -> tuple[Counter[str], dict[str, float], dict]:
    """Count words in a file with a pool of worker processes (MapReduce).

    Args:
        path: File to analyze.
        workers: Number of worker processes (p).
        chunk_size: Target chunk size in BYTES.
        mode: "offset" (send byte ranges) or "send" (send chunk data).

    Returns:
        (counts, timings, stats)
        counts  - frequency-ordered Counter, identical to the sequential one
        timings - pool_startup, partition, map_reduce, sort, pool_shutdown, total
        stats   - chunk count, per-chunk records, per-worker summary, warning
    """
    warning = validate_arguments(path, workers, chunk_size, mode)
    if warning:
        print(f"WARNING: {warning}", file=sys.stderr)

    total_start = time.perf_counter()
    total: Counter[str] = Counter()
    chunk_records: list[dict] = []

    # SYNCHRONIZATION: the context manager guarantees the pool is cleaned up
    # even if an error happens.
    with Pool(processes=workers) as pool:
        after_startup = time.perf_counter()

        # PARTITIONING (PCAM) + AGGLOMERATION: word-safe byte ranges.
        chunks = compute_chunks(path, chunk_size)
        after_partition = time.perf_counter()

        # MAPPING / LOAD BALANCING: many more chunks than workers, handed out
        # one at a time (chunksize=1). imap_unordered gives each result back
        # as soon as it is ready, so a worker that finishes early immediately
        # takes the next chunk (dynamic scheduling).
        results = pool.imap_unordered(map_chunk, build_tasks(path, chunks, mode), chunksize=1)

        # REDUCE PHASE: merge each partial Counter as soon as it arrives.
        # update() adds counts in place; sum(counters, Counter()) would build
        # a brand-new Counter at every step and be much slower.
        for partial_counts, seconds, pid in results:
            total.update(partial_counts)
            chunk_records.append({"pid": pid, "seconds": seconds})
        # SYNCHRONIZATION: this point is reached only after ALL chunks have
        # been mapped and reduced (the loop above consumes every result).
        after_map_reduce = time.perf_counter()

        pool.close()  # no more tasks will be submitted
        pool.join()   # wait for every worker process to exit
        after_shutdown = time.perf_counter()

    # Final serial step done by the master: rank words by frequency.
    total = sort_by_frequency(total)
    total_end = time.perf_counter()

    timings = {
        "pool_startup": after_startup - total_start,
        "partition": after_partition - after_startup,
        "map_reduce": after_map_reduce - after_partition,
        "pool_shutdown": after_shutdown - after_map_reduce,
        "sort": total_end - after_shutdown,
        "total": total_end - total_start,
    }
    stats = {
        "workers": workers,
        "mode": mode,
        "chunk_size": chunk_size,
        "num_chunks": len(chunks),
        "chunk_records": chunk_records,
        "per_worker": summarize_workers(chunk_records),
        "warning": warning,
    }
    return total, timings, stats
