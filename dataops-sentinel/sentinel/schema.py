"""The small versioned data contract shared by ingestion and validation."""

COLUMNS = (
    "record_id",
    "event_timestamp_utc",
    "location",
    "category",
    "quantity",
    "status",
)
MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 10_000
RULESET_VERSION = "1"
CATEGORIES = frozenset({"delivery", "maintenance", "support"})
STATUSES = frozenset({"pending", "completed", "cancelled"})
