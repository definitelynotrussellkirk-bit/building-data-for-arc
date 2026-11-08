# Solve work log

## Initial observation

I had not opened this task's generator, rule, notes, solutions, audit records, or private labels. The four visible demonstrations contain separated color-4 objects. Objects with a genuinely enclosed background region are recolored 8; objects without a hole are recolored 2. A concave object whose missing cell opens to the exterior is 2, so this is topology rather than rectangularity, size, or density.

## Revision 1

Hypothesis: find each same-color four-connected nonzero component, flood the complement from the boundary of that component's bounding box, and classify it as color 8 exactly when an unvisited interior background cell remains. Recolor every other component 2 and retain the background. This handles rings of different sizes and distinguishes the open notch in train example 1 from a closed hole.

Remaining uncertainty: the visible examples use only color 4 and separated objects. The implementation preserves component identity by original color and applies the same hole test to any nonzero color.
