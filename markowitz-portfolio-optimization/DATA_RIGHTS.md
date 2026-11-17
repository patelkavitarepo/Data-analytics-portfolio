# Provider rights investigation · 2026-11-11

Status: **validation blocked**. Latest instruction:
[Holmes review, 6803628288](https://github.com/patelkavitarepo/Data-analytics-portfolio/pull/6#issuecomment-6803628288).
This is an evidence inventory, not a claim that any provider granted a licence.
No account created, subscription purchased, provider contacted or data published.

## Rights decisions are separate

| Source | Automated collection | Private educational/quant analysis | Public derived results / dashboard | Current decision / next action |
| --- | --- | --- | --- | --- |
| Yahoo / yfinance | Yahoo terms require express prior permission; no grant found | Personal-use notice does not resolve collection or intended-use rights | No applicable grant established; raw redistribution also unestablished | **Blocked**. Suspend collection and Yahoo performance; obtain actual provider permission or use another entitled source |
| Alpha Vantage | Documented authenticated API, conditional on applicable licence and endpoint entitlement | Terms cover qualifying individual private noncommercial research; user's eligibility/account not established | Not established for this public portfolio use | **Candidate only**. Adjusted daily API is premium; no key/subscription available or created |
| EODHD | Official API is documented; authorized plan/history required | Official terms/FAQ permit qualifying personal private quant research and private quality comparison | FAQ explicitly requires separate assessment for publication, including derived outputs | **Conditional private-use candidate**, not a public-project licence. Free history is only one year; full 2016–2024 access/eligibility and actual price basis remain unverified |
| Tiingo | API requires token/plan; website scraping not authorized by API documentation | Plan- and use-dependent | Derived-product restrictions apply | **Not an approved independent verifier**: current terms specifically restrict validating/reconciling another dataset; no exception established |
| Sharadar Fund Prices (SFP) | Documented authenticated API, subscription/eligibility required | Personal licence applies to individuals only; professional/institutional use excluded | Limited derived-output provisions, reconstruction restrictions, and separate confidentiality restriction on publishing evaluations | **Candidate only**. Correct fund-price product documented, but no entitlement, account or project/publication clearance established |

No candidate above is approved for this project's complete workflow. Private
analysis, retention, independent comparison, public aggregate statistics, daily
benchmark return downloads, rebased charts and raw-price redistribution can have
different permissions. A reversible return series or SPY wealth curve may expose
underlying data even without an absolute price column. Public GitHub logs and
artifacts count as disclosures; “educational” and “free dashboard” are not exemptions.

## Primary-source evidence inspected

Checked 2026-11-11 using public documentation research. References below are
provider publications; not unverified GitHub datasets or claims of granted rights.
Documents can change; GitHub documentation receipts add retrieval time, response
status and hash without reproducing documents or collecting prices.

### Yahoo

[Yahoo US terms](https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html),
Member Conduct item 2.b.9, restrict automated access/collection without
“express, prior permission”. The primary indexed text was readable; direct web
open returned status 999, so the GitHub receipt is a separate retrieval check.
No express permission for this project was located.
[yfinance's notice](https://ranaroussi.github.io/yfinance/) identifies the tool as
unaffiliated and points users to Yahoo's data terms; its personal-use statement
and software availability do not supply the missing permission. We therefore
cannot rely on past successful downloads to run Yahoo-based evaluation.

The previous 2,730-session audit remains a historical acquisition/coverage
observation, **not a permission finding**. The Actions acquisition job is now
disabled, chart endpoint probes removed, downloader blocked before vendor calls,
and stale live session caches discarded. No new Yahoo prices are acquired here.

### Alpha Vantage

[Terms](https://www.alphavantage.co/terms_of_service/), sections 2–3, condition
personal noncommercial access on the EULA and distinguish individual private
research from broader/commercial use. The
[official API documentation](https://www.alphavantage.co/documentation/#dailyadj)
documents raw closes, adjusted closes and split/dividend events; daily adjusted
history is a premium endpoint requiring a key. These are credible documented
API/private-research provisions, **not proof that this user/project qualifies or
owns the required entitlement**. Public portfolio distribution remains unresolved.
No account, demo workaround, key request or purchase was attempted.

### EODHD

[Terms](https://eodhd.com/financial-apis/terms-conditions), Personal and Commercial
Use, permit qualifying individual private analysis but restrict redistribution.
[Personal-use FAQ](https://eodhd.com/help/personal-use) explicitly discusses quant
research, private cross-provider quality checks, and separately treats publication
of derived statistics. [Storage FAQ](https://eodhd.com/help/storage) documents
private retention and reproducibility records, including after cancellation.
The [pricing/history table](https://eodhd.com/pricing) limits free history to one
year; the 2016–2024 experiment needs entitled longer history.

[EOD documentation](https://eodhd.com/financial-apis/api-for-historical-data-and-volumes)
distinguishes unadjusted `close` from split/dividend `adjusted_close` and warns
that adjustment levels are revised. The provider's terms/disclaimer also describe
indicative aggregated prices, not an exchange feed. Therefore we have not approved
it as an equivalent official-close reference or confirmed coverage of the eight
ETFs. This candidate needs both eligibility/entitlement and price-basis review;
it is not a recommendation to buy a subscription.

### Tiingo

[Terms](https://www.tiingo.com/tos/), last updated November 5, 2026, sections
1.6(a)–(c), restrict Starter/Trial retention, derived outputs and use to confirm
another dataset. Section 1.6(c) explicitly lists cross-dataset validation among
restricted uses. Thus a token or personal subscription cannot be assumed to
permit independent verification for this experiment. Its
[EOD documentation](https://www.tiingo.com/documentation/end-of-day) describes
split/dividend-adjusted closes and CRSP methodology, but technical suitability
is not permission. No Tiingo prices requested or account created.

### Sharadar

[Fund Prices documentation](https://sharadar.com/docs/funds) describes ETF/fund
history and separates `closeunadj`, split-adjusted `close`, and split/dividend/
spinoff-adjusted `closeadj`; it requires an authenticated API. SFP, rather than
an equity-only product, is the relevant candidate.
[Personal-use terms](https://sharadar.com/terms), sections 2, 4, 6, 8 and 10,
limit eligibility, reconstructible redistribution, publication of service/data
evaluations, and retention. Limited derived-work language is not blanket approval
for a professional portfolio dashboard or publication of data-comparison findings.
No account/entitlement, actual eight-ETF coverage or independent origin from any
chosen primary source has been established. No data requested.

## Evidence required to unblock

1. Identify intended user/entity and audience. Resolve whether the proposed use
   is qualifying personal research or public/professional portfolio work; do not
   infer eligibility from this repository being educational.
2. For both primary and independent reference sources, record applicable provider
   terms/contract, plan/endpoint entitlement, permitted automation, private
   analysis/retention and cross-provider comparison. Record public derived/raw
   distribution as separate granted/restricted/unknown decisions. Do not put
   secrets or private contract text into public git or Actions logs.
3. Obtain data only after those permissions are established. Use an approved
   GitHub execution path with bounded requests and secrets in approved settings,
   no public raw-price artifacts. Acquire **2016–2024 only** for this phase.
4. Complete [ADJUSTMENT_REVIEW.md](ADJUSTMENT_REVIEW.md), with actual independently
   obtained observations against the same audited snapshot, timestamp/hash and
   explicit cutoff. Existing single-point JSON checks are not a substitute for
   the new multi-date review. No source is currently approved in `source_policy.py`.
5. Only then enable an explicitly reviewed source policy and run fixed 2023–2024
   validation, at zero cost and the prespecified 10 bps/gross-notional sensitivity.
   Do not reveal or evaluate 2025+.

Buying a plan alone would not resolve all these gates. We have not contacted a
provider: licensing correspondence, account creation or purchase requires a
separate owner instruction. No speculative returns replace the missing evidence.
