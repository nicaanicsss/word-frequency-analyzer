"""Word-boundary-safe partitioning of a file into byte ranges.

PARTITIONING (PCAM): the data (the file) is decomposed into independent pieces
that can be counted in parallel. This is DATA DECOMPOSITION.

AGGLOMERATION (PCAM): instead of one task per word or per line (far too many
tiny tasks, each with communication overhead), bytes are grouped into chunks
of a configurable size (default 4 MB).

Each chunk is described only by (start, end) byte offsets, end exclusive.
Chunks are contiguous and non-overlapping, so:
  * no byte is skipped        (chunk i+1 starts exactly where chunk i ends)
  * no byte is counted twice  (ranges never overlap)
  * no word is split          (every boundary sits on a non-letter byte)
"""

import os
from typing import BinaryIO

from tokenizer import is_letter

DEFAULT_CHUNK_SIZE_MB = 4
SCAN_BUFFER_BYTES = 256  # small read used while searching for a boundary


def find_boundary(file: BinaryIO, position: int, file_size: int) -> int:
    """Return the first offset >= position whose byte is NOT a letter.

    Cutting the file at that offset is safe: the byte there is a delimiter,
    so the word before it (if any) is complete. If the end of the file is
    reached first (e.g. a giant word), the file size is returned.
    """
    file.seek(position)
    while position < file_size:
        buffer = file.read(SCAN_BUFFER_BYTES)
        if not buffer:
            break
        for index, byte_value in enumerate(buffer):
            if not is_letter(byte_value):
                return position + index
        position += len(buffer)
    return file_size


def compute_chunks(path: str, chunk_size_bytes: int) -> list[tuple[int, int]]:
    """Split a file into word-safe (start, end) byte ranges.

    Algorithm: start at 0, jump ahead by chunk_size_bytes, then move forward
    to the next non-letter byte; that offset is the boundary. Repeat to EOF.

    Edge cases:
      * empty file               -> []
      * file smaller than chunk  -> [(0, file_size)]
      * word longer than chunk   -> that chunk simply grows to hold the word
      * no trailing delimiter    -> last chunk ends at file_size

    Args:
        path: File to partition.
        chunk_size_bytes: Target size of each chunk (must be > 0).

    Returns:
        List of (start, end) offsets covering the whole file in order.
    """
    if chunk_size_bytes <= 0:
        raise ValueError("chunk size must be greater than 0 bytes")

    file_size = os.path.getsize(path)
    chunks: list[tuple[int, int]] = []
    start = 0

    with open(path, "rb") as file:
        while start < file_size:
            end = min(start + chunk_size_bytes, file_size)
            if end < file_size:
                end = find_boundary(file, end, file_size)
            chunks.append((start, end))
            start = end  # next chunk begins exactly here: contiguous ranges
    return chunks
