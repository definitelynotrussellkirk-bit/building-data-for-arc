# Working notes: 2243318b8e96

## Current decision

Keep the canonical rule unchanged: identify same-color 4-connected objects,
paint odd cell counts 3 and even cell counts 8. The production generator is now
version 3.0.0 with exact observable axes only (`grid_h`, `grid_w`, `n_blobs`,
`n_distinct_colors`) and strict integer/type validation.

## Base defects repaired

The imported generator lacked `RULE_HASH`, exposed dead/degenerate controls,
accepted non-exact scalar inputs, and did not adequately cover the canonical
component/color structure. The replacement constructively realizes every
supported override and adds boundary contact, irregular bounding boxes, color
reuse across parity, and separated same-color diagonal contact. The canonical
Racket rule was not changed.

The semantic gate initially exposed a reviewer declaration error: ordinary
lesson rivals had been mislabeled as canonical-ambiguous shortcuts. Only the
8-connectivity alternative actually fits all canonical pairs, so the declaration
was narrowed while all six rivals remain lesson competitors.

## Parametric family

`parity_reference` is episode-fixed:

- `absolute`: exact canonical default, odd → 3 and even → 8.
- `same_as_cue`: locate the unique color-1 cue object, compute its size parity,
  and paint objects with matching parity 3, others 8.
- `opposite_to_cue`: use the same input-derived cue parity but reverse 3/8.

The minimum two demonstrations cross odd/even cue parity and nuisance frequency
ranks. Every episode has four distinct queries, with a substantive 30×30 fourth
query, and inputs are matched across settings.

## Adversarial findings and repairs

Focused review found and repaired (1) a shape-flip path that displaced the
intended diagonal anchor, (2) a component-identity bug in the cue mutation
probe, and (3) a total-foreground-parity shortcut that survived one minimum
lesson profile. Final probes cover 96 episodes, all settings, demo counts 2/6,
960 named-shortcut attacks, strict malformed inputs, public/private invariance,
crossed cue/object parity controls, and 32 substantive 30×30 checks.

## Status and next action

The exact source has reviewer preflight, protected-Racket execution, a replayed
wrong-intermediate causal witness, and verified one-query public projection.
Finite testing does not prove universal uniqueness. Next action is owner source
review followed by unchanged native qualification/acceptance; training admission
remains separate.
