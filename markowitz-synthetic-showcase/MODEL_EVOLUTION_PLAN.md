# Model Evolution Protocol · 006-evolution-v1

Status: **policy/checkpoint only; no new experiment or approved challenger**.
Authorized by [Holmes checkpoint 6833527231](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6833527231).
The ETF hypothesis remains empirically unanswered. [Data rights](DATA_RIGHTS.md),
[independent adjustment verification](ADJUSTMENT_REVIEW.md), and all existing
source/holdout gates still apply. This protocol cannot enable them.

## Purpose and frozen reference

More observations can improve estimation without guaranteeing that future market
structure follows earlier estimated relationships. This is a **research rationale**,
not a verbatim owner quotation. The owner's personal lesson and any portfolio
quotation remain **pending final editorial approval**; publication is not approved.

“Champion” means the frozen **006-v1 reference**, not a proven investment winner:
minimum variance and LOCAL max-Sharpe with equal weight retained as comparator
(and SPY as the empirical external benchmark). Preserve the eight ETFs, 2016–2022
training, 2023–2024 validation, untouched 2025+ reserve, 35% target cap, 2% assumed
annual risk-free, original costs/rebalancing and calculation code. These settings
are historical reference assumptions, not recommendations. The three completed
synthetic studies remain separately versioned; never overwrite their artifacts.

Covariance shrinkage, regime monitoring and rolling recalibration are **candidate
ideas only**, not approved model changes. Adaptation algorithms, new datasets and
further synthetic sweeps need separate authorization and predeclaration.

## Workflow: propose → preregister → validate → confirm → decide

| Checkpoint | Required action | Stop/reject/defer condition |
| --- | --- | --- |
| Proposal | State a falsifiable hypothesis, exact isolated change, rationale, expected failure mode and known limitation. Log every attempted variant, including abandoned ones. | No clear hypothesis, ineligible data, or a proposed change to historical claims: defer. |
| Preregistration | New candidate/version ID; seal code/config/environment, data/vintage manifests, metrics, comparisons, costs, all windows, pass/fail rules, multiplicity treatment and owner signoff before outcome access. | Unknown rights, unchosen criteria, missing hashes, chronology problems or no fresh reservation: blocked. |
| Synthetic/software checks | Deterministic tests of calculations, constraints, failure handling, leakage isolation and monitoring logic if separately authorized. Label outputs synthetic. | Software failure: reject or issue a new version and repeat checks, without rewriting the failed record. Passing does not establish market value. |
| Time-separated validation | Same eligible snapshot, information sets, evaluation dates and execution/cost assumptions for champion/challenger; both original objectives and equal weight retained. Record SPY when the empirical comparison requires it. | Predeclared fail rule, inadequate evidence or inconsistent comparisons: reject/defer. Any tuning makes these outcomes development evidence. |
| Fresh confirmation | Freeze the candidate after validation; evaluate once on a separately authorized, previously unseen period, with access recorded as consumption. | Reused/overlapping period, earlier performance peek or changed candidate/criteria: no clean confirmation claim. |
| Owner decision | Append reject/defer/adopt outcome, reasons, all reports and failure counts, consumed-period status, and separate owner signoff. Only predeclared criteria can support an adoption proposal. | A failed or mixed result need not produce a winner. New ideas require new IDs and another untouched confirmation reservation. |

Adoption is a **research designation**, not permission to trade, merge, publish or
deploy. Keep the original champion/results available even if a future reference
is adopted; any new champion lineage needs a separately reviewed protocol version.
No automatic p-value, Sharpe cutoff or numerical market-change threshold is chosen
here. Thresholds in proposals are explicitly **proposed** until selected and
sealed before seeing comparison outcomes. Do not select a rule after a favorable
result. Owner decisions must disclose multiple variants, repeated validation,
optional stopping and metric/window selection; descriptive ranges are not
confidence bounds or proof of superiority.

## Temporal information contract: three clocks

1. **Decision time:** the hypothetical/live time at which weights or a monitoring
   action could be chosen. Training, preprocessing, covariance/mean estimation,
   regime classification and all calibration must use only observations actually
   available then. Publication and revision availability matter as well as the
   observation date. Delayed releases cannot be backdated to their economic date.
2. **Snapshot/vintage time:** record retrieval time, publisher adjustment vintage,
   coverage, entitlement/retention and independent-verification references, plus
   immutable snapshot/manifest hashes. A later download of an old observation is
   not proof its revised value was known earlier. If retrieval follows decision
   time, require documented point-in-time vintage evidence. Future corporate
   actions/adjustments and later releases must not leak into historical decisions.
3. **Research time:** preregistration/signoff and earliest evaluation/access time.
   Freeze criteria before outcomes are inspected, even in retrospective research.
   A retrospective preregistration may occur after the historical calendar period;
   this does not make already inspected outcomes unseen. Log earlier access and
   classify it as development evidence. Do not confuse research time with the
   simulated decision clock.

Every rolling decision would need its own information-set proof and window/lag
manifest. The lightweight checker validates declared maxima for a single decision,
not a row-level pipeline. It cannot certify all rows or implement a rolling model.
Training/calibration must precede validation and confirmation. Reused development
observations must be disclosed; no future labels may enter fit/calibration.

A historical revision, newly entitled dataset or different adjustment vintage
creates a **new snapshot/version** and new report. Retain the old snapshot privately
only if licensed, its hash, old manifest/code/lockfile/command and old result.
Publish an explicit restatement/comparison if authorized; never silently replace
an earlier result or claim the new data were available at the old decision time.
Hashes identify bytes, not data correctness or permission; do not commit raw prices,
private contracts, secrets or reconstructible outputs without applicable rights.

