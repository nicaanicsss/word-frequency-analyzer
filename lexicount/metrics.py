"""Performance metrics shared by main.py, benchmark.py and visualize.py.

Formulas (p = number of workers):
    Speedup        S = T_seq / T_par
    Efficiency     E = S / p
    Karp-Flatt     e = (1/S - 1/p) / (1 - 1/p)     (estimated serial fraction)
    Amdahl's Law   S_max(p) = 1 / (e + (1 - e) / p)
"""

from typing import Optional


def speedup(sequential_time: float, parallel_time: float) -> float:
    """S = T_seq / T_par. Above 1 means the parallel version is faster."""
    return sequential_time / parallel_time if parallel_time > 0 else 0.0


def efficiency(speedup_value: float, workers: int) -> float:
    """E = S / p, as a fraction (1.0 means perfect use of every worker)."""
    return speedup_value / workers if workers > 0 else 0.0


def karp_flatt(speedup_value: float, workers: int) -> Optional[float]:
    """Experimentally estimated serial fraction e. Undefined for p = 1 or S = 0."""
    if workers <= 1 or speedup_value <= 0:
        return None
    return (1 / speedup_value - 1 / workers) / (1 - 1 / workers)


def amdahl_speedup(serial_fraction: float, workers: float) -> float:
    """Amdahl's Law: the best possible speedup on p workers for serial fraction e."""
    return 1 / (serial_fraction + (1 - serial_fraction) / workers)
