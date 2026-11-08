# Native parametric family: e282a664f807

- `single_box` is the exact canonical program: identify the unique two-cell
  color and fill its bounding rectangle on a blank grid.
- `largest_completed` completes every two-cell color into its rectangle, then
  recolors the unique largest completed rectangle to 9.

The alternate has a real sequential dependency.  Before completion all
candidate colors occur exactly twice; only the completed intermediate exposes
the rectangle areas used by the second selection.  The retained wrong-order
program chooses the smallest raw pair color before completion.

Generation supports 2–6 demonstrations and 1–4 private queries with stable,
independent prefixes.  The fourth query is a substantive 30x30 case.  Public
projection and presentation order are handled by the shared packet tools.
