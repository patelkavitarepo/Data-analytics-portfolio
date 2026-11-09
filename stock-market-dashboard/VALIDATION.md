# Validation record

Executed November 9, 2026 on Python 3.12/Linux using the versions captured in
`requirements-lock.txt`. These are observed local results, not claims about remote CI.

| Check | Observed result |
| --- | --- |
| `python -m market.download` | Downloaded the pinned original and reproduced 4,752 rows; source and subset SHA-256 checksums matched |
| `python -m market.ingest` | Loaded 4,752 validated rows into SQLite |
| `python -m pytest -q` | **14 passed** in 2.15 seconds on the final implementation |
| `CHROMIUM_EXECUTABLE=/usr/bin/chromium python tests/browser_smoke.py` | Passed: metrics, four tabs, download control, mobile viewport, no JavaScript page errors |
| Additional desktop/mobile browser capture | Passed; manually inspected desktop screenshot and corrected contrast and header spacing |
| `python -m pip check` | No broken requirements found |
| `git diff --check` | No whitespace errors |

The Streamlit AppTest exercises symbol selection, featured-stock selection state,
volatility-window changes, date filtering, and empty selection. Browser smoke uses
actual Chromium against the running server at port 8501. Viewports were 1440×1080
and 390×844. Screenshot: [dashboard](docs/dashboard.png).

During validation, the upstream CSV's symbol column was found to be named `Name`
(case-sensitive); the reproduction pipeline handles it explicitly. Visual review
found low metric contrast in the initial theme, which was corrected. Streamlit's
usage telemetry attempted a write to a read-only home directory in the sandbox;
telemetry is now disabled in project configuration and the server was restarted.
Final browser runs completed without application exceptions or JavaScript errors.

GitHub Actions is configured for Python 3.11 and 3.12. Those remote matrix results
are separate from this local run. The local environment tested Python 3.12 only.
