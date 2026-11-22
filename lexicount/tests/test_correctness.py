"""Correctness tests: the parallel result must equal the sequential result exactly.

Run from the lexicount folder:
    python -m unittest discover -s tests -v
"""

import os
import shutil
import sys
import tempfile
import unittest

# Make the project modules importable when running from the tests folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chunker import compute_chunks  # noqa: E402
from parallel import parallel_count  # noqa: E402
from sequential import sequential_count  # noqa: E402
from tokenizer import count_words, is_letter  # noqa: E402

NORMAL_TEXT = (b"The quick brown Fox jumps over the lazy dog. Don't stop: the DOG barks!\n"
               b"It's 2024; numbers123 and under_scores split words. The end, THE END.\n") * 40


class TempFileTestCase(unittest.TestCase):
    """Base class that creates a temporary folder for test files."""

    def setUp(self) -> None:
        """Create an empty temporary directory."""
        self.folder = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Delete the temporary directory and everything inside it."""
        shutil.rmtree(self.folder, ignore_errors=True)

    def make_file(self, content: bytes) -> str:
        """Write content to a new temporary file and return its path."""
        path = os.path.join(self.folder, f"test_{len(os.listdir(self.folder))}.txt")
        with open(path, "wb") as file:
            file.write(content)
        return path

    def assert_parallel_matches(self, content: bytes, chunk_size: int,
                                workers: int = 2, mode: str = "offset") -> None:
        """Check parallel == sequential (full Counter) for the given content."""
        path = self.make_file(content)
        expected, _ = sequential_count(path)
        actual, _, _ = parallel_count(path, workers, chunk_size, mode)
        self.assertEqual(expected, actual)
        self.assertEqual(expected, count_words(content))


class TestTokenizer(unittest.TestCase):
    """The shared word definition."""

    def test_case_insensitive_and_contractions(self) -> None:
        """'The'/'THE' merge; "don't" becomes 'don' + 't' by design."""
        counts = count_words(b"The THE the don't")
        self.assertEqual(counts, {"the": 3, "don": 1, "t": 1})

    def test_non_ascii_bytes_are_delimiters(self) -> None:
        """UTF-8 letters such as é split ASCII words."""
        self.assertEqual(count_words("café".encode("utf-8")), {"caf": 1})


class TestChunker(TempFileTestCase):
    """Partitioning must be contiguous, complete and word-safe."""

    def check_chunks(self, content: bytes, chunk_size: int) -> list[tuple[int, int]]:
        """Assert the three chunker guarantees and return the chunks."""
        path = self.make_file(content)
        chunks = compute_chunks(path, chunk_size)
        if not content:
            self.assertEqual(chunks, [])
            return chunks
        self.assertEqual(chunks[0][0], 0)                  # starts at the beginning
        self.assertEqual(chunks[-1][1], len(content))      # covers the whole file
        for (_, end), (next_start, _) in zip(chunks, chunks[1:]):
            self.assertEqual(end, next_start)              # contiguous, no overlap
        for start, end in chunks:
            self.assertGreater(end, start)                 # never empty
            if end < len(content):                         # never splits a word
                self.assertFalse(is_letter(content[end - 1]) and is_letter(content[end]))
        return chunks

    def test_various_chunk_sizes(self) -> None:
        """Guarantees hold for many chunk sizes."""
        for chunk_size in (1, 2, 3, 7, 16, 100, 1000, 10**6):
            with self.subTest(chunk_size=chunk_size):
                self.check_chunks(NORMAL_TEXT, chunk_size)

    def test_edge_cases(self) -> None:
        """Empty file, small file, giant word, no trailing delimiter."""
        self.check_chunks(b"", 16)
        self.assertEqual(self.check_chunks(b"tiny file", 1000), [(0, 9)])
        self.assertEqual(len(self.check_chunks(b"a" * 5000 + b" end", 16)), 2)
        self.check_chunks(b"ends without delimiter", 5)

    def test_invalid_chunk_size(self) -> None:
        """A chunk size of 0 is rejected."""
        with self.assertRaises(ValueError):
            compute_chunks(self.make_file(b"abc"), 0)


class TestParallelEqualsSequential(TempFileTestCase):
    """Full-Counter equality between the two implementations."""

    def test_word_exactly_on_chunk_boundary(self) -> None:
        """A word that starts/ends exactly where a naive split would cut."""
        content = b"aaaa bbbb" + b"wordacrossboundary" + b" cccc"
        for chunk_size in range(1, 20):
            with self.subTest(chunk_size=chunk_size):
                self.assert_parallel_matches(content, chunk_size)

    def test_tiny_chunks_on_normal_file(self) -> None:
        """16-byte chunks on a normal file, in both modes."""
        for mode in ("offset", "send"):
            with self.subTest(mode=mode):
                self.assert_parallel_matches(NORMAL_TEXT, 16, workers=3, mode=mode)

    def test_empty_file(self) -> None:
        """No words at all."""
        self.assert_parallel_matches(b"", 16)

    def test_punctuation_only(self) -> None:
        """Only delimiters: zero words."""
        self.assert_parallel_matches(b"... ,,, !!! ??? 123 456 --- \n\n", 4)

    def test_single_word(self) -> None:
        """One word without a trailing delimiter."""
        self.assert_parallel_matches(b"Hello", 2)

    def test_word_longer_than_chunk(self) -> None:
        """A 10,000-letter word with 16-byte chunks."""
        self.assert_parallel_matches(b"start " + b"x" * 10_000 + b" finish", 16)

    def test_utf8_and_windows_line_endings(self) -> None:
        """é, ñ, emoji and CRLF line endings."""
        content = "Café niño 😀 smile\r\nJalapeño résumé 🚀 rocket\r\nend\r\n".encode("utf-8") * 50
        for mode in ("offset", "send"):
            with self.subTest(mode=mode):
                self.assert_parallel_matches(content, 7, workers=2, mode=mode)

    def test_worker_counts_and_modes(self) -> None:
        """Worker counts 1, 2, 3, 8 in both communication modes."""
        for workers in (1, 2, 3, 8):
            for mode in ("offset", "send"):
                with self.subTest(workers=workers, mode=mode):
                    self.assert_parallel_matches(NORMAL_TEXT, 64, workers=workers, mode=mode)

    def test_missing_file(self) -> None:
        """A friendly FileNotFoundError, not a crash inside a worker."""
        with self.assertRaises(FileNotFoundError):
            parallel_count(os.path.join(self.folder, "missing.txt"), 2, 16)


if __name__ == "__main__":
    unittest.main()
