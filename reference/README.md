# reference/

Persistent project context and provenance material — not code or data to run against, but background needed to understand the project's history and standing methodological rules.

| File | Purpose |
|---|---|
| `haldetect_starthere_2026-08-10.md` | Full project context / onboarding doc. Read this first if `../CLAUDE.md`'s summary isn't enough. |
| `haldetect_session_handoff_2026-08-20.md` | Latest session handoff notes. |
| `haldetect_decision_log__Evaluating_feasibility_of_hallucination_detection_project.md` | Decision log for the project's feasibility evaluation. |
| `haldetect_technical_config__Evaluating_feasibility_of_hallucination_detection_project.md` | Technical configuration notes, including the CITATION verifier's known-broken status. |
| `haldetect_fingerprints.md` | The version-identification fingerprint table (row counts, grep markers) used throughout this reorganization. **Two of its claims were found not to hold against actual file content** during the 2026-08-21 audit — see `../WORKSPACE_AUDIT.md` sections 2 and 7 for the specifics (TEMPORAL's "patent office" marker isn't actually mutually exclusive with the v2 retry logic; the negatives CSVs' actual row counts don't match what this doc describes). Still useful as a starting heuristic, but always verify against the file itself. |

This folder holds only the 5 handoff/context docs — no claim data. (`haldetect_claims_20260731_175241.csv`, the raw pre-gold-labeled Batch 3 run, was briefly misfiled here and has been moved to `../archive/csvs/`, where the rest of the claims-data lineage lives.)

## The one rule that matters most
**Never trust a filename, a suffix like `(1)`/`(2)`/`(3)`, or a doc's description of a file — always verify row counts, `mtime`, and specific content markers directly.** This was the single biggest source of wasted effort across the project before this reorganization, and it's why `../WORKSPACE_AUDIT.md` exists.
