# Episode solve record

This is an assistant-authored engineering work log, not a captured token-level
model trace or log-probability record. Earlier rule exposure: YES. During the
preceding generator repair I read the rule, canonical examples and generator.
This solve is therefore NOT blind, regardless of the example-only workflow below.
After `prepare`, I read only `solve/challenge.json` and worked in `solve/`.
No reference source, generator, private labels or earlier solution explanations
were consulted during this phase. The supplied tools ran references internally.

## Visible observations and diagnostic probes
The three public outputs are left-aligned bars for colors 1/2/3 with run lengths
(2,3,4), (3,4,5), and (1,4,4). Other input colors do not appear in those bars.
`visible_probes.py` compares pixel totals, eight-neighbor regions and
four-neighbor monochromatic regions against those observed outputs. These are
explicit diagnostic candidates, not deliberately failed submissions presented
as natural model mistakes. The exact results are in `visible-probe-results.json`.

## Revision 1
Implemented a standalone four-neighbor flood fill per target color. A region
contributes one bar cell regardless of its area. Diagonal contact does not join
regions; other colors do not join target regions. Output width is the largest
count, with a minimum of one. The minimum-one empty case is a robustness
extension, not uniquely inferred from these nonempty demonstrations.

Checked transpose, horizontal reflection, removal of non-target colors, and
2x nearest-neighbor expansion on each public example. These probes preserve
region counts and therefore should preserve output. No masked query answer was
opened or used to select the implementation. There was one genuine attempted
solution revision; no unsuccessful revision was manufactured.
