# LexiCount: A Parallel Word Frequency Analyzer Using Data Decomposition and MapReduce

## Overview

LexiCount counts how often every word appears in a large text file and lists the most
frequent ones. It does the job twice: once with a normal **sequential** program (one
process, one CPU core) and once with a **parallel** program that splits the file into
chunks and lets several worker processes count different chunks at the same time.
It then checks that both versions found exactly the same counts and reports how much
faster the parallel version was.

The parallel version follows the **MapReduce** pattern on a **master-worker** process
pool. The master cuts the file into word-safe byte ranges (data decomposition), the
workers count words in their chunks (map), and the master merges the partial counts
(reduce). A benchmark suite measures speedup, efficiency and overhead for different
numbers of workers, file sizes, chunk sizes and communication strategies, and
produces charts that explain the results with Amdahl's Law and the Karp-Flatt metric.

## Setup

Requires Python 3.10+. The core uses only the standard library; `matplotlib` is needed
for charts and `streamlit` is optional (dashboard only).

**Windows (PowerShell)**
```powershell
cd lexicount
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**
```bash
cd lexicount
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```bash
python dataset_generator.py 1 10 50 100 500        # create test files in data/ (offline)
python main.py --file data/dataset_100MB.txt --workers 4
python main.py --generate 100                       # generate + analyze in one step
python main.py --file data/dataset_100MB.txt --chunk-size 1 --mode send --top 20
python -m unittest discover -s tests -v             # correctness tests
python -m streamlit run dashboard.py                # landing page + live-demo dashboard
```

| Option | Meaning | Default |
|---|---|---|
| `--file PATH` / `--generate SIZE_MB` | input file, or generate `data/dataset_<SIZE>MB.txt` first | (one required) |
| `--workers N` | number of worker processes | CPU cores |
| `--chunk-size MB` | target chunk size | 4 |
| `--top N` | number of top words shown and saved to `results/top_words.csv` | 10 |
| `--mode offset\|send` | send byte ranges (default) or chunk data to workers | offset |

To use real text, place a book (e.g. from Project Gutenberg) at `data/seed.txt`; the
generator will replicate it instead of generating synthetic Zipf-distributed text.
(Delete existing `data/dataset_*.txt` files or pass `--force` to regenerate.)

## Project structure

| File | Purpose |
|---|---|
| `tokenizer.py` | Shared word definition (`[A-Za-z]+`, case-insensitive, on bytes) |
| `sequential.py` | Sequential baseline |
| `chunker.py` | Word-boundary-safe partitioning into byte ranges |
| `parallel.py` | MapReduce master-worker implementation (`multiprocessing.Pool`) |
| `metrics.py` | Speedup, efficiency, Karp-Flatt, Amdahl formulas |
| `main.py` | CLI: runs both versions and prints the report |
| `benchmark.py` | Experiments A-D, saves `results/benchmark_results.csv/.json` |
| `visualize.py` | Charts (PNG, 300 dpi) from the benchmark results |
| `dataset_generator.py` | Offline dataset creation |
| `dashboard.py` | Streamlit entry point; the Analyzer view keeps the original dashboard |
| `landing_page.py` | Landing page and temporary How it works / About views |
| `tests/test_correctness.py` | `unittest` suite |

## How PDC concepts map to the code

| Concept | File | Function |
|---|---|---|
| Partitioning (PCAM) - data decomposition | `chunker.py` | `compute_chunks`, `find_boundary` |
| Communication (PCAM) - offset vs send modes, combiner keeps results small | `parallel.py` | `build_tasks`, `map_chunk`, `read_range` |
| Agglomeration (PCAM) - grouping bytes into MB-sized chunks | `chunker.py` | `compute_chunks` (`--chunk-size`) |
| Mapping / Load balancing - many chunks, dynamic scheduling | `parallel.py` | `parallel_count` (`imap_unordered`, `chunksize=1`), `summarize_workers` |
| Map phase (+ local combiner) | `parallel.py` | `map_chunk` → `tokenizer.count_words` |
| Reduce phase | `parallel.py` | `parallel_count` (`total.update(partial)`) |
| Synchronization | `parallel.py` | `parallel_count` (`with Pool`, result loop, `close()`/`join()`) |
| GIL / why processes, not threads | `parallel.py` | module docstring, `multiprocessing.Pool` |
| Performance metrics | `metrics.py` | `speedup`, `efficiency`, `karp_flatt`, `amdahl_speedup` |

## Reproducing the benchmarks and charts

```bash
python dataset_generator.py 1 10 50 100 500
python benchmark.py                 # ~15 min on 8 cores; use --runs 3 for a quicker run
python visualize.py
```

| Experiment | What changes | What it shows |
|---|---|---|
| A - strong scaling | workers 1, 2, 4, ... cores (100 MB) | speedup, efficiency, Amdahl fit |
| B - data scaling | file 1-500 MB (all cores) | overhead dominates small files; crossover |
| C - agglomeration | chunk 0.25-64 MB | too small = overhead, too large = poor load balance |
| D - communication | offset vs send mode | cost of moving data between processes |

Each configuration: 1 discarded warm-up run + 5 measured runs (mean, median, std dev),
every run verified against the sequential result. Machine info is stored in the results.

Charts written to `results/`: `execution_time_vs_workers.png`, `speedup_vs_workers.png`,
`efficiency_vs_workers.png`, `time_vs_file_size.png`, `chunk_size_effect.png`,
`offset_vs_send.png`, `time_breakdown_stacked.png`.

## Formulas

With `p` workers, `T_seq` the sequential time and `T_par` the parallel time:

| Metric | Formula | Meaning |
|---|---|---|
| Speedup | $S = T_{seq} / T_{par}$ | how many times faster the parallel version is |
| Efficiency | $E = S / p$ | fraction of ideal speedup achieved (100% = perfect) |
| Amdahl's Law | $S(p) = \dfrac{1}{f + (1 - f)/p}$ | max speedup when a fraction `f` of the work is serial; limit `1/f` |
| Karp-Flatt | $e = \dfrac{1/S - 1/p}{1 - 1/p}$ | serial fraction estimated from a measured speedup |

## Design notes

* **Word definition:** a maximal run of ASCII letters, case-insensitive. `don't` → `don`, `t`
  by design. Every non-letter byte (including all UTF-8 multibyte bytes) is a delimiter,
  so a chunk can safely end at any non-letter byte.
* **Correctness:** the full Counters are compared (every word), not only the top N.
* **Windows/macOS:** both use the `spawn` start method, so every entry script is guarded by
  `if __name__ == "__main__":` and workers share no global mutable state.
