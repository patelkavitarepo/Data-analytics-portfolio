# Synthetic data provenance

All records in `data/synthetic_operations.csv` are fictional. Locations are
named **Synthetic Hub Amber**, **Synthetic Hub Birch**, and **Synthetic Hub
Cobalt**; identifiers use the `SYN-` prefix. No customer records, names, PII,
external API data, or actual business outcomes were used.

`sentinel/synthetic.py` uses Python's standard-library `random.Random` with
fixed seed **1729**, a fixed starting time of **2026-01-05 09:00 UTC**, and
15-minute intervals. It creates 40 baseline rows and appends 10 deliberately
constructed rows. Categories are `delivery`, `maintenance`, and `support`.
Baseline quantities range from 8 to 12 and baseline statuses are `completed`
or `pending`.

The committed CSV contains 50 data rows, excluding its header. Its exact
UTF-8/LF bytes have SHA-256:

```text
2dd1cb18a89f0f4ee639595d0e5eb75ea01fc5c9cefc94296307aa68939b0b21
```

## Independent truth labels

`data/truth_manifest.json` contains the seed, source hash, expected counts,
and a label for **every** data row. Each label gives the one-based data-row
number, business ID, hard-error flag, advisory flag, and reason. Data-row
numbers exclude the CSV header, so data row 41 is physical CSV line 42.

The manifest records the deliberately injected truth. Production validation
must not consume those labels to decide which records to flag. It is used
separately to evaluate results for this exact synthetic source.

| Data row | Business ID | Deliberate change | Truth label |
| --- | --- | --- | --- |
| 1–40 | `SYN-0001`–`SYN-0040` | Fictional baseline rows | No hard error or advisory |
| 41 | `SYN-0041` | Blank required `location` | Hard error |
| 42 | blank | Blank required `record_id` | Hard error |
| 43 | `SYN-DUPLICATE` | Repeated ID paired with row 44 | Hard error |
| 44 | `SYN-DUPLICATE` | Repeated ID paired with row 43 | Hard error |
| 45 | `SYN-0045` | Impossible timestamp `2026-02-30T09:00:00Z` | Hard error |
| 46 | `SYN-0046` | Quantity `-3` | Hard error |
| 47 | `SYN-0047` | Quantity `10001`, above the allowed maximum | Hard error |
| 48 | `SYN-0048` | `cancelled` status with positive quantity `10` | Hard error |
| 49 | `SYN-0049` | Unsupported status `mystery` | Hard error |
| 50 | `SYN-0050` | Unusual but permitted quantity `500` | Advisory only; accepted |

Expected reconciliation from the constructed labels:

```text
50 input rows = 41 accepted rows + 9 rejected rows
1 accepted row has an advisory; it remains part of the 41 accepted rows.
```

These are fixture expectations, not a substitute for running the application.
Measured execution and test results belong in the project's test evidence.
Even perfect agreement on these deliberately constructed labels would not
demonstrate accuracy on an empirical dataset.

## Reproduce and inspect

From the repository root:

```bash
cd dataops-sentinel
python -m sentinel.synthetic --output-dir data
```

The command writes the named CSV and manifest in `data/` and prints the seed,
content hash, and expected counts. The generator uses no network access and
does not include a changing generation timestamp. With the documented seed,
regeneration should leave the committed artifacts unchanged:

```bash
git diff --exit-code -- data/synthetic_operations.csv data/truth_manifest.json
```

A different seed can create another baseline for exploration, but the default
committed manifest and its hash apply only to the committed source. Do not
attach those labels to a user upload or another dataset.
