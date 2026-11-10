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

## 2026-11-09 — D004 broad-decline descriptive evidence (AI implementation)

The human lead chose broad declines and supplied the reasoning and requirement
for interpretation before AI conclusions; D004 records that separately. AI
operational definitions, support guards, discovery cutoff and screen were fixed
in design.json and committed at a0977d8 before relationship results were inspected.
No claim is made that the lead separately chose those numerical parameters.

Implemented daily_study/declines.py and decline_diagnostics.py. The primary run
loads only date/stock/log_return through 2015-12-31; no future-target columns or
2016–2018 relationship results enter calculations. Integrity hash checks still
verify the existing whole clean artifacts. Stock and pair contexts exclude the
focal names and use common conservative donors; normalization excludes the current
return. Market control is descriptive unit-loading de-medianing, not a fitted
predictive model or a complete causal market-exposure adjustment.

Actually executed:

- Descriptive scan on 730 discovery sessions, 495 names with observed returns,
  489 supported profiles per policy and 119,316 supported pairs per policy.
- Retained all three mechanically selected primary examples plus three fixed
  controls, their sample counts, episode resampling, rank coefficients, matched
  dates and predeclared threshold sensitivities. No screening thresholds relaxed.
- Added explicitly post-hoc floor/transform, influential-observation, baseline
  variation, full-period signed-correlation and maximum-masking-difference checks.
  All checked variants are shown; no preferred floor chosen, no quote/zero changed,
  no new positive hypothesis candidate substituted. These checks are not falsely
  labeled as preregistered. The measurement results do not constitute an AI
  economic conclusion about the lead's hypothesis.
- Two complete primary runs reproduced the entire pair table exactly. A plotting
  shared-axis issue was corrected for the final evidence charts; no numerical
  descriptor or selected example changed. The final examples PNG was visually
  inspected, including the labeled covariance-contribution dates.
- Independent actual-data pandas deletion/median/correlation calculations agreed
  for 30 sampled policy/pair cases; final design and code hashes match the run.
- `python -m pytest -q`: **32 passed** on Python 3.12.14. Tests include exact
  leave-out medians, no future/current contamination of normalization, focal
  exclusion, fixed support screens, deterministic block resampling, filtered
  loading, zero-preserving diagnostic transforms and an end-to-end synthetic run.
  Mathematical fixtures are not market evidence. Eleven third-party timedelta
  deprecation warnings remain; they are not test failures.

Public review exports include the methods, charts, profiles, examples, every
screen-pass pair, measurement checks and manifests. The full pair scan remains an
ignored reproducible Parquet artifact. Source/cleaning policies and Project 001
were unchanged; no prediction model was trained and no PR merged. No AI assessment
of whether D001 is supported or rejected is issued before the lead interprets the
evidence. The next checkpoint is that interpretation, not automatic replication,
model training or selection of a preferred metric after looking at results.

## 2026-11-09 — D005 CVR mathematical investigation (AI assistance)

The lead supplied a cautious interpretation of D004 and the CVR objective; D005
records those human contributions separately. AI assistance drafted
`research/CVR-D005/README.md`: conditional-lift algebra, symmetry and probability
bounds, directional probability companions, historical stress definitions,
severity-mixture confounding, episode dependence, sparse-event identification,
multiple comparisons, masking/coverage and a staged later-replication proposal.
Primary methodological sources are linked. No claim of a new mathematical ratio,
confirmed reference stock or forecasting improvement is made.

Proposed history lengths, quantiles, evidence categories and uncertainty methods
are explicitly unapproved. The next recommended stage after methodology approval
is discovery-only support/precision feasibility, followed by another lead decision
before final operational gates and relationship assessment. No numerical composite
score, pair ranking or CVR production pipeline was implemented.

Actually executed (2026-11-10 UTC / 2026-11-09 America/New_York):

- Dataset-free `research/CVR-D005/verify_algebra.py` checked 45,415 synthetic
  positive-margin contingency tables for count/probability equivalence, symmetry
  and lower/upper probability bounds. All assertions passed. Both labeled
  synthetic examples passed: equal CVR but unequal directional conditional
  probabilities, and pooled CVR above one despite independence within severity
  strata. These calculations are not market evidence.
