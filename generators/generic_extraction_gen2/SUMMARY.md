# generic_extraction_gen2

gen2: recolor one distractor color, then extract-largest.

Transform: `(extract-largest (recolor g SRC DST))` — first recolor every
SRC cell to DST (a global color swap on the scattered distractors), then
crop to the bounding box of the largest 4-connected object (extraction).

The input is a large field of many small distractor components plus ONE
strictly-largest solid rectangle (a unique color, untouched by the
recolor, so it stays the unique argmax). Output = that rectangle's bbox
patch, recolored. SRC/DST are chosen so the swap never creates a
component larger than the rectangle and never touches the rectangle's
color, keeping the Racket `argmax obj-size` deterministic.

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
