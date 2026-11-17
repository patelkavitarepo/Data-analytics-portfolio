"""Evidence checkpoint, separate from financial/model parameters.

No source has passed the latest Holmes rights + action-date review. Do not
register a source merely because a client, endpoint, checkbox or JSON is usable.
A future approval needs provider-scope evidence and completed ADJUSTMENT_REVIEW.md
checks against the exact audited snapshot. Keep credentials/private grants out of git.
"""


def require_approved_source(record, audit):
    raise ValueError('SOURCE EVIDENCE BLOCKED: no source has yet passed the provider-rights and independent action-date review. A supplied checkbox or review JSON cannot grant rights. See DATA_RIGHTS.md and ADJUSTMENT_REVIEW.md.')
