# public_eval_4a21e3da — authoring decisions

The supplied parent has three training pairs and two provided test golds. Edge
markers cast inward row/column rays through the farthest foreground pixel on
each marker's own axis. Foreground on either axis stays fixed. Partition every
other foreground cell by the cut axes, retain regions whose corner touches a
marked edge, and translate each whole region's bounding box flush to that corner.
Disconnected cells in one region share its translation; connected components
are not independent pieces. With two orthogonal markers, the opposite quadrant
vanishes. With one marker, both pieces move to its two adjacent corners.

Use `selection=union|intersection`: the exact default retains corners adjacent
to any marked edge; the alternative retains only corners adjacent to every
marked edge. One-marker behavior coincides. A discovers cut axes, foreground
regions and their separate bounding boxes; B consumes those boxes to translate
the selected regions. A wrong-intermediate witness substitutes the whole-shape
box for the local boxes while preserving the selected cells.

The authored grammar uses rectangular 5–30 grids, equal background corners,
one or two same-color noncorner edge markers (at most one per orientation), and
a third-color foreground mask strictly inside the grid. Every marker axis must
hit foreground. Generalizing the original blue/orange/red palette and connected
silhouettes to renamed colors and arbitrary region masks is explicit. Background
comes from the corners, so a dense foreground may be the modal color.

Build three core demos: a rich two-cut scene, one single-vertical scene and one
single-horizontal scene. Keep common rotation parity so the two single-axis
demos remain different physical orientations. Include visible gaps between axis
hits, off-axis extrema beyond ray endpoints, a disconnected selected region,
and singleton pieces. Queries cover both single axes, a 5×5 boundary case and
a dense 30×30 case. The supported minimum is three: all 24 evaluated two-demo
subsets left an axis-omission or selection rival that changed a query answer.
Across 44 full episodes, all 17 independently frozen rivals were refuted by
the demonstrations, with no dangerous query-changing survivor. This is a
bounded rival result, not a uniqueness proof for arbitrary programs.

Root generation is self-contained and input-only, with literal
`RULE_TASK_ID = 'ee_4a21e3da'`, empty override AXES, findings-list self_check,
and a byte-identical parametric canonical.rkt. Use the current native unapproved
preflight and protected witness/public-export helpers. Owner registration,
qualification, acceptance and training admission remain separate.

Keep the adapter resource closure self-contained: `sampler.py` is an exact
byte copy of root `generator.py` inside `workspace/parametric/`, declared as a
resource and checked by a parity regression. This avoids an undeclared outward
import while keeping the root independently relocatable.

Independent evidence under `checks/public_eval_4a21e3da/` includes a frozen
coordinate-based oracle, all five supplied labelled pairs, hand cases, strict
request/count-prefix checks, and protected Racket labels for dense, thin and
axis-only boundary scenes. Portable tests retain literal expected outputs
without importing the private checks tree. The original palette and connected
silhouettes do not alone prove the explicitly documented broader grammar;
independent geometry and boundary checks support those authored extensions.

## Current repeated-parent reconciliation

Retain exact palette-general union/intersection programs and all current sampler colors. Add largest-sector policy by replacing only placements in the current Racket decoder, retaining incoming original source as provenance; current empty-sector totality remains. Fixed-palette incoming program cannot execute current palette diversity, so no common-domain palette restriction is imposed. Both constructors alternate complete query episodes; current first two single-axis demos plus a demo-only third-lesson selection defeat named sector/ray shortcuts. Three demos remain sufficient; base source and inputs unchanged. Current evidence resides in evidence/repeat-fourth-union. Private native acceptance and root publication are separate.
