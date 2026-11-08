# Working notes: 5295bc5ff1cb

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Native parametric extension — reconstruct, then mark the spanning lattice

`workspace/parametric/` adds a finite two-setting lesson while preserving the
catalog rule as the byte-exact default. `tile_only` infers the smallest visible
row/column periods, shifts one column, and reconstructs the full grid.
`tile_then_mark_span` first creates that complete intermediate, then finds the
unique same-color component whose bounding box reaches all four output borders
and repaints that component with the original cover color. The spanning object
is not available before reconstruction, so Stage B consumes Stage A's
input-dependent result.

Both settings use identical inputs, support 2–6 demonstrations, and emit exactly
four novel queries including one 30×30 stress case. The visible decoy color is
more frequent and numerically lower than the lattice color, so most-frequent,
fixed-lowest, no-shift, visible-only, and tile-only shortcuts are contradicted
in ordinary two-demo lessons. The bounded self-review covers seeds 0–31 and
demo counts 2, 3, and 6. It is finite Python-mirror evidence only; native
qualification and causal receipts separately establish protected-Racket
execution and exact source binding. No owner acceptance or training admission
is claimed here.
