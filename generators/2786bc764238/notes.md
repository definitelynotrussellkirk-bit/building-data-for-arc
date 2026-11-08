# Working notes: 2786bc764238

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

## 2026-10-25 review `review-8031d0b1f785cb68`

The canonical rule itself was sound, but the source API accepted coercive scalar
inputs: integer-valued floats could satisfy integer overrides and negative
`sample_index` values indexed schedules from the end.  Generator version 3.1.0
now rejects booleans/floats for exact integer fields, rejects negative indices,
closes the difficulty enum, and validates override names and ranges before any
sampling.

The native parameter is `selection_metric = cell_count | bbox_area`; the exact
canonical `cell_count` program is unchanged.  Each lesson contains unique,
different winners plus explicit taller and wider low-area decoys.  Placement is
rejected unless topmost, leftmost, largest-height, largest-width, and global-crop
shortcuts disagree with both declared rules.  The retained bounded audit covers
8 seeds at 2 and 6 demonstrations (32 episodes, 256 pairs); all named-rival
survival counts are zero.  Protected-Racket authoring preflight and owner review
remain separate gates.
