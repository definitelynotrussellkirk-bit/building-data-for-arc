# f34f99f28c2d

0-bg grid with exactly: (a) ONE control cell in {6, 7, 8, 9} at some scattered position; (b) ONE color-2 template (4-connected blob of 3-5 cells); (c) ONE color-1 anchor cell at some position. Layout is randomized: template, control, and anchor are placed at varied positions with 1-cell buffer between them. Rule: find control → rot_count = control - 6. Find template, normalize its cells, rotate 90° CW rot_count times. Paint the rotated cells at offset (anchor) in color 4 onto a copy of the input. Stamps must fit within grid bounds.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
