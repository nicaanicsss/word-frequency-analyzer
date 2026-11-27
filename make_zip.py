"""Build LexiCount.zip for submission: python make_zip.py [output.zip]

Takes only the files tracked by git (plus new, not-ignored files), so the virtual environment,
generated datasets, caches and the .git folder are never included. Everything is placed inside a
top-level "LexiCount" folder, and the Mac start file keeps its "executable" permission.
"""

import os
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
FOLDER = "LexiCount"
SKIP = {"make_zip.py", ".gitignore", ".gitattributes"}  # repo housekeeping, not needed by the professor


def project_files() -> list[str]:
    tracked = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                             cwd=HERE, capture_output=True, text=True, check=True).stdout.split("\n")
    return sorted(path for path in tracked
                  if path and os.path.isfile(os.path.join(HERE, path))
                  and os.path.basename(path) not in SKIP)


def main() -> int:
    output = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "LexiCount.zip"))
    files = project_files()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            info = zipfile.ZipInfo.from_file(os.path.join(HERE, path), f"{FOLDER}/{path}")
            mode = 0o755 if path.endswith((".command", ".sh")) else 0o644
            info.external_attr = (0o100000 | mode) << 16  # regular file + permissions
            info.compress_type = zipfile.ZIP_DEFLATED
            with open(os.path.join(HERE, path), "rb") as source:
                archive.writestr(info, source.read())
    print(f"{output}: {len(files)} files, {os.path.getsize(output) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
