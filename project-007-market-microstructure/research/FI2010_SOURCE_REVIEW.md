# Project 007 — FI-2010 source admission and research limits

**Reviewed November 11, 2026; source access and published license independently confirmed.** This replaces the earlier preliminary source search.

## Canonical dataset

- Ntakaris, Magris, Kanniainen, Gabbouj & Iosifidis, *Benchmark Dataset for Mid-Price Forecasting of Limit Order Book Data with Machine Learning Methods*, *Journal of Forecasting* (2018), DOI https://doi.org/10.1002/for.2543.
- FI-2010 records five Nasdaq Nordic stocks over ten trading days in June 2010. The NoAuction/DecPre version consists of 149 rows: 144 publisher-processed features followed by five supplied 3-class future-mid-price target rows, with sampled-observation horizons 1, 2, 3, 5 and 10.
- Original research catalog: https://etsin.fairdata.fi/dataset/73eb48d7-4dbc-4a10-a52a-da745b47a649.
- **Official publisher metadata read live:** https://metax.fairdata.fi/v3/datasets/73eb48d7-4dbc-4a10-a52a-da745b47a649. Access type is Open, license CC BY 4.0. An independent legacy metadata endpoint reported the same. See [source probe](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43092037095).
- DeepLOB research authors' publicly distributed archive: https://github.com/zcakhaa/DeepLOB-Deep-Convolutional-Neural-Networks-for-Limit-Order-Books/tree/master/data. Their notebook explicitly links to the official original source and alternative public copy.

## Acquired archive and limits

The source runner downloaded 56,278,154 bytes. ZIP SHA256 `7a5564290a504bdc104dccaf44aa6c0b3857bf1db6b0517b9b88577c2def3e5f`. Archive contains four exact text files: CF7 training, day-eight test CF7, day-nine CF8, day-ten CF9. Compressed archive contents total 940,100,600 uncompressed bytes. The actual FI-2010 original dataset publisher's checksum was not accessible for independent binary comparison. Reproducibility of **this research copy** is established, but original byte equivalence **is not**.

Only train CF7 and day-eight test CF7 were opened; no day-nine/ten data consumed. The benchmark matrices passed numeric/form checks and produced a real historical **constant-prior-only baseline**, documented in [EMPIRICAL_DAY8.md](EMPIRICAL_DAY8.md). A second independent calculation read publisher label rows directly from the ZIP and exactly reproduced the counts and score fractions. [Verification run](https://github.com/patelkavitarepo/Data-analytics-portfolio/actions/runs/43093046158).

## Scientific limitations

- The publisher's **precomputed** labels were checked for allowable classes, not independently derived from a raw order event stream.
- Whether late training labels incorporate subsequent-day prices has not been established. Therefore this is an exploratory evaluation, not certified absence of future-label leakage.
- The files contain 144 publisher-processed numeric features, NOT raw exchange messages or elapsed timestamps. Cannot derive truthful absolute spread, queue priority, original order-flow imbalance, slippage or execution P&L.
- Observations are serially correlated and overlapping; an IID uncertainty estimate would be inappropriate. One 2010 day does not establish a contemporary market regime.
- Published CC BY 4.0 metadata supports attribution-bearing derived discussion, but does not erase independent checks of input version, numerical semantics, and published-source attribution. The original bytes remain outside the repo.

## Before predictive modelling

1. Obtain the human lead's interpretation of train/day-eight distribution change; keep its causes unproven.
2. Investigate precomputed label-boundary leakage and evaluate feasible trimming/purging policies without consulting days nine/ten.
3. Predeclare a single input feature family, a simple model and a strict training-only parameter policy. Retain the constant prior as the frozen day-eight baseline.
4. Keep days nine and ten reserved until a separately approved evaluation.

LOBSTER samples have separate unresolved rights and remain a distinct engineering track.
