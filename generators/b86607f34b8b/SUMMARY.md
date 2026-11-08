# b86607f34b8b

Rows 0 and 1 form a color-to-operation legend above a full color-9 divider
at row 2. For each color, use its original body cells: mode 1 fills horizontal
spans; mode 2 fills vertical spans; mode 3 fills rows, then columns, exactly
once; mode 4 retains only newly added horizontal bridge cells and erases its
original seeds. Rebuild the body on background 0. Conflicts prefer mode 1,
then 3, then 2, then 4; equal modes prefer the larger numeric color.

Kind: `per_puzzle`. Repaired version: `3.0.0` (imported baseline `2.1.0`).
Canonical authority: `6fa3fd6234a8`, unchanged.

The sampler alternates compact canonical-scale examples with broad examples
that expose operation order, one-pass behavior, and overlap arbitration.
Its executable teaching contract covers 16 named rivals, including 13 that
fit all three canonical pairs. This finite contract does not establish unique
induction. Exact controls are `grid_h=9..14`, `grid_w=9..14`, and
`n_colors=3..5`; old inert controls are rejected. See `notes.md` for the
distribution and `workspace/README.md` for reusable review commands.

Approval is derived by the catalog from current code and retained evidence.
