# Working notes: 6470a9c16f7b

## Current rule and generation

A zero cell inside nested hollow rectangular frames takes the color of its
smallest enclosing frame. Nonzero frame cells and exterior background remain
unchanged. The canonical examples contain two or three frames; adjacent borders
of different colors are lawful.

Version 1.3.0 generates two hollow frames normally and three on hard; `n_frames`,
`palette_size`, and `n_distinct_colors` can select two or three and must agree.
Every normal draw has a zero in its outer annulus and a zero inside its innermost
frame. Those two ownership witnesses refute filling all enclosed zeros with the
outermost color. Three-frame middle regions may have no zeros when adjacent
borders occupy their whole annulus, as in the canonical family.

The former 1.2.0 generator produced one frame plus a solid five-cell bar. It
never exercised inner-frame ownership, and its self-check accepted that reduced
family. Two focused regressions failed against those exact original bytes
(`69110c8b4ec69952bafdbab7e361667f2e10f657a1bd6d64f72eab7ffd28ac90`)
before the change. The selected repair replaces the bar with hollow nested
frames and checks exact outlines and strict nesting. The checker permits lawful
adjacent nesting; the stronger outer-annulus witness is a production guarantee,
not a restriction on canonical inputs.

## Axes and limits

Frame and canvas dimensions, palette kind/texture alias, and color cardinality
are consumed and validated. Two frames need an outer frame at least 7×7;
three need at least 9×9 so the outer-annulus witness fits. Canvas bounds are
7–14 rows and 7–16 columns, with dynamic lower bounds for nesting depth. Frame
bounds additionally depend on the chosen canvas. Invalid names, non-integer
numeric axes, conflicting cardinalities/aliases, and impossible dimensions raise
clear errors. Warm/cool palettes select from their declared nonzero color sets.
`default` and `varied` both use colors 1–9. Position bias and density retain their
single supported values. Diagnostic degenerate textures remain deliberately
outside the normal domain, use fixed fixtures, and reject additional axis
settings rather than ignoring them.

This generator supports a single chain of two or three differently colored
rectangular frames. It does not claim arbitrary depth, repeated frame colors,
multiple disjoint nests, or nonrectangular regions. No reference rule changed.

## Focused verification

Task-local tests cover both historical defects, deterministic normal draws across
four difficulty settings, two/three frame depths, minimum/maximum geometry,
palette/cardinality aliases, impossible overrides, invalid types, broken borders,
degenerates, and all three canonical input geometries. The final direct and
portable task-test runs each passed 73 tests.

Selected Racket labels match independently constructed smallest-container labels
on 16 generated palette/depth/geometry cases and the supplied outputs on all
three canonical pairs. All three canonical inputs also pass the self-check.
Evidence is retained under `checks/6470a9c16f7b/` in the repair packet. Bounded
adversarial checks addressed geometry/nesting and palette/override/domain
validation; no remaining failure was found in that scope. No broad battery or
exhaustive seed census was run; matching labels do not establish universal
coverage or training admission.
