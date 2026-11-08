# Working notes: 628b4a2c24c1

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/628b4a2c24c1/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-24 parametric main review

Built a native task-local family under `workspace/parametric/` with one private
parameter, `sweep_policy`:

- `rightward` is byte-for-byte the canonical Racket program (SHA-256
  `5ac6fbbb3b3dddc964628cb88665dcaae3bfa10c6dc7973fe7a7eb0afdb36c27`).
- `widest_corridor` measures the nearest wall/boundary on both sides of each
  seed, compares the two open corridor lengths, and fills the wider corridor
  (right on ties).

The first two demonstrations deliberately include a wall-free seed row and both
left/right decisions, so the previously observed “only extend rows with a right
wall” shortcut is no longer viable.  A reusable protected-Racket finite-rival
audit lives at `workspace/parametric/audit.py`; it checks intended labels and
eight named rivals against demonstrations only before looking for query harm.

Current reviewer evidence:

- Native source inventory:
  `workspace/parametric/evidence/manifest.json`
- Native qualification:
  `checks/628b4a2c24c1/qualification/qualification.json`
- Protected causal witness:
  `checks/628b4a2c24c1/causal/witness.json`
- Bounded teaching audit:
  `checks/628b4a2c24c1/audit/audit.json`
- Staged task tests:
  `checks/628b4a2c24c1-task-tests/result.json`

The staged task suite also exposed and repaired a portability defect in the
existing canonical test: it now resolves canonical data through
`reviewer_support.find_root` and `canonical_pairs` rather than a fixed parent
depth.  The canonical generator and canonical data were not changed.

Status is reviewer-reported `ready`, not accepted.  Exact-source owner replay,
acceptance, and any training admission remain separate required decisions.
Finite seeds and named rivals do not prove universal identifiability or measured
learning benefit.
