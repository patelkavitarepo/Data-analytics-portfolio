# Official-data access and evidence status

Checked 2026-11-09 in the managed cloud environment.

- No local competition files were found in the accessible workspace.
- No Kaggle-prefixed credential environment variable names were present; no
  `kaggle.json` was present in the standard inspected locations. Secret values
  were not requested, printed, or committed.
- The selected environment reported restricted, enforced network access and no
  configured secrets. `www.kaggle.com` was absent from its permitted destinations.
- A normal HTTPS request to the official competition API list endpoint failed at
  the proxy with `CONNECT tunnel failed, response 403` (curl exit 56, HTTP 000).
  This is an environment network denial, not proof that Kaggle denied this user's
  competition permissions. No download occurred.
- Browser/search access exposed indexed official documentation, not local dataset
  bytes. JavaScript pages did not render readable body text directly; source
  excerpts were retrieved through search. No mirrors, community datasets, or
  leaderboard result tables were substituted for the official dataset.

## Consequence

**No official rows have been analyzed. No empirical charts, fitted relationships,
RMSPE scores, stock counts, or dataset-wide missingness rates are claimed.** The
charts produced in automated tests use explicitly labeled mathematical fixtures
inside a temporary test directory; they are not committed or presented as research.

## Authorized routes

1. **Private Kaggle notebook:** the lead signs in, accepts the competition's current
   terms, attaches the official competition data, and runs the research code inside
   that notebook. The expected input root is
   `/kaggle/input/optiver-realized-volatility-prediction`. Keep notebook outputs
   private until publication permissions are reviewed.
2. **Local/private staging:** the lead downloads the official files after accepting
   the competition terms and makes them available in private storage accessible to
   the research runtime. Required initial inputs are `train.csv`,
   `book_train.parquet/stock_id=*/...parquet`, and
   `trade_train.parquet/stock_id=*/...parquet`.
3. **Managed authenticated download:** configure Kaggle/network access and secrets
   through environment settings, never in chat or Git. This runtime does not expose
   a tool for proposing network-policy edits; the settings flow is required. A
   network grant alone does not establish competition permission or rule acceptance.

Do not redistribute raw data or derived stock-level observations on the public
portfolio. Inputs, artifacts, and credentials are ignored by the project-local
`.gitignore`. Ignore rules are a guardrail, not a substitute for reviewing staged
files. The user should review the current official rules; they were not fully
readable during this session, so permission to publish derivatives is not assumed.
