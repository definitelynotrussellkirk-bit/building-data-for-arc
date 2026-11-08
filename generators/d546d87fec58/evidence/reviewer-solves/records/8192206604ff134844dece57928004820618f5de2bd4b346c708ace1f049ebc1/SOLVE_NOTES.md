# Solve work log

Earlier generator/rule exposure: **yes**. For this prepared episode I used only
`solve/challenge.json`, this log, and my own Python. I did not consult the generator,
Racket authority, reference solutions, private labels, or preserved prior solve files.

## Revision 1

All four demonstrations are reflection-symmetric textures with rectangular groups of
color 4 replacing otherwise determined cells. In the first and fourth demonstrations,
a 180-degree counterpart directly supplies each missing value. The second and third
also erase some opposite blocks, so a horizontal or vertical counterpart is needed.
All visible members of each reflection orbit agree whenever they are present.

The solver leaves non-4 cells untouched and replaces each 4 by the first available
non-4 member of its orbit under 180-degree rotation, horizontal reflection, and
vertical reflection. This is the smallest rule that explains all examples and avoids
the cheaper rotate-180-only shortcut. The remaining uncertainty is whether 4 might be
ordinary content in some unseen case, but every visible 4 belongs to a rectangular
erasure and all demonstrations remove it in the output.
