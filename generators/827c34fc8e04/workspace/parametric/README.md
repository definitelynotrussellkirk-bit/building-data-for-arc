# Parametric family: 827c34fc8e04

The byte-exact canonical `all_markers` rule is the default. The alternate
`max_color_marker` rule introduces a true sequential dependency:

1. **A** scans the colored source cells and selects the highest-valued marker
   (row-major tie break), yielding its coordinate as the intermediate.
2. **B** doubles the complete input and paints color 1 only on the selected
   marker's full NW–SE output diagonal.

The setting-independent sampler uses three markers on three distinct diagonals,
rotates which marker carries color 9, is count-prefix independent, and includes
a 15×15 input whose output reaches ARC's 30×30 limit. Owner qualification,
acceptance, and training admission remain separate from this authoring proposal.