## Detecting assumption changes without selecting on future returns

A candidate monitoring proposal must name its diagnostics (for example covariance/
correlation changes, volatility, covariance conditioning, missingness/adjustment
anomalies, concentration, cap incidence or weight instability), reference window,
as-of availability, cadence, minimum evidence and **proposed** thresholds. These
are possible diagnostics, not implemented detectors or claims of a regime change.

Preregister false-alarm/multiple-testing handling and a response: log/review,
quarantine suspect data, or propose a new version. A monitoring alert does **not**
prove structural change or authorize recalibration, strategy switching or holdout
inspection. Separate data-quality changes from market-assumption changes. Any
rolling/retraining schedule and lag rules must be fixed before evaluation. An
alert-triggered idea remains a challenger, evaluated through the same hierarchy.

## Confirmation reservations and irreversible consumption

- Synthetic illustration → time-separated validation → **fresh unseen confirmation**
  is the evidence hierarchy. No synthetic result settles the ETF question.
- The 006-v1 **2025+** reserve is not a pool for selecting challenger variants.
  Renaming an interval, shifting the start date, or viewing only part does not
  create fresh evidence. Never repeatedly tune on it and call it untouched.
- The original reservation is currently open-ended. The v1 checker therefore
  rejects any overlapping challenger reservation, including later subsets. **No
  future market dates are assigned here.** Establishing a distinct data horizon /
  confirmation allocation requires owner authorization and a new reviewed policy
  version; do not silently shorten or reallocate the original split.
- Before first performance access, append a consumption event and mark that
  reservation consumed. Log candidate, actor/evidence reference, access time and
  purpose. Charts, metrics, partial results, failed runs that exposed outcomes,
  negative findings and variant-selection feedback all count. Once consumed,
  never restore “untouched”; aborting a study does not undo access.
- A blind completeness/provenance audit with no performance/selection feedback
  is distinct from performance consumption under the existing safeguards. Never
  use that distinction to smuggle outcome-derived diagnostics into selection.
- Post-confirmation edits are exploratory. A revised candidate needs a genuinely
  new reservation; report the previous test and all comparisons honestly.

## Reviewable records and reproducibility

[decision-template.json](research/model-evolution/decision-template.json) is an
**unapproved proposal template**, not an actual preregistration or financial result.
It requires hypothesis/change/failure/limitation; monitoring rationale; metrics,
benchmarks, equal execution/costs; proposed/frozen pass/fail criteria and multiplicity;
training/calibration/validation/confirmation; temporal/vintage/rights evidence;
code/config/environment hashes, RNG streams and command; owner preregistration
signoff and requirements for a later outcome/signoff record. No numeric improvement
thresholds or actual confirmation dates are supplied.

[registry-v1.json](research/model-evolution/registry-v1.json) records the frozen
reference and original untouched reservation, **zero challenger decisions and zero
consumption events**. It fingerprints the existing calculations, dashboards,
synthetic artifacts/plans/findings, rights documents, brief and environment lock.
It does not contain data or performance. Do not edit it in place: append a new
registry checkpoint/file with predecessor path/hash, retain all prior decisions,
fingerprints and consumption events, and reference sealed decision/report artifacts.
Use new candidate IDs for revisions; keep rejected/abandoned reports too. For a
completed study append outcome/reasons and owner signoff to a **new sealed outcome
report referencing the original candidate ID**, not to an already hashed file.
Add its path/hash to the next registry’s `preserved_artifacts`; the `decisions`
list retains the unchanged candidate preregistration. Do not reuse a candidate
ID for a changed model or alter its sealed criteria. The current checker covers preregistration metadata
and registry continuity, not automatic outcome adjudication or adoption.

Eligibility distinguishes automated access, analysis, retention, independent
comparison, public derived outputs and raw redistribution. The last two must be
resolved for the intended disclosure, even if private analysis is separately
allowed. A checker PASS or supplied JSON is **not** a licence or source-policy
approval. No source is currently approved; the owner's inquiry remains pending.

## Offline checkpoint and limits

From the project directory, using the existing environment:

```bash
.venv/bin/python scripts/check_model_evolution.py
# Expected: structurally valid proposal; evaluation NOT cleared.
.venv/bin/python scripts/check_model_evolution.py --require-preregistered
# Expected exit 1: the template has no approved preregistration/rights/periods.
.venv/bin/python scripts/check_case_study.py
.venv/bin/python -m pytest -q
```

The standard-library checker reads metadata/local hashes only: required fields,
version IDs, declared chronology, rights/checklist references, period overlap,
consumption state and predecessor continuity. It never opens market data, calls a
provider, computes returns, fits a model, grants entitlement or touches the empirical
holdout. Unit tests use invented metadata and temporary text artifacts only.

Git review supplies the trusted historical anchor. Anyone able to rewrite the
checker, genesis registry and hashes could falsify a record; this is not a secure
append-only database. The checker cannot prove honest timestamps, unseen outcomes,
actual rights or adjustment correctness. Review manifests and evidence manually;
existing runtime source/holdout safeguards remain authoritative and unchanged.
Future policy changes must be explicit and versioned, not bypasses of those gates.

## Implementation verification

The initial checkpoint passed **41 metadata-only unit tests** and the full
**168-test offline regression suite**, including all 127 earlier tests. The case
study check passed **125 assertions / 42 local links and anchors**; all four local
links in this plan resolve. All **26 protected historical files** match the
reviewed baseline commit recorded in the registry. The proposal checker passes
structure/hash checks and correctly exits 1 with `--require-preregistered`.
No new research run or market-data request was performed.
