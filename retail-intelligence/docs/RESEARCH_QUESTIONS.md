# Research log — Project 003

## R001 — What is a valid sales transaction?

**Status:** open, not yet tested.

- A row represents a line item, not necessarily a distinct order or customer.
- UCI documents `C`-prefixed invoice codes as cancellations.
- Investigate negative quantities, refunds, zero-priced items, postage, non-merchandise codes, and duplicate records.
- Do not define revenue solely as `Quantity * UnitPrice` without explaining exclusions, cancellations, and the monetary meaning of the resulting figure.

## R002 — Are monthly or geographic differences meaningful?

**Status:** open, not yet tested.

- Check temporal completeness, seasonality, geography, and the effect of major wholesale orders.
- Avoid attributing trends to marketing or customer behavior without corroborating data.

## R003 — What can customer IDs tell us?

**Status:** open, not yet tested.

- Quantify missing customer IDs before estimating repeat-purchase rates or RFM segmentation.
- Document that anonymous transactions cannot confidently be attributed to individuals.

## Evidence discipline

Separate source metadata, observed audit counts, assumptions, and business interpretations. Record every cleaning/filter decision and its row impact before using it downstream. No dashboard or final narrative is approved yet.
