# Engineering and analytical decisions

1. Existing repository is Python/Streamlit with project-local requirements and GitHub Actions. No Bottleneck implementation existed at inspection; no AGENTS.md was found. Isolate all work in this folder and a new workflow; preserve Optiver.
2. DataSF is the intended low-cost public path because no GCP identity or billing project is configured. Both metadata endpoints were network blocked. Never infer schema or 2025 coverage from prior Baltimore work. Initial checked-in state is evidence pending.
3. Source mapping is provisional, guarded by exact runtime metadata checks. Extraction orders by ID and validates uniqueness, counts and source update metadata. The public API is mutable: these checks reduce but do not eliminate snapshot uncertainty. No paid service is enabled.
4. Retain all eligible unresolved requests. Inconsistent closure evidence is not a successful closure. Creation/identity ambiguity fails publication.
5. Use within-month/category leave-one-agency-out comparisons. No valid peer overlap means no adjusted result. A ≥30 eligible per-side cell threshold reduces unstable screens; this is a preliminary choice, not a power analysis. Persistence uses the user's ≥3 months/≥90 requests and 10/15-point rules.
6. Store additive day-grain aggregates; raw records stay in process memory and are never committed. Duration histograms support flexible filtering and reproducible approximate quantiles with <1 day error. Pin dependencies; no visitor credentials or API requests.
7. Geography uses a neighborhood heatmap and coverage table. No verified geometries or point fields are available, so a map would be misleading. Reporting intensity is not a location-repeat failure measure.
8. Generated briefs label explanations as hypotheses. Recommendations are validation steps: verify work orders/outcomes, routing rules, status practices and subcategory complexity. Staffing and dispatch claims require separate evidence.
9. Synthetic records live only in test fixtures and temporary test directories; no demo data switch exists in production. A hash/provenance gate fails closed. This gate checks integrity, not authenticity against malicious falsification of metadata.
10. Deployment is prepared, not performed. Main remains untouched. PR review and Community Cloud publication remain user-controlled.
