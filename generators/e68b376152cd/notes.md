# Working notes: e68b376152cd

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Current retained-rule union

Preserve exact spatial and largest-first programs. Incoming area-descending has the same area/bbox ordering and packing semantics, so retain its program as comparison evidence rather than an indistinguishable setting. Use both nonrectangular incumbent and incoming ordinary/large-rectangle banks; the first demonstration retains a nonrectangular shape diagnostic.

Source-bound bounded checks live in `workspace/parametric/evidence/union-current/`. They establish finite Python contracts and protected Racket replay, not universal correctness or training admission. Owner qualification and fresh acceptance passed on these exact source bytes; `parametric/accepted.json` and `evidence/owner-merge-current/admission.json` are current. Existing canonical audits and training admission remain separate.
