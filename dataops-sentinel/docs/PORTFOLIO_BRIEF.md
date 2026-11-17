# DataOps Sentinel portfolio brief

Prepared for a computer science career-fair conversation on **November 18, 2026**.
This brief describes the offline, synthetic portfolio MVP; human review and owner
acceptance remain pending.

## Project and evidence

A fictional operations feed can contain missing values, duplicate business IDs,
invalid dates, impossible quantities, and inconsistent statuses. DataOps Sentinel
shows how a small Python application can explain those failures, retain an audit,
and produce a clean dataset without hiding suspicious but valid records.

Its modular Python architecture separates schema and bounded CSV/JSON ingestion,
pandas validation, SQLite persistence, reporting, and the Streamlit UI/CLI. Source
SHA-256 hashes identify exact input bytes. Transactional SQLite writes retain
source provenance, runs, accepted/rejected rows, and findings. Exact-input replay
under the same rule version reuses the saved run; business IDs already accepted
in that database are rejected in later different files.

The committed fixed-seed example has **50 input rows = 41 accepted + 9 rejected**.
One accepted row has an advisory; it is included in the 41, not an additional
cohort. A separate, hash-bound truth manifest labels every synthetic row.
Regeneration and independent fixture reconciliation are documented in the
[adversarial review](ADVERSARIAL_REVIEW.md).

Checkpoint 3 reran **214 pytest cases, all passing in 24.83 seconds**, on
Linux/Python 3.12.14, with Ruff and compilation checks also passing. Tests cover
validation, exact replay, cross-file duplicates, rollback, timezone handling,
mocked API failures, report safety, and UI behavior. A separate automated browser
walk passed 14 acceptance checks; this did not complete human acceptance.
The [checkpoint results](CHECKPOINT_3_RESULTS.md) record commands, outputs and
verification boundaries. Test count is not business impact, a
coverage percentage, or an estimate of real-world detection accuracy.

## Thirty-second explanation

> DataOps Sentinel is an AI-assisted Python and Streamlit MVP for checking a
> fictional operations feed. It explains validation failures, keeps a transactional
> SQLite audit, and reuses exact-file reruns. Its example reconciles 50 rows into
> 41 accepted and nine rejected, with one accepted advisory. Separate truth labels
> and automated tests make results reviewable. It runs offline; personal human
> code review remains pending.

## Two-minute technical demonstration

Prepare the local environment using [README.md](../README.md) before the fair;
the demo itself needs no network or credentials. Use a fresh session audit so
earlier accepted IDs do not change the fixture's validation context.

| Time | Demonstration and explanation |
| --- | --- |
| 0:00–0:15 | Identify the feed as entirely synthetic and the app as an educational MVP. State the problem: explain invalid records while preserving an audit. |
| 0:15–0:40 | Click **Load synthetic demo**. Reconcile **50 = 41 + 9** and identify the single advisory as part of the accepted cohort. |
| 0:40–1:05 | Compare duplicate-ID rows 43/44, both rejected, with row 50 (`SYN-0050`, quantity `500`), which remains accepted with an advisory. Suspicion does not establish an error. |
| 1:05–1:25 | Load the same demo again. Show the saved-run reuse indicator and explain exact-byte hash identity versus business-ID identity. Replay adds no new accepted rows. |
| 1:25–1:45 | Download the JSON report and accepted CSV. Point to source provenance, row-level explanations, and the retained advisory record. Refer to the recorded test evidence. |
| 1:45–2:00 | Name the ingestion → validation → SQLite → reporting seams. Close with the local/ephemeral storage limits and AI-assisted authorship; personal human review is still pending. |

## Résumé wording and contribution boundaries

**Editable résumé bullet, conditional on the owner checking the evidence and
being able to explain the stated direction and validation requirements:**

- Directed requirements and requested validation for an **AI-assisted Python/Streamlit
  data-quality MVP**, demonstrated by **50 synthetic records reconciled into
  41 accepted and 9 rejected, with 1 accepted advisory**, and **214 automated
  tests recorded passing**, by specifying modular processing, transactional
  SQLite auditing, and deterministic replay.

This wording describes requirements and validation direction. It does not claim
independent implementation, personal test execution, human code review, real
operational savings, or empirical accuracy. Update the test evidence if a later
run differs; do not reuse the historical timing as a new result.

The evidence-supported owner contribution at this point is task direction:
requesting the project, its scope and constraints, validation, and reviewable
documentation. The implementation and software review were AI-assisted. No
record here establishes that the owner personally ran commands, read particular
modules, approved the design, or completed human acceptance. Those contributions
can be claimed only after the actual steps are completed and recorded.

The requested attribution **“AI-assisted implementation; human-reviewed research/design decisions”**
describes the intended review process. Its human-review portion is pending; it
must not be presented as completed. See [INTERVIEW_GUIDE.md](../INTERVIEW_GUIDE.md)
for the fuller distinction between AI-generated code and personally reviewed code.

## Limits to explain plainly

- The feed and truth labels are constructed examples. The advisory heuristic can
  flag legitimate values or miss unusual ones; synthetic agreement does not
  establish general accuracy.
- SQLite is local and single-instance. Session storage is ephemeral; there is no
  durable shared service, authentication, retention policy, or migration tool.
- Streamlit session-database isolation does not make known download URLs private
  or immediately revocable. Use fictional, non-sensitive inputs only.
- A live API client, production deployment, formal accessibility/security audit,
  empirical evaluation, and multi-user load certification are outside the
  verified MVP. No merge, deployment, or release is asserted by this brief.

## Owner review and contribution log — fill only after doing the work

Leave entries blank until each action actually occurs. Record what was personally
done, what was understood or changed, and the evidence. Do not copy AI actions
into the owner's contribution column.

| Date | Personally completed action/module | Command, artifact, or review evidence | What I understood or contributed | Remaining questions |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

This blank log records no owner acceptance or completed human review.
