# Working notes: 75381adf158d

## Base repair

The imported `2.0.1` generator advertised a broad set of mostly ignored or
singleton axes, silently accepted unknown overrides, stayed on small grids, and
had no exact rule mirror or observable structural contract.  Some degenerate
modes contradicted its own self-check.  Version `3.0.0` replaces that interface
with three real controls (`grid_h`, `grid_w`, and `scene_profile`), constructive
separated-quadrant scenes, fail-closed override validation, an exact flood-fill
oracle, structural analysis, and stronger self-checks.  Ordinary draws now
cover 10×12 through 30×30 and always exercise the canonical fill while retaining
an exterior-connected zero-region.

The three scene profiles serve distinct teaching roles.  `mixed` combines
closed and open frames; `largest_counterexample` gives closed holes of different
sizes plus an open-frame distractor; `many_holes` supplies four closed holes.
The exact canonical Racket authority `(fill-all-enclosed g 8 0)` and
`RULE_HASH=ae1411cac560` remain unchanged.

## Parametric reviewer build — `largest_escape`

The native family in `workspace/parametric/` has two settings.  `canonical`
preserves the selected canonical source byte-for-byte.  `largest_escape` first
fills enclosed zero-regions with color 8, then reads the newly created cyan
components, chooses their unique largest member, and paints a straight cyan
route from its center to the nearest border (tie order: top, left, bottom,
right).  The protected counterfactual chooses the smallest created component;
its different result proves that stage B consumes stage A's input-dependent
intermediate rather than merely repainting the source grid.

Focused tests passed for the repaired generator and family.  A bounded 32-seed
audit covered 64 setting episodes, 192 matched pairs, 192 causal separations,
192 named-rival checks, count boundaries, and distributed 30×30 content.  The
three Racket programs passed strict syntax and protected label checks; the
authoring preflight, protected causal replay, and 16-view sequential public
projection passed.  These receipts are reviewer-side authoring evidence only.
Owner exact-source integration, native qualification and acceptance, variant
approval, and training admission remain pending.
