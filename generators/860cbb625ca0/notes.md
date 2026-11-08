# Working notes: 860cbb625ca0

## Base review and repair

The imported `1.2.0` generator declared public controls but did not consume them,
and its exact matches were always placed on the top board row.  That made
`grid_h`, `grid_w`, palette, row count, position, color-count and density
requests non-observable and admitted a fixed-row shortcut.  The repaired
`1.3.1` generator now implements those controls exactly, rejects unknown or
non-integral overrides, rejects incompatible geometry instead of silently
clamping it, and keeps the selected canonical rule unchanged.

The final base surface includes explicit controls for grid size, palette family,
number and placement of matching rows, one/two-color scenes, and one/two/three
matches per selected row.  A special minimum-height case is rejected when
`position_bias=scattered` would be indistinguishable from an edge placement.
A deterministic sweep exercised 280 valid control combinations and five invalid
or unobservable combinations.

## Native parametric family

The canonical Racket program already defines three orientation policies inside
`variant-grids`; the canonical task fixes the final call to mode `0`.  The
native task-local family exposes that latent episode-level choice as
`match_mode=exact|rotations|dihedral`:

- `exact` preserves the canonical program byte-for-byte;
- `rotations` uses canonical mode 1 (0/90/180/270 degrees);
- `dihedral` uses canonical mode 2 (rotations plus reflected orientations,
  de-duplicated by the Racket source).

The sampler varies asymmetric full and sparse templates, palettes, wildcard
fillings, match rows, counts, orientations, color-aware near misses, clutter and
boundaries.  Every supported episode has 2–6 demonstrations and exactly four
distinct queries; one query is a substantively occupied 30×30 case.  Every
private episode records the concrete orientation intermediate, semantic
placements and named shortcut diagnostics.  The native adapter accepts the
worker's positional `generate(seed, settings, demos, queries)` call shape as
well as the optional difficulty argument.

## Adversarial and causal evidence

The final adversarial sweep covered 72 episodes and 552 labeled pairs over all
three settings, seeds 0–7, and 2/3/6 demonstrations.  It refuted all 264 named
shortcut attempts, checked 144 neighboring parameter rivals, performed 24
palette-invariance checks, eight fixed-anchor crossed-control checks, and 72
substantive 30×30 cases.  It found 278 distinct output profiles.  Named attacks
include fixed-row, mask-only, zero-is-background and partial-orientation
intermediates; illegal ARC outputs are recorded as refutations rather than
silently discarded.

The protected causal witness decomposes the solution as:

1. crop the input template and derive the selected orientation variant list;
2. retain that concrete, input-dependent list as the intermediate;
3. search the board with every listed grid and count starts by row.

On a qualified rotations episode, replacing the four-grid intermediate with an
exact-only intermediate removes two rotational matches and changes the final
row histogram.  Both the qualified and counterfactual programs were executed
through protected Racket and replayed from source-bound evidence.

## Readiness evidence and limits

- `workspace/parametric/evidence/current/report.json`: ordinary three-demo,
  four-query evidence for all three settings plus canonical replay.
- `workspace/parametric/evidence/current/adversarial-probe.json`: the bounded
  deep sweep described above.
- `workspace/parametric/evidence/manifest.json`: current native source and
  evidence inventory.
- `checks/860cbb625ca0/qualification/qualification.json`: passed base-authoring
  preflight on exact source bytes, with 36 parametric labeled pairs, three
  canonical pairs, two ordinary base-generation checks and 60 protected-Racket
  evaluations.
- `checks/860cbb625ca0/causal/witness.json`: source-bound protected causal
  counterfactual.
- `checks/860cbb625ca0/first-turn.json`: 24 sequential public views, 36 private
  or future-field invariance mutations and six visible-change positive controls.

This is reviewer-ready authoring evidence, not owner qualification, catalog
acceptance or training admission.  The finite sweeps refute the named nearby
rivals only; they do not prove uniqueness against arbitrary programs or all
possible sparse templates.

Imported associated notes retain their original evidence and timestamps in
`evidence/associated_notes.jsonl`.
