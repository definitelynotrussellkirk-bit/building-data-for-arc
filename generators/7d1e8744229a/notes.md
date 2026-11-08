# Working notes: 7d1e8744229a

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 — Native cue-directed sequential family

Built `workspace/parametric/` with the exact canonical program as
`mode=canonical` and one meaningful adjacent setting,
`mode=cue_rotate_erase`.  The input keeps the canonical three-color symbolic
seed and replaces one non-anchor edge-midpoint cell with a zero cue.  The
sequential setting expands the canonical 10×10 template, rotates that
intermediate according to the cue, then erases the full 4-connected component
containing intermediate coordinate `(0,1)`.  Four demonstrations are required
because they constructively cover all four cue directions; four fresh queries
remain controller-private and are projected one at a time.

The source morphology is intrinsically 5×5→10×10.  I did not pad it to 30×30,
because that would create a different family rather than stress the same rule.
Bounded self-review found no supported-seed construction, teaching, public
projection, or Racket-label failures.  The source-bound witness changes A by one
extra quarter-turn while leaving B unchanged and replays two disagreeing final
outputs through protected Racket.  Next owner action: review the exact source,
run native qualification/acceptance on the integrated hashes, and decide
training admission separately.
