LexiCount: A Parallel Word Frequency Analyzer
BCS43 - Parallel and Distributed Computing

HOW TO RUN
----------
Windows:  double-click  START_LexiCount_Windows.bat
Mac:      double-click  START_LexiCount_Mac.command
          (if macOS says it cannot verify the developer: right-click the file,
           choose Open, then click Open again)

The first time, it sets itself up (about 1-2 minutes, needs internet).
Then the LexiCount dashboard opens in your web browser.
Keep the black window open while using it; close it to stop LexiCount.

REQUIREMENT
-----------
Python 3.10 or newer: https://www.python.org/downloads/
(On Windows, tick "Add python.exe to PATH" during installation.)

WITHOUT INTERNET
----------------
If the dashboard packages cannot be installed, the start file runs the
command-line version instead (it needs only Python). To run it directly:
  Windows:  open a terminal in this folder and type   py launch.py --cli
  Mac:      open a terminal in this folder and type   python3 launch.py --cli

WHAT IS INSIDE
--------------
lexicount/            all the Python source code
  parallel.py         parallel MapReduce version (master + worker processes)
  sequential.py       sequential baseline
  chunker.py          splits the file into chunks without cutting words
  tokenizer.py        word definition and counting
  metrics.py          speedup, efficiency, Karp-Flatt, Amdahl's law
  main.py             command-line program
  dashboard.py        web dashboard
  benchmark.py        performance experiments (python benchmark.py)
  tests/              unit tests (python -m unittest discover -s tests)
  README.md           full documentation
launch.py             the setup-and-start script used by the START files
