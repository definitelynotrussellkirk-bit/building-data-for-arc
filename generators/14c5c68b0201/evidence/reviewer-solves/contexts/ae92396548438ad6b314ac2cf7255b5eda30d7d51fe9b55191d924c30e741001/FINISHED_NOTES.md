# Solve work log

## Exposure declaration before solving

I had not opened the task `14c5c68b0201` generator, canonical rule, notes,
reference solution, private labels, or earlier solution explanations. Before the
episode I had only read packet-level workflow documentation and the assignment
text naming the task. I treated this as a genuinely blind visible-example solve.

## Revision 1 — periodic seed rectangle per compartment

**Observation.** Color 9 partitions every grid into one or more four-connected
rectangular zero-valued compartments. Each compartment contains one small colored
pattern. In every training output, the compartment is filled by periodically
repeating the smallest axis-aligned rectangle containing that colored pattern;
zeros inside that seed rectangle are meaningful cells of the tile.

Examples checked manually:

- The three-cell 4-colored L has bounding tile `[[4,4],[4,0]]`; repeating it with
  phase anchored at the observed seed reproduces the alternating/all-4 rows.
- The 6-colored seed has a 3x3 tile and the 7-colored seed a 3x4 tile; their
  output row and column phases match modulo those dimensions.
- The second and third training pairs use the same construction with 3x4 and
  3x5 seeds, so the rule is not tied to a particular color, panel size, or tile
  size.

**Probe.** I wrote an inline Python implementation using only
`solve-blind/challenge.json`. It found four-connected components of non-9 cells,
extracted the colored cells' bounding rectangle from the input, repeated that
rectangle modulo its height/width over the component, and compared all generated
training outputs exactly. Result: `True` for all three training pairs.

**Implementation choice.** Components are found rather than assuming every panel
is a perfect global rectangle, so separator geometry is respected. The period is
anchored at the observed seed rectangle's top-left; this preserves the phase seen
in every example. A component without a colored seed is left unchanged.

**Alternatives rejected.** Repeating only the colored cells' shape without the
zeros would lose holes in the motif. Inferring a fixed 3-row or 4-column period
would fail the 2x2 and 3x5 examples. Filling bounding boxes directly rather than
non-9 components could overwrite 9-valued separators in irregular layouts.

**Remaining uncertainty.** Visible examples do not show multiple nonzero colors
inside one panel or a motif whose bounding box touches a non-rectangular panel
edge. The component-and-literal-tile interpretation is the smallest rule that
matches every visible pair and naturally handles both cases.
