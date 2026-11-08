# Working notes: 34569d6118b3

The canonical rule pairs ordered non-gray swatches with ordered gray masks,
then expands a dense lower color layout through those masks. The first all-zero
row ends the header; gray becomes the layout color and mask holes stay zero.
The selected generator is unchanged at version 4.0.0 and normalized rule hash
`e2b81b5e525c`. Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

## Current parametric proposal

`workspace/parametric/prototype.py` adds two episode-fixed parameters:
`template_order=forward|reverse` and `mirror=false|true`. The default
`forward,false` preserves the exact canonical Racket text (SHA-256
`213d60bb58991cfb0f063a34f4ad178ac1fe312f144a5583abcfc166cfe8fc8f`).
Alternatives minimally alter template binding order and/or horizontal lookup
inside each mask; header parsing, swatch/color binding, layout extraction and
mask expansion remain the original reasoning pattern.

The prototype reuses the ten canonical general input profiles. Demonstration
and query counts are independent, defaulting to three and four. Every retained
input is distinct across both splits. Bounded sampling requires the first
demonstration to distinguish all four settings; it records rejections and fails
visibly on exhaustion. The compact two-color profile alone cannot distinguish
`forward,false` from `reverse,true`: its 2-by-2 masks are horizontal reflections
of each other. A focused counterexample retains those two survivors and marks
a distinguishing query ambiguous. Compact inputs remain supported after an
informative demonstration.

All retained labels and parameter-rival predictions are executed in matching
Racket and compared to an independent Python mask composer. Query
identifiability uses only survivors inferred from demonstration pairs. Public
files use the shared exact public projection and content IDs, sorted opaque
filenames, no hidden setting/seed/program/query answers, and atomic duplicate
rejection/no-overwrite publication. Exact references, hashes, executed witnesses,
query checks and source/runtime identities are private.

This is a **proposed task-local prototype**, separate from canonical approval
and training admission. The input teaching filter intentionally emphasizes
parameter evidence; testing the four declared rivals does not establish
uniqueness among arbitrary ARC hypotheses. Counts are limited to 1..32 per
split; the default sampling cap is 512 candidates (configurable up to 4096).
Atomic export requires Linux. Runnable commands and precise behavior are in
`workspace/parametric/README.md`; focused regressions are in
`tests/test_parametric_34569d6118b3.py`. Retained execution receipts belong under
the review packet's `checks/parametric/` and do not alter canonical authorities.