- Repeated the script and compared its JSON to the published result with `diff`;
  exact match. No full predictive/analysis test suite is newly claimed for this
  documentation-and-algebra change; the 32-test D004 run is recorded above.
- `git diff --check` passed. Project 001's separate checkout is clean and remains
  at `05eb5058a8ecde3a1aeb95e004e44c42ebe708e6`.

No market input files, future-target columns or later-period relationship data
were read for these calculations. The original source, cleaning artifacts and
all Project 001 files were not edited. No predictive training or merge. No human
approval of the proposed methodology is inferred from asking for investigation.

## 2026-11-10 UTC — D006 discovery support feasibility (AI implementation)

D006 separately records the lead's approval, objective of multiple references
with redundancy awareness/abstention, and explicit boundaries. AI assistance
committed the complete feasibility grid at 779af1e before results: four risk
measurements, 60/252-session own histories, 90th/95th quantiles, complete/80%
historical coverage, both masks, episode gap 1/5/10 and disclosed synthetic
precision cases. These are comparison settings, not lead-chosen final criteria.

Implemented daily_study/feasibility.py and tests/test_feasibility.py. Input
projection/date predicates restrict parsed observations to 2013–2015 and exclude
target columns. Market support calculations use exact two-focal-stock exclusion.
Anonymous distributions span all 122,265 pairs of discovery-observed names;
no D004 screen, observed pair CVR, candidate ranking, weighted score or predictive
model is computed. The severity-mixture ratio is a counterfactual from paired
stratum marginals, explicitly not observed pair dependence or causal adjustment.
The discovery-median severity split is retrospective diagnostic stratification,
not an as-of regime boundary. Own-stock stress baselines always end at t-1.

Actually executed:

- Full 64-case policy/definition audit on 730 discovery sessions, 495 observed
  names; stock support, matched masking/history checks, shared-calendar coverage,
  anonymous co-stress/episode counts, uncertainty feasibility and 50,000 labeled
  synthetic experiments. No relationship coefficient used to select a definition.
- Added mandatory D003 hash checks before/after the final run and software/code
  provenance, plus final PNG/SVG charts. Initial/final numerical definitions,
  coverage, masking, history, synthetic and stock-support registries match exactly.
  The final code hash matches the finalized run; three final charts visually checked.
- Final full suite: **42 passed**, Python 3.12.14, 4.59 seconds; 11 previously
  recorded third-party timedelta deprecation warnings. New tests verify timing,
  missingness, exact pair context/median, episode definitions, rare-event bootstrap
  failure, synthetic reproducibility, protected date/column loading, input tamper
  detection and an end-to-end no-model audit.
- Independent actual-data NumPy quantiles/manual histories agreed for 23,360
  stock-date/definition state cases; direct donor deletion agreed for six paired
  support-count cases. A first verification invocation failed on the working
  directory before reading input; corrected project-directory execution passed.
- Original CSV SHA256 is unchanged; four cleaning input hashes match D003 before
  and after. Public numerical exports exactly match the final run. Stock-support
  CSV contains all 31,680 profiles in policy/definition/alphabetical order and is
  losslessly compressed; no reference-stock ranking is published.

The feasibility report explains that coverage and sample concentration constrain
precision, broad severity remains a plausible common explanation, and independent
episodes cannot be certified from grouping rules. It proposes longer auditable
pre-2016 discovery history, not relaxing standards. Numerical planning examples
are explicitly hypothetical precision goals, not new thresholds. The report
separates simultaneous co-stress from future prediction and pairwise association
from incremental information after other references/own-stock/market controls.

No 2016–2018 relationship observations or target columns were parsed. Whole-file
byte hashes verify unchanged inputs without inspecting later relationships.
Source, masks and Project 001 remain unchanged. No training or merge. Final
operational definitions, evidence criteria, new sources and later-period
replication remain subject to human research decisions; no approval is inferred.
