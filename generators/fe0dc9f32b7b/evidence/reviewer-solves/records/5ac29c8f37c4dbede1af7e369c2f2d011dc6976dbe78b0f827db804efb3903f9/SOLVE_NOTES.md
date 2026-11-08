# Solve work log

I had not opened any generator, Racket rule, canonical answer, prior solution, or audit evidence before this solve. I used only the prepared visible challenge.

## Revision 1 — concentric frame regions

Hypothesis: the nonzero singleton cells other than color 8 are an ordered palette. Color 8 draws rectangular frames. Each palette color fills the region immediately inside the corresponding concentric frame but outside the next concentric frame. A deeper frame with no corresponding palette entry protects its interior, which remains unchanged. A centered ladder with an internal crossbar is not another rectangular frame, so its enclosed cells stay in the outer region.

Probe: I compared connected color-8 components with their bounding-box outlines. The first and third training examples contain concentric outline components; the slightly damaged inner frame differs from its ideal outline by one missing boundary cell and one extra interior cell. The second example's centered ladder has five interior 8 cells, so treating it as a frame would incorrectly use the second palette color.

Implementation: detect 4-connected color-8 components that are exact rectangular outlines or have at most one missing boundary cell and one interior displacement; keep the nested components sharing the largest frame's center; color each annular region from outside inward. Remaining uncertainty is whether hidden instances permit more than one displaced wall cell.
