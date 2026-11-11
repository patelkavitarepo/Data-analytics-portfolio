# Independent adjustment review plan · 006-data-review-v2

Predeclared 2026-11-11, **before any real validation performance is computed**.
Status: **not executed; no legitimate independent adjusted-price observations in
hand**. This replaces the sufficiency of the old one-price-per-ETF checklist.
It changes data verification, not the frozen portfolio methodology.

## Fixed window and observation selection

- Request only 2016-01-01 through **2024-12-31**, never 2025+ for this review.
- Normal controls for **every ETF**: **2023-02-15** and **2024-02-15**, plus the
  preceding and following XNYS sessions. Independently confirm there is no action
  in each control window; if an action is found, report a non-normal control and
  stop for a documented plan amendment before reading any performance.
- For each distributing ETF, select the **first ordinary cash distribution with
  issuer-confirmed ex-date on/after March 1 in 2023**, and the same rule in 2024.
  Freeze exact dates from the issuer records **before looking at price differences**.
  Request ex-date and its preceding/following sessions. Do not choose easier dates
  because discrepancies are smaller.
- Review issuer/provider split and reverse-split histories across **2016–2024**.
  If an event exists, add the first verified event and its adjacent sessions;
  if none exists, record the checked source and coverage, not an invented split.
- GLD: issuer's [December 2023 FAQ](https://www.spdrgoldshares.com/media/GLD/file/GLD-FAQs-December-2023.pdf)
  states that the trust does not generate income. Do not invent cash distributions.
  Verify the no-distribution finding and split history across the actual review
  interval; use the two normal controls. Gold sold for expenses is not a cash
  dividend or ETF market-price total return.

## Per-asset request register

The dates below are **predeclared candidate request dates, not issuer-verified
ex-date findings**. They must be reconciled to the fixed selection rule above.
An unreconciled date leaves the asset blocked. No dividend amount or adjusted
price has been copied from a search snippet into this plan.

