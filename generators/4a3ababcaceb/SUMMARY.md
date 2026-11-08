# 4a3ababcaceb — strongest-red motif replacement

Version 3.1.0, input-only generator. Racket authority unchanged; rule pin
`3617779ffc60`.

A regular lattice has 3×3 tiles with complete color-9 separators. One tile has a
unique positive maximum count of red (2). One distinct tile contains the only
green (3) marker and no red. Replace that entire target with cyan (8) at the
source's red offsets and zero at all other offsets. Preserve all other tiles.

Three consecutive un-overridden draws for one seed provide a canonical one-row
anchor, a denser weaker-red candidate before the source, and a sparser/purer
weaker-red candidate after it. Contrast sources contain non-red clutter and
contrast targets require erasure. The profile schedule rotates with seed and
sample index; three-demo guarantees do not extend to arbitrary resampling.

Supported exact integer overrides: `tile_rows=1..5`, `tile_cols=3..6`,
`src_size=2..9`, `marker_offset=0..8`. Full bounds work at every difficulty. Old
inert axes are intentionally removed; unknown names raise an error. Structural
validation is somewhat broader than default sampling, including lawful two-tile
and singleton-source examples.

Checks and decisions are retained in the review return. Approval remains derived
from catalog/maintainer evidence; no training-quality certification is implied.
