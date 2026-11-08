# Working notes: 8c12816521a2

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/8c12816521a2/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Native parametric proposal (2026-10-24)

- Added one episode-fixed parameter, `red_anchor`: canonical `far_edge` is preserved byte-for-byte; `separator_edge` keeps the same input-derived per-lane red count but rebuilds that band beside the cyan separator.
- The required sequential dependency is: identify each yellow-triggered lane and count its original opposite-side red cells (`nr`), then use that lane-specific `nr` to choose the red/cyan boundary. The boundary cannot be fixed before the count is known.
- The deterministic sampler supports 2–6 demonstrations and exactly four distinct queries, includes vertical/horizontal and both yellow sides, substantive 15–30 grids, connected red inputs, mixed lane counts, multi-cell yellow, and non-trigger lanes. Inputs are identical across settings and query sampling is independent of demonstration count.
- Bounded self-review at `workspace/parametric/evidence/current/self_review.json` checked seeds 0 and 17 under both settings. Demonstrations alone rejected the declared alternate plus fixed-count-one, global-max-count, yellow-count, all-lanes, no-green, wrong-tip, and no-transpose shortcuts. Selected labels and the declared rival were replayed in protected Racket; this is finite evidence, not a universal uniqueness claim.
- Repaired the existing test to resolve canonical/base data through `reviewer_support` in relocated runtimes and to compare the compact base rule with the pretty canonical rule semantically rather than by formatting bytes. Production `generator.py` and canonical behavior remain unchanged.
- Remaining owner action: admit only after exact-source integration, fresh native qualification, and acceptance on the live bytes. This review prepares evidence; it does not claim acceptance or training admission.

## Reviewer qualification handoff (2026-10-24)

- Native qualification status: `qualified` for both `far_edge` and `separator_edge`, seeds 0 and 17, three demonstrations and four queries per episode; 40 protected-Racket evaluations. Receipt: `checks/8c12816521a2/qualification/qualification.json` (`02c31104ec1bc008c0843f7ce549c542783db8682d123a621831f1f3a3bf16be`); execution: `checks/8c12816521a2/qualification/execution.json` (`6e2be08500e8365d1aaa4fd6d15fb93777a37ca61b3df0bfc52b66d94e2b6460`).
- Causal witness: a 30x30 canonical-setting query records per-trigger-lane red counts `3,4,2,3,1,2,3`; replacing that intermediate with constant one changes 11 output cells under protected Racket. Witness: `checks/8c12816521a2/causal/witness.json` (`3a057bd8cf59e36ff260822cfe2bee40402f61cc2434bbef8afac7d67078d531`); replay: `checks/8c12816521a2/causal/replay.json` (`095f2851635ed4df10cf17a27ef59d624698cf3ffc781c5bda426926e0ec5d8c`).
- Exact program hashes: canonical `c9f4b6ba8f93a08df02604a40459169ff7930613791c1ad106f877f54029afd4`; separator-edge `8deabf656dcff8536ad80f7a8b9acd7b9ddf1fa1da20d8af35d069a9e58e4648`; source inventory `4a0d440a796cb771dc360eebe623ef87e5d64ba383abfe95e19065f802294ebd`.
- Owner acceptance and training admission remain unperformed; the qualified reviewer source must still be integrated and accepted on the exact live bytes.
