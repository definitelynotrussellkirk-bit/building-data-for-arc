# f0d16ecf2012

Color-9 walls form 2–5 regular horizontal lanes. Every same-color 4-connected
non-wall component moves east independently as a rigid object. The canonical
motion test uses a static board containing the walls **and that component's
original footprint**. Vacated source cells therefore remain blockers: a gapped
connected shape can stop before the east wall. Other components do not block
one another.

The generator varies width 9–22, lane count 2–5, lane height 2–4, all movable
colors 1–8, placement, connected profile, split-component diagonal slope,
witness lane assignment, and safe color reuse across wall-separated lanes.
Every ordinary draw includes both a source-footprint-blocked connected witness
and an ordinary wall-docking multi-component witness, distinguishing one-step
motion, row-wise alignment, merged-lane motion, and wall-only docking. Exactly
one override-free draw in each three-sample block is a canonical-profile anchor,
but a source-hashed slot choice prevents a fixed every-third-position cue.

Kind: `per_puzzle`. Current version: `3.3.0`. Rule hash: `4e0031784e59`.
