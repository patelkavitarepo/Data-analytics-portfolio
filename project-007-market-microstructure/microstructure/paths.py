"""Enforce ignored local-only output destinations for provider-derived reports."""
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_ARTIFACT_ROOT = (PROJECT_ROOT / "artifacts").resolve()


def safe_report_output(path):
    """Only JSON report paths inside this project's ignored artifacts directory.

    Resolve symlinks before accepting the path; code is not an entitlement grant.
    """
    dest = Path(path).expanduser().resolve()
    if not dest.is_relative_to(LOCAL_ARTIFACT_ROOT) or dest == LOCAL_ARTIFACT_ROOT:
        raise ValueError(
            "Output must be within project-007-market-microstructure/artifacts/ "
            "(ignored local-only reports)"
        )
    if dest.suffix.lower() != ".json":
        raise ValueError("Only .json local reports are accepted")
    return dest
