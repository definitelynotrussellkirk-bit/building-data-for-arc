# Working notes: 15df00eb9323

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

## 2026-10-25 review `review-8031d0b1f785cb68`

The inherited generator exposed mostly dead or coercive controls.  Version 2.0.0
replaces them with three exact observable axes (`grid_h`, `grid_w`, and
`palette_kind`), rejects unknown/coercive values and negative indices, preserves
all canonical inputs, and constructs three isolated connected blobs whose
normalized support map always contains counts one, two, and three.

The native parameter is `consensus_level = majority | unanimous`; the exact
canonical majority program is unchanged and the alternate changes only the
support threshold from two to three.  A 40-seed audit at 2 and 6 demonstrations
covers 160 episodes and 1,280 pairs with no union or exactly-two rival survivor.
That audit caught a seed-7 shelf-permutation bug: anchors had been centered before
shelf assignment, allowing a wider transformed mask to inherit an out-of-bounds
right-edge anchor.  Anchors are now centered only after shape-to-shelf assignment,
and the exact seed is retained as a regression.  Protected-Racket authoring
preflight and owner review remain separate gates.
