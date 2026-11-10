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


## 2026-11-09 — Approved daily-data pilot: integrity investigation only

The lead approved the Plotly source and provisionally approved five sessions; D002
records those human decisions without changing D001. AI assistance wrote the
daily_study audit/target utilities, tests, evidence ledger and quality report.
The original Optiver tools are preserved and their initial README is archived;
no claim is made that the daily pilot uses Optiver microstructure observations.

Actually executed:

- Read the unchanged 619,040-row source, verifying its SHA-256 before/after.
- Cross-checked all dates against XNYS sessions (exchange-calendars 4.13.2).
- Audited fields, missing stock sessions, OHLC contradictions, repeated records,
  large returns and simple-ratio candidates; researched 24 evidence-led cases.
- Generated real-data issue registers, policy-effect counts and three SVG figures.
  No raw source CSV, credentials, or full target table was committed.
- Previewed proposed exclusions without writing corrected/cleaned prices; all
  future-target use was limited to integrity/count sensitivity, not model fitting,
  relationship discovery, regime choice or selection on forecast results.
- `python -m pytest -q`: **20 passed** in 2.45 seconds on Python 3.12.14. Five
  warnings came from exchange-calendars/NumPy timedelta compatibility; tests did
  not fail. Tests use labeled mathematical fixtures, not fabricated market evidence.
- `pip check`: no broken requirements. A separate project-local research virtual
  environment was installed; Project 001's dependencies were not changed.
- The full actual-data target panel was independently cross-checked against NumPy
  sliding six-close windows (separate from the shift-based implementation).
- SVG visual inspection via browser capture encountered a file-URL policy block,
  then a screenshot timeout over local HTTP. An equivalent PNG plot of the same
  actual case-study observations was generated for visual inspection; no browser
  screenshot success is claimed.
- Project 001 checkout remained clean at commit 05eb505; it was not modified.

The proposed mask policy, final adjustment basis, chronological fold boundaries,
context definition and model choices remain unapproved. No predictive model was
trained, no replacement price was invented, and no PR was merged. The complete
corporate-action history and all 72 unresolved general extreme moves remain open.

## 2026-11-09 — D003 provisional cleaning implementation (AI work)

D003 separately records the human approval and its conditions. AI assistance
implemented the approved masks in `daily_study/clean.py`, retaining the unchanged
source and a full aligned-original artifact. No observations were deleted or
replaced. A narrow comparison quarantines internally inconsistent records; the
conservative view adds repeated-record suspicion. Both share the verified economic
boundary guards; an error-only reference prevents those events being mislabeled
as data errors. These comparison definitions and fixed selection-audit bands are
implementation recommendations, not additional choices attributed to the lead.

Actually executed on the approved 619,040-row source:

- Persisted versioned raw/reference/narrow/conservative views in the ignored
  `artifacts/clean-D003-v1-final` run, with price/return/target reason codes, target
  end dates and OHLC-feature eligibility. No prediction model or training split.
- Produced 2,315 direct cause/review entries and exhaustive links from each of the
  153 narrow / 9,599 conservative newly unavailable targets to actual price or
  boundary causes. The first development run correctly stopped on a missing cause
  mapping in the error-only reference; that mapping was fixed and regression-tested.
  Incomplete development output is not the final verified run.
- Compared stock, origin-date, year, fixed observed market-direction/variation and
  activity-proxy bands. Raw and quality-eligible proxy definitions are both shown;
  neither uses future target values as a context indicator or fits a predictive regime.
- Verified unchanged source hashes, exact original-field equality for all recorded
  rows in the aligned artifact, no invented analysis prices, nested mask coverage,
  and all per-run artifact hashes on the actual data.
- Verified AMD/VRTX event returns and all five preceding shock-containing labels
  for each survive in both policies. This is not a claim that every genuine event
  has been adjudicated.
- `python -m pytest -q`: **24 passed** in 3.35 seconds, Python 3.12.14, after final
  implementation changes. Tests include immutable source, policy nesting, missing
  opening-price behavior, no magnitude clipping, action/origin timing, complete
  cause attribution, paired-date hindsight, and tamper detection. Eleven warnings
  are third-party NumPy/exchange-calendar timedelta deprecations, not failures.

The raw source, detailed analysis views and hash registry remain private working
artifacts; public review exports contain the full reason ledger, downstream cause
links, aggregate availability/rates, manifest and concentration chart. No API
credentials or restricted Kaggle files were used or committed. Full-day market
condition labels are descriptive audit choices, not adopted forecasting contexts.
Original feed delivery timestamps remain unknown; 1,066 first repeated records
need future-session comparisons. Point-in-time validity is not claimed.

No training or merge was performed. Project 001's checkout and dependencies were
unchanged. The next proposed no-model descriptive experiment is left for the lead
to review and choose the economic context before implementation.
