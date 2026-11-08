# 2b83f449 — install bridges, route green tokens

Design inferred from both train examples and the private test gold: turn each
orange 777 bridge into 868, extending its magenta center one row up and down.
This partitions and links the cyan tracks. For each resulting 4-connected path,
count original green tokens and pack them from its lower endpoint inward. Tracks
whose endpoints share a row preserve their original token locations.

The episode-fixed parameter selects `down` (exact reference) or `up` (pack from
upper endpoint). The causal ablation packs tokens on the original horizontal
strips before constructing the bridges. It misses the newly connected routes.

Plan: literal and original-pair tests; Racket and Python claim implementations;
strict bridge/path sampler with matched streams and short finite-rival curriculum;
protected-Racket preflight, bounded audit, private query presentation, causal
witness, clean replay. Authoring gold is never used by the sampler.

Height is odd because complete horizontal strips alternate with bridge rows.
The maximum admitted stress canvas is 29x30, not a falsely padded 30x30.
Owner registration, review, qualification and acceptance remain pending.

## Current implementation and self-review

The default program matches both official train pairs and the supplied test gold
through protected Racket. Packing by the original side boundary is wrong at holes:
a path beginning at the right edge may end on the left side of an interior gap.
The literal hole-endpoint test pins this distinction, and `original_side` remains
in the finite rival audit. The counterfactual executes the full bridge geometry
but chooses token destinations before its connectivity exists.

Both modes use the same input stream. The curriculum uses 2–6 demonstrations,
chosen from a deterministic 64-scene pool using demonstration labels only; four
independent, distinct queries are fixed across settings and demonstration counts.
Eighteen policies cover wrong direction, wrong order, missing separators, ignored
holes, center-only barriers and positional endpoint choices. This is a finite
hypothesis audit, not universal identifiability. Bounded sampling failures raise.

The source grammar has fixed color roles, separated length-three orange bars,
nonbranching installed paths, and tokens at strip endpoints. Token-free cycles
are harmless. Equal-height endpoint ties preserve original token locations.
The stricter self-check now rejects six-cell orange runs that would otherwise
be interpreted as overlapping bridge windows. The adapter does not support
arbitrary recoloring, branch networks or an even-height canvas. Larger puzzles
use 29x30 with content spanning the width and height, not empty padding.

All seven original labelled pairs across the two assigned parents are authoring
checks, not held-out model evaluation. No owner acceptance or training admission
is implied by source execution or authoring preflight.

Final self-review strengthened the malformed-run regression: the first fixture
was already rejected by the topology check. The retained hole-at-bridge fixture
removes that incidental branch, is accepted without the new length check, and
fails/passes under a direct removal/restoration mutation of the actual validator.