| ETF | Candidate 2023 / 2024 ex-date windows | Issuer action-reference location | Verified equivalent adjusted-price reference |
| --- | --- | --- | --- |
| SPY | 2023-03-17 / 2024-03-15, adjacent sessions | [State Street SPY distributions](https://www.ssga.com/us/en/individual/etfs/spdr-sp-500-etf-trust-spy) | Not obtained |
| QQQ | 2023-03-20 / 2024-03-18, adjacent sessions | [Invesco QQQ](https://www.invesco.com/qqq-etf/en/about.html); obtain archived distribution record | Not obtained |
| IWM | 2023-03-23 / 2024-03-21, adjacent sessions | [iShares IWM distributions](https://www.ishares.com/us/products/239710/ishares-russell-2000-etf) | Not obtained |
| EFA | 2023-06-07 / 2024-06-11, adjacent sessions | [iShares EFA distributions](https://www.ishares.com/us/products/239623/ishares-msci-eafe-etf) | Not obtained |
| EEM | 2023-06-07 / 2024-06-11, adjacent sessions | [iShares EEM distributions](https://www.ishares.com/us/products/239637/ishares-msci-emerging-markets-etf) | Not obtained |
| TLT | 2023-03-01 / 2024-03-01, adjacent sessions | [iShares TLT distributions](https://www.ishares.com/us/products/239454/ishares-20-year-treasury-bond-etf) | Not obtained |
| GLD | No dividend date asserted; normal controls and split-history check | [Issuer 2023 FAQ](https://www.spdrgoldshares.com/media/GLD/file/GLD-FAQs-December-2023.pdf) | Not obtained |
| VNQ | 2023-03-24 / 2024-03-22, adjacent sessions | [Vanguard VNQ distributions](https://investor.vanguard.com/investment-products/etfs/profile/vnq#distributions) | Not obtained |

**Normal dates for all eight: 2023-02-15 and 2024-02-15.** Issuer links identify
intended authoritative action sources, not proof that their historical tables,
automated access rights or exact candidate dates have already been verified.
The GLD FAQ observation is issuer-supported; it does not prove every historical
corporate-action entry or provide an independent adjusted-price series.

## Equivalent bases before numeric checks

For each source record security identity/class, USD currency, session date/timezone,
venue and definition of close (official auction / consolidated last / midpoint),
raw versus split-only versus dividend-adjusted fields, distribution types,
ex-date versus pay date, split-factor orientation and reinvestment convention.
Record retrieval timestamp, vendor revisions and source/entitlement provenance.
Independence requires a distinct underlying provider/issuer reference, not Yahoo
through another Python wrapper or a GitHub mirror with unknown lineage.

NAV, an issuer NAV total-return chart, a benchmark index, and exchange-traded
market-price returns are **different bases**. Issuer distributions can corroborate
an action without validating adjusted ETF closes. A market-price return based on
bid/ask midpoint is also not automatically the closing-trade return. A basis
mismatch is a blocker, not a failed optimization or an invitation to substitute NAV.

Adjusted price levels can have different terminal scales or be revised for later
distributions. Prefer daily adjusted-return and adjustment-factor comparisons.
For the level diagnostic normalize each independently obtained adjusted series
by its own **2024-12-31 adjusted close**, after confirming identical action and
reinvestment conventions. Do not compare a fresh scaled price directly to an
older differently anchored snapshot. This common historical anchor avoids using
holdout prices. Keep original entitled snapshots and normalization metadata
privately only if the terms allow retention.

## Predeclared tolerances (do not tune to the observed performance)

| Check | Rule |
| --- | --- |
| Security, currency, session, action date/type | Exact match; documented comparable closing convention required |
| Independently reported same-basis raw close | Absolute difference ≤ max(USD 0.01, 0.01% of reference close) |
| Cash distribution per share | Difference ≤ max(USD 0.000001, half the reference's last published decimal unit), after matching split/share basis |
| Split-factor orientation/value | Same declared definition; absolute difference ≤ 1e-8 |
| One-session adjusted simple return | Absolute difference ≤ 0.0002 (2 basis points) |
| Same-anchor normalized adjusted level | Relative difference ≤ 0.005 (0.5%; inherited diagnostic ceiling) |
| Missing/duplicate/nonpositive/session-misaligned inputs | Zero permitted in the required interval |

For each window compare raw-close movements, adjustment-factor changes and
independently reported actions. Apply the **documented provider convention** for
cash reinvestment and splits, including simultaneous actions. Do not assume that
`(close + dividend)/previous_close` equals every vendor's adjusted-close return;
reinvestment timing and backward-adjustment methods can differ. Explain any
material convention difference before declaring equivalence. Passing one number
is insufficient. A pass requires all eight assets and all prescribed windows,
rights and coverage checks, and a completed split-history review.

## Evidence packet and current blockers

For each asset retain privately (where licensed): exact source URLs/record IDs,
source lineage, actual selected dates, raw/adjusted observations, distribution and
split references, both entitlement decisions, timestamp, common anchor,
normalization method, errors, tolerances and disposition. Bind the completed
review to the **same price snapshot hash, eight tickers and as_of 2024-12-31**.
Do not publish price excerpts or potentially reconstructible benchmark paths.

Current dispositions: **0 of 8 completed**. No independent adjusted-price source
with established project entitlement is available. Candidate ex-dates and absence
of split events have not been certified from archived issuer records. Nasdaq's
prior page probe was 403, which neither proves that all independent sources are
unavailable nor gives permission to use another source. Tiingo's dataset-
verification restriction prevents treating its standard personal API as a free
cross-check. Alternative documented providers still need account/entitlement,
use classification and coverage/closing-basis verification.

Only after the evidence packet is actually completed may the source-policy gate
be reviewed and explicitly enabled. Old template booleans, synthetic fixtures,
HTTP 200 and the legacy numerical consistency checker cannot enable it.
No portfolio validation or holdout performance has been computed for this plan.
