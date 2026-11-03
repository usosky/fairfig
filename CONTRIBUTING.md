# Development

## Set up

```bash
git clone https://github.com/usosky/fairfig
cd fairfig
pip install -e ".[test,docs]" mypy ruff
```

## Tests

```bash
pytest --mpl          # unit tests, figure snapshots, and every script in examples/
ruff check .          # lint
mypy                  # type check (strict)
```

- **Figure snapshots** (`tests/test_snapshots.py`) draw the cookbook figures and compare
  them pixel by pixel with the images in `tests/baseline/`. Text rendering depends on
  the FreeType version matplotlib is built with, so there is one folder per version;
  [`tests/baseline/README.md`](https://github.com/usosky/fairfig/blob/main/tests/baseline/README.md)
  explains how to make new baselines after a deliberate change to the look. Without
  `--mpl` the figures are drawn but not compared.
- **CI** (`.github/workflows/tests.yml`) runs the tests on every push for Python 3.9 to
  3.14 with matplotlib 3.7 to 3.11, on Linux, Windows and macOS, plus Python 3.15 ahead
  of its release. A failed snapshot uploads the baseline, the new image and their
  difference as an artifact of the job.
- Code style: type hints on every function, NumPy-style docstrings (the API reference
  is built from them), British spelling.

## Documentation

```bash
mkdocs serve          # http://127.0.0.1:8000, reloads on every change
```

The pages are in `docs/`; the API reference comes from the docstrings, and the cookbook
page includes the code of `examples/demo_phase_equilibria.py` between its
`--8<-- [start:…]` and `[end:…]` markers. After a change to the look, refresh the images
with `python examples/make_readme_images.py` and `python examples/make_identity_sheet.py`.
Every push to `main` deploys the site to <https://usosky.github.io/fairfig/>.

## Releasing

Once, before the first release:

1. **PyPI**: sign in at pypi.org, open *Your account → Publishing* and add a *pending
   publisher* for GitHub: project name `fairfig`, owner `usosky`, repository `fairfig`,
   workflow `release.yml`, environment `pypi`. No token is stored anywhere: PyPI trusts
   that workflow.
2. **Zenodo**: the GitHub integration is switched on for `usosky/fairfig` (zenodo.org →
   *GitHub*), and `.zenodo.json` holds the metadata.

For each release:

1. Set the new version in `fairfig/__init__.py` (`__version__`) and in `CITATION.cff`
   (`version` and `date-released`), and describe the changes at the top of
   `CHANGELOG.md`. `tests/test_package.py` checks that the three agree.
2. Push to `main` and wait for *Tests* and *Docs* to pass. *Actions → Release → Run
   workflow* is a dry run: it checks the versions, builds the package and tests the wheel
   without publishing.
3. On GitHub, *Releases → Draft a new release*: tag `v1.3.0` (the version with a `v`),
   title `fairfig 1.3.0`, the changelog section as notes. Publish it.
4. The *Release* workflow uploads the package to PyPI, and Zenodo archives the release
   and gives it a DOI. The DOI badge in the README always points to the latest version.

If the version check fails, delete the release and its tag, fix the version and make the
release again.
