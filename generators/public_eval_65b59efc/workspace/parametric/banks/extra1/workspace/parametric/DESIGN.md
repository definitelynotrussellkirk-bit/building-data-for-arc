# Table-driven stencil assembly

Build the missing faithful reference for public parent 65b59efc, then add the episode-fixed setting tile_orientation=as_drawn|clockwise. Infer the slot size from the gray table dividers. Decode each top template and its bottom recolor legend; overlay middle panels by original source color; replace each occupied layout cell with its selected, optionally rotated, recolored template. This retains input-dependent correspondence and nested geometry.

Alternatives considered: changing only output colors would be cosmetic; rotating the whole assembled output would obscure correspondence. Rotate each recovered tile instead. This choice is the implementer's, under the request to build autonomously.

Scope: only this task home; no catalog/approval/shared changes. Default reference and canonical copy must be identical. All native resources are adjacent inside parametric/. Independent demos 2..6, queries 1..4, four private query bank; matched input streams; sequential public views with independent private ordering. Exact 30x30 stress uses five-cell tiles and five source templates, full-width table and large bottom legend swatches; no output exceeds 30x30.

Grammar: square template/layout slots; unique source colors, each legend swatch one nonzero non-gray color; overlaid layout conflicts rejected. Finite original data do not establish behavior on conflicting panels. Infer rather than hardcode template size, number of columns or palette.

A: recover templates, layout and recoloring by source color. Intermediate: selected per-layout-cell template offsets and recolor. B: rotate (variant) and stamp into the enlarged output. Witness replaces recovered offsets by solid tile offsets in executable Racket, not merely metadata.

Verification: original train and gold, literal asymmetric fixture, malformed-input/count checks, deterministic matched streams and stable prefixes, bounded finite-rule teaching audit, protected native authoring preflight, fresh source-bound causal replay and public privacy checks. No owner acceptance or training claims.
