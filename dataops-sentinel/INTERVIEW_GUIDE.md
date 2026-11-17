# Interview guide

## Thirty-second explanation

> DataOps Sentinel is an offline Python and Streamlit portfolio MVP for checking
> a fictional operations feed. It validates CSV records, separates rejected
> business-rule failures from advisory outliers, and stores the result in a
> transactional SQLite audit. The committed example has known injected
> anomalies and a separate truth manifest, so the demo can explain each finding
> and reconcile every input row. Exact-file reruns reuse the audit result rather
> than silently counting the records again. It is an educational MVP, not a
> production data platform.

## Two-minute demonstration

1. Start the app using the commands in [README.md](README.md), then load the
   fictional demo data. Point out its **synthetic** label before discussing
   any numbers.
2. Reconcile the example: **50 input = 41 accepted + 9 rejected**. The one
   advisory is an accepted row, not a fourth cohort. These are the fixture's
   expected counts; refer to the recorded test evidence for observed execution.
3. Inspect rows 43 and 44. Both share `SYN-DUPLICATE`; both are rejected because
   the application cannot choose which conflicting business record is correct.
4. Inspect row 50, `SYN-0050`, with quantity `500`. It meets the hard rules but
   differs from the baseline, so its advisory asks for review while retaining
   it in the clean dataset. Suspicion does not establish a data error.
5. Run the same source again. Explain the reused run and unchanged stored row
   counts. Download the quality report and accepted dataset, and identify the
   audit's content hash and row-level reasons.

## Duplicate and idempotency walkthrough

The source content hash identifies the **exact input bytes**. Processing the
same file under the same validation rules reuses its stored run. This avoids
creating a new set of false duplicate findings or inflating accepted totals.
A changed filename does not change the bytes' identity; a byte change does.

Business IDs serve a different purpose. Within one file, every member of a
repeated nonblank ID group is rejected. Across different source files in the
same database, an ID already accepted is rejected with an explicit finding.
The MVP does not overwrite an accepted business record or implement updates.
The ID scope is the current SQLite database; it is not a global shared service.

This policy means a reformatted file can be a new source while containing
already accepted IDs. That is intentional and should be explained to a reviewer.
For a real update workflow, a designer would need explicit versioning and
conflict-resolution requirements.

## Anomaly versus error

Hard validation covers required values, business-ID uniqueness, timestamps,
allowed categories/statuses, integer quantity bounds, and status/quantity
consistency. A row with any hard finding belongs to the rejected cohort.

The quantity advisory runs on otherwise accepted rows when there are at least
eight. Its robust score uses the median and median absolute deviation (MAD),
with a minimum MAD of one, and flags scores above `3.5`. This is a transparent
heuristic, not a trained model or proof of incorrectness. It can flag a legitimate
large operation and miss unusual records in other fields.

The truth manifest labels deliberately injected examples independently of the
detector. False positives and false negatives describe agreement with those
labels on this fixture. They do not estimate performance on real operations
data. Hard-error and advisory evaluations must remain separate.

## Questions a recruiter or reviewer might ask

| Question | Answer to demonstrate in the code |
| --- | --- |
| Why SQLite? | It provides local SQL persistence, uniqueness constraints, and atomic transactions without a service or credentials. It suits this single-instance MVP. |
| Why pandas? | It supports tabular processing while the ingestion, validation, persistence, and reporting modules keep separate responsibilities. |
| What happens if a write fails halfway through? | The transaction rolls back instead of leaving a partial run. Show the rollback test and its actual result. |
| What is the difference between a file hash and a business ID? | The hash supports replay identity; the business ID enforces record identity across accepted data in the same database. |
| What does a naive timestamp mean? | A timestamp without an offset is assumed UTC. Offset-aware timestamps are normalized to UTC; this assumption must be visible to the user. |
| What makes an outlier a valid row? | A surprising quantity can still satisfy every business rule. Its advisory leaves it accepted and explains why review might be useful. |
| How do you know your detector works? | Inspect the tests and recorded outputs, then compare the fixture's row-level results with the separate truth manifest. Do not extrapolate from synthetic labels to real-world accuracy. |
| Can the app work offline? | The demo and CSV ingestion need no external source. The JSON/API adapter is tested using supplied mock responses, not a required live API. |
| What happens to uploads in a hosted demo? | Each browser session needs an isolated audit store. Ephemeral session storage is not durable backup, authentication, or a production retention policy. |
| What would you improve next? | Start with requirements for authenticated use, retention, schema/rule version migration, update semantics, operational monitoring, and representative evaluation data. |

## Authorship and review status

The issue requests the attribution **“AI-assisted implementation; human-reviewed research/design decisions”**.
In this project, that phrase describes the intended
portfolio review process; it does **not** certify that a candidate or another
human has already reviewed the implementation or design.

The implementation was generated with AI assistance. The candidate should
personally run the demo and tests, read the ingestion/validation and transaction
paths, inspect the synthetic labels, and record what they reviewed before
claiming personal review or ownership of those decisions. In an interview,
distinguish code personally reviewed and understood from AI-generated code
that still needs review. Do not claim independent authorship, real business
outcomes, or test results that were not observed.
