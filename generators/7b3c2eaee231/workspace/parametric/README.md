# Tallest-color packing axis — proposed parametric family

The default `canonical` setting is byte-for-byte the selected source rule: crop
three monochrome objects, sort by `(width, height, color)`, and center-pack them
horizontally with one-column gaps.

The alternative `tallest_color_axis` setting adds a genuine input-dependent
composition. Step A selects the tallest object (width and color break otherwise
unsupported ties) and exposes its color. Step B consumes that color: an even
controller uses the canonical horizontal packing, while an odd controller sorts
by `(height, width, color)` and center-packs vertically. Every two-demonstration
lesson contains one even and one odd controller, ruling out both an always-
horizontal and an always-vertical shortcut. Inputs are sampled independently of
the setting and of the requested query prefix.

The authoring grammar keeps exactly three separated, distinct-color connected
objects. It includes tie-break cases, varied morphology and placement, and a
30×30 query with large objects distributed across all three vertical thirds.
The family is proposed only; native owner review, qualification, acceptance and
training admission remain separate.
