# Feedback to Codex

## F1: Biggest avoidable friction: staged public-task tests have no supported repository-root contract

symptom: A test using `reviewer_support.find_root()` passed in the full checkout but failed in `review.py task-tests`, because that stage intentionally carries the assigned source, raw ARC data, and runtime while omitting the canonical catalog ledger required by the helper.

evidence: The task-local tests now locate the nearest ancestor containing the raw challenge file, raw solution file, and `shared/runtime`; the final staged receipts pass with zero source drift at `checks/public_eval_21897d95-tests-final/result.json` and `checks/public_eval_0934a4d8-tests-final/result.json`.

suggested change: Give staged tests an explicit `ARCPUZZLES_REPO_ROOT` (or a supported helper whose contract matches the staged closure) so task authors do not need to reproduce root-discovery logic.

## F2: Public-authoring exports cannot use the standard public preview path

symptom: The standard export flow is qualification-oriented, while a public-evaluation creation has only an authoring `preflight.json`; producing one-query privacy evidence therefore required a bespoke source-bound audit/export helper.

evidence: `checks/_tools/audit_public_creation.py` generated the retained exports, and the independent checks are `checks/public_eval_21897d95/public-export-check.json` and `checks/public_eval_0934a4d8/public-export-check.json`.

suggested change: Add a `--public-preflight` mode to the standard preview/export command that preserves the explicit unapproved authoring status while reusing its identity and privacy checks.
