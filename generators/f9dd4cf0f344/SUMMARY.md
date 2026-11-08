# f9dd4cf0f344 — exact hollow-cardinal-cross completion

The unchanged Racket rule fills an **interior zero cell** with color k exactly
when all four cardinal neighbors equal the same nonzero k. Nonzero centers,
partial arms, mismatched colors, diagonal-only arms, and boundaries do not fire.

Selected generator version: **4.0.0**. One third of default texture draws are
small canonical-style anchors (two distinct-colored crosses, no distractors),
in every difficulty. The remaining draws mix positives with 3+1-color near
misses, occupied centers, partial arms, diagonal-only motifs, and 2+2-color
mismatches. Larger canvases and counts increase by difficulty outside anchors.

Accepted numeric overrides are exact: `grid_h`, `grid_w` (5..22), `pluses`,
`n_decoys` (0..8). Free dimensions may grow to accommodate pinned counts.
Impossible pinned combinations raise structured `ValueError`, never silently
shrink the request. See `generator.py:AXES` for textures and exact defaults.

Breaking change from 3.0.0: removed inert `palette_kind`, `palette_size`,
`position_bias`, `n_distinct_colors`, `density`, and old inert helpful-texture
aliases. Unknown/removed overrides now fail explicitly. `texture=no_pluses`,
`partial_arms`, `mismatched_arms`, or `pluses=0` are explicit identity controls,
not the default lesson distribution. `self_check` accepts these with matching
metadata; it requires a real rule application for unannotated/default draws.

Racket authority was not edited. Current catalog approval still depends on
maintainer intake of source-bound evidence, not this summary. This generator
has known-rival coverage, not a proof that every sampled lesson identifies the
rule or measured evidence of improved model accuracy.

The retained fresh solve is a concrete lesson-level counterexample: three
visible-consistent candidate programs disagree on both queries. A public-only
query-sensitive gate is supplied in workspace/lesson_ambiguity_gate.py; it is
not integrated into the shared exporter. See the root G5 finding before
admitting unconstrained sampled lessons to training.
