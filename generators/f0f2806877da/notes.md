# Working notes: f0f2806877da

## Current parametric decision

The separate `workspace/parametric/` adapter adds `read_order=forward|reverse`.
The forward program is the exact canonical string; reverse changes only the
order of decoded symbols before the stateful trace. The canonical generator,
grammar and reference authority remain unchanged. Use three demonstrations and
four queries normally; the adapter supports independent 2–6 and 1–4 counts.

The causal dependency is prefix trace → input-dependent cursor → placement of
the next segment and suffix. A protected-Racket witness substitutes column 3 for
the carried column and must change the final output. Input bounds stay exactly
2×12 and output bounds 8×7; 30×30 would require a different grammar or empty
padding. Queries exercise both lateral boundaries and the last row.

## Teaching and review findings

Construct the first two demos with the same command counts but different paths.
The first exposes left `00` and right `22` upper rows; the second exposes left
`02` and right `20`. Together all four two-cell upper patterns are visible, and
a width-one upper-zero symbol teaches width-first parsing. This strengthens the
initial diagonal-only design after an independent reviewer retained a protected
Racket counterexample at seed 1. A related seed-2 “any upper zero” shortcut is
covered by the same fix and explicit regressions. The two-demo floor is retained.

`audit.py` is the reusable task-local check/example writer: twelve executable
rivals, chosen-rule parity, distinct input/count checks, and one-query public
projection. Finite tested rivals do not establish universal identifiability.
Its receipts distinguish protected execution from the additional Python-only
sampler census. Native qualification, source inventory and causal witness are
required before the owner can accept this exact source; no training admission.

The existing canonical sampler's seed-167 top-right-cell shortcut remains open:
the new adapter fixes its own teaching path only. Existing canonical tests now
use public same-checkout discovery and data helpers. Whitespace-normalized base
authority strings agree in full; raw/target equality and the canonical rule hash
pin remain enforced. That test portability repair does not change any labels.

The next owner action is source integration followed by fresh native qualification
and exact-source acceptance. See the compact return `REVIEW.md` and its source-bound
receipts for checks actually run. Imported historical evidence remains in
`evidence/associated_notes.jsonl` and `evidence/review_index.json`.
