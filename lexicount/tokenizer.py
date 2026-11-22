"""Shared tokenizer used by BOTH the sequential and the parallel implementation.

Using exactly the same counting function in both versions guarantees that any
difference in the results can only come from how the work is split, never from
two different definitions of "word".

Definition of a word
--------------------
A word is a maximal run of ASCII letters (A-Z, a-z), compared case-insensitively.
Everything else (digits, spaces, punctuation, apostrophes and every byte of a
UTF-8 multibyte character, which are all >= 0x80) is a delimiter.

By design "don't" is counted as two words: "don" and "t". This keeps the rule
simple and identical for every chunk, which is what makes safe partitioning
possible: a chunk may end at ANY non-letter byte without splitting a word.
"""

import re
from collections import Counter

# Precompiled once at import time. Each worker process imports this module, so
# every process gets its own compiled copy (no shared mutable state).
WORD_PATTERN = re.compile(rb"[A-Za-z]+")

# The 52 byte values that count as "letters". The chunker uses this set to
# find safe chunk boundaries, so both modules share one definition.
LETTER_BYTES = frozenset(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")


def is_letter(byte_value: int) -> bool:
    """Return True if a single byte value (0-255) is an ASCII letter."""
    return byte_value in LETTER_BYTES


def count_words(data: bytes) -> Counter[str]:
    """Count case-insensitive ASCII words in a block of bytes.

    Steps:
      1. Find every letter run exactly as written ("The", "THE", "the").
      2. Count those raw matches (fast, done in C by Counter).
      3. Merge the case variants into one lowercase str key. This loop runs
         once per DISTINCT spelling, which is tiny compared to the number of
         words, so lowering here is much cheaper than lowering all the data.

    Args:
        data: Raw file bytes (a whole file or one chunk of it).

    Returns:
        Counter mapping lowercase word (str) -> number of occurrences.
    """
    raw_counts = Counter(WORD_PATTERN.findall(data))

    counts: Counter[str] = Counter()
    for raw_word, occurrences in raw_counts.items():
        # The regex only matches ASCII letters, so ascii decoding never fails.
        counts[raw_word.lower().decode("ascii")] += occurrences
    return counts
