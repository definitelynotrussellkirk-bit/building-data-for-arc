# Solve work log

This is a human work log, not a captured model token trace.

## Prior exposure

Before this solve episode I had already reviewed and repaired the selected generator, so I had earlier exposure to the intended odd-one-out rule. I did not consult the generator, Racket rule, canonical ledger, reference solution, private query labels, or earlier solve explanations after `solve prepare` created this episode.

## Revision 1

Visible hypothesis: each non-zero connected component is a colored shape. Compare shapes after translation, quarter-turn rotation, and mirror reflection. Three or more components belong to one dihedral-equivalence class and exactly one belongs to a singleton class. Return that singleton as its tight bounding-box crop, preserving the pose and color seen in the input.

Checks from the visible examples:

- Example 0 has three 3-cell L shapes and one 4-cell L shape; the output is the 4-cell object's original 3×2 crop.
- Example 1 requires reflection as well as rotation: three five-cell components are equivalent under the full dihedral group, while the color-5 component is the singleton; the output preserves its 4×2 pose.
- Example 2 keeps object size equal, so cell count alone is insufficient; the color-1 T shape is the singleton and is returned in its observed 2×3 orientation.

Implementation: find same-color 4-connected components, canonicalize each component over the eight dihedral transforms, count canonical classes, select the only class of frequency one, and crop that original component. I did not make a deliberately wrong revision because the first visible hypothesis accounts for all three demonstrations and directly handles both queries.

Remaining uncertainty: private query labels are intentionally hidden. The code assumes the visible lesson contract continues to provide exactly one singleton dihedral class and uses 0 as background.
