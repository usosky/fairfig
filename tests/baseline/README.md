# Snapshot baselines

`tests/test_snapshots.py` draws the cookbook figures and compares them with these
images (`pytest --mpl`). Text rendering depends on the FreeType library that
matplotlib is built with, so there is one folder per FreeType version:

| Folder | Used by |
|---|---|
| `freetype-2.6/` | matplotlib 3.7 to 3.10 (pip wheels bundle FreeType 2.6.1) |
| `freetype-2.14/` | matplotlib 3.11 and later (pip wheels bundle FreeType 2.14) |

Matplotlib 3.8, 3.9 and 3.10 draw these figures pixel for pixel the same; 3.7 differs
slightly (RMS < 0.7, contour maps 5.1), which the tolerances in `test_snapshots.py`
allow. Where no folder matches (e.g. a conda-forge matplotlib built against the
system FreeType), the comparison is skipped locally; CI requires it.

## After a deliberate change to the look

Make new baselines, look at every image, and commit them with the change. Either run
**Actions → Snapshot baselines → Run workflow** and unzip its two artifacts
(`baselines-freetype-2.6`, `baselines-freetype-2.14`) into this folder, or locally:

```bash
pip install -e ".[test]" "matplotlib==3.10.*"
pytest tests/test_snapshots.py --mpl-generate-path=tests/baseline/freetype-2.6
pip install "matplotlib==3.11.*"
pytest tests/test_snapshots.py --mpl-generate-path=tests/baseline/freetype-2.14
```

When a snapshot fails in CI, the job uploads a `snapshot-diffs-…` artifact with the
baseline, the new image and their difference for each failed test.
