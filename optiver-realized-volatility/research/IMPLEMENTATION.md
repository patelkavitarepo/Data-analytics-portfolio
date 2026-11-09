# AI implementation log — separate from human decisions

## 2026-11-09 — Research foundation

**AI-assisted implementation:** created a separate worktree and feature branch
`feat/002-optiver-research` from `origin/main`. Project 001's checkout, code,
requirements, branch, and PR were left unchanged. This project has its own ignore
rules, dependency list, pytest configuration, research documents, and workflow.

**Source review:** consulted indexed official competition data/evaluation/host-Q&A
material. Found a direct Kaggle network denial and no configured local Kaggle
credentials. This is a data-access blocker, not an empirical finding.

**Code written by AI assistance:** target-free book/trade features, within-window
realized volatility, explicit zero-depth/coverage behavior, RMSPE validation,
manifest-gated local discovery runner, SHA-256 source tracking, stock profile and
chart generation, explicit-context similarity/count utility, private review UI,
and synthetic-fixture tests. No complex or simple prediction models were trained.

**Methodological proposals drafted by AI assistance:** indicator definitions,
factor/selection-bias warnings, individual/pooled/shared/static-peer/context-aware
comparisons, controls, nested time-group validation, and publication boundaries.
These have not been adopted as human decisions. No empirical interpretation is
attributed to the lead.

**Empirical outputs:** none. Test outputs are temporary synthetic fixtures and are
not portfolio findings. Official schema compatibility, data coverage, economic
validity, and forecast performance remain untested on real competition files.

### Verification actually run

- Python 3.12.14, pandas 2.3.3, NumPy 2.5.4, PyArrow 26.0.1, Plotly 6.9.0,
  Streamlit 1.67.0, pytest 9.2.0. Reused an already installed environment without
  changing Project 001's dependencies.
- `python -m pytest -q` from the project folder: **13 passed** in 1.38 seconds on
  the current code. This includes a temporary Parquet-to-feature-to-chart run
  using labeled synthetic fixtures and a deliberately unreadable target file,
  verifying that the initial runner never reads target values or excluded windows.
- Real Chromium browser against the running UI at port 8504, 1024×1366 touch
  viewport: correct no-data warning, zero market charts/metrics, zero application
  exceptions, and zero JavaScript page errors. This is not an iPad Safari test.
- Project 001 checkout: `git status --porcelain` was empty; its files were untouched.
- No official-data audit, fitted relationship, model score, or interpretation has
  been run. Python 3.11/3.12 CI is configured; remote results are distinct from
  this local run and must be checked independently.
