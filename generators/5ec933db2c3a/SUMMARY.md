# 5ec933db2c3a

Version `3.0.0`; selected rule hash `009a49ded011`.

A full-height color-9 divider at column 3 separates a 3×3 template from a larger board. The template has six color-2 cells, one color-7 cell, and two zeros. Consider all four rotations. A board window is repaired only when every template-zero aligns with zero, every present occupied cell has the correct color, and exactly two occupied template cells are missing. Restore those two cells with their template colors and return the board alone.

The generator emits 7–10 by 12–16 inputs. Every generated scene contains exactly two repairable targets, a one-hole negative, a three-hole negative, at least one target requiring a non-identity rotation, and a target whose missing cells include color 7. Only `grid_h` and `grid_w` are public overrides; both are exact. Three of every four default profiles are canonical-size anchors.

Declared lesson competitors test the three closest shortcuts: repairing one/three-hole copies, ignoring rotations, and filling every hole with color 2. Three demonstrations are required and must refute all three competitors.
