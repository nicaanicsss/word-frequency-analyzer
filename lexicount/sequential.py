"""Sequential baseline: one process reads the whole file and counts every word.

This is the reference implementation. Its execution time is T_seq in the
speedup formula S = T_seq / T_par, and its result is the "ground truth" the
parallel version must match exactly.
"""

import time
from collections import Counter

from tokenizer import count_words


def sort_by_frequency(counts: Counter[str]) -> Counter[str]:
    """Return a new Counter whose keys are ordered from most to least frequent.

    Counters compare equal regardless of key order, so this does not affect
    correctness checks; it just lets callers read the ranking in order.
    """
    return Counter(dict(counts.most_common()))


def sequential_count(path: str) -> tuple[Counter[str], dict[str, float]]:
    """Count words in a file using a single process.

    Args:
        path: Path of the text file to analyze.

    Returns:
        (counts, timings) where counts is a frequency-ordered Counter and
        timings holds read_time, count_time, sort_time and total_time in seconds.
    """
    start = time.perf_counter()

    # Read the whole file in binary: the tokenizer works on bytes.
    with open(path, "rb") as file:
        data = file.read()
    after_read = time.perf_counter()

    counts = count_words(data)
    after_count = time.perf_counter()

    counts = sort_by_frequency(counts)
    end = time.perf_counter()

    timings = {
        "read_time": after_read - start,
        "count_time": after_count - after_read,
        "sort_time": end - after_count,
        "total_time": end - start,
    }
    return counts, timings
