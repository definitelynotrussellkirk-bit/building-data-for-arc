# Working notes: 44690b1b635f

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.


## Current recovery proposal

Unselected hash-bound source repair/prototype proposal: `generators/44690b1b635f/workspace/proposals/recovery-54e4297da80c4d24/manifest.json`. Original assignment/draw contracts are absent; no source/variant/training approval is granted. Isolated patch replay passed; author checks are reported or incomplete. Reproduce identity or independently rebase/review before selecting these bytes.

## Current parametric proposal — review-8be11c16d1774c03

The retained fixed-mask audit identified finite topology support rather than a label defect. A separate unapproved prototype now varies two nearby semantic choices while preserving the canonical default exactly: `connectivity=cardinal|king` and `phase=center_even|arm_even`. The canonical Racket source remains byte-identical (SHA-256 `d78c0152b4b3f003a6ceaf2601ffb3234247354b626267c771a1bcf51d25e618`; normalized rule hash `72a0e00e932b`); `generator.py`, the canonical row, approval state, and training boundary were not changed.

The procedural sampler creates independent wall masks with a cardinal component, a diagonal-only component, and an unreachable pocket. One setting is chosen once per episode; demonstrations uniquely identify it among all four declared rivals and every retained query disagrees with the other three. The retained evidence at `WORK/checks/parametric/44690b1b635f-maze-connectivity-phase-v1/` contains four 3-demo/4-query episodes, 28 distinct inputs, exact private Racket programs, visible-only content IDs, and independent Racket/Python replay. The task-local owner inventory at `workspace/parametric/evidence/manifest.json` binds the reviewed source, adapter, contract, documentation, focused tests, unchanged generator, and canonical authority. The bounded adversarial probe covered maximum seed/count boundaries, forced retry exhaustion, strict bool/ragged-grid rejection, redaction, and all 28 retained labels without finding a defect.

Remaining limits: the evidence is finite and claims only the four declared rivals. The unchanged production test wrapper is blocked in this packet because `puzzle_generators.per_puzzle.44690b1b635f` is not mapped; the task-local focused suite runs directly and does not turn that aggregate wrapper failure into a pass. Next useful action is owner qualification of the adapter/manifest, not a production-source or approval-hash change.
