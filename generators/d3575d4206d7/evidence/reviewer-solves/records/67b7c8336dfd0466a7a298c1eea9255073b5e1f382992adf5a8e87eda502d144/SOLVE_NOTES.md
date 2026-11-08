# Solve work log

I used only `solve-blind/challenge.json`, the public rendering, and my own local
scripts. I had not seen this task's generator, Racket rule, private labels, or
an earlier explanation before this attempt.

## Revision 1 — component/layout hypothesis

The examples are divided by full rows and columns of the dominant color into
small symbol cells, usually 3×3. Azure (`8`) is not asking for a global color
replacement. It marks one or more example symbol shapes. The other annotation
color makes copies of those shapes in other symbol cells.

Initial false leads included matching exact 3×3 neighborhoods, recoloring every
same-shaped component, and flood-filling through newly recolored copies. Each
fails visibly: exact neighborhoods differ among positive copies; isolated
same-shaped objects remain unchanged; and iterative propagation would absorb
extra dangling objects at the far edge.

The consistent rule is marker-anchored row/column rectangle completion. For one
azure component, find same-shaped monochromatic components in its symbol-row and
symbol-column. Recolor those copies. When a row-aligned and a column-aligned copy
exist, also recolor a same-shaped copy at their fourth rectangle corner. Do not
continue propagating from that new corner. Multiple azure shapes are processed
separately.

A local parser splits on full dominant-color separator lines, extracts
8-connected components inside each resulting symbol cell, and compares their
shapes up to translation. The source color is the color that supplies aligned
copies for the largest number of azure shapes; rarity breaks an accidental tie
with a common base-pattern color. This is needed in the first training example,
where a common color happens to make the same four-pixel diamond in a few cells.

Local visible-example replay produced exact outputs for all three training
pairs. Remaining uncertainty is limited to whether a hidden query introduces a
tied source color or a marker crossing a separator; neither occurs in the five
public grids, and both query layouts preserve the same cell construction.
