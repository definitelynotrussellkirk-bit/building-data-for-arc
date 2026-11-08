# 72a261e69372

Generate an 11–18 by 13–20 color-0 grid containing two or three distinct-color rectangular roles and color-1 markers. Two complementary scene families teach the exact rule:

- **Nested:** two or three intact same-color connected rectangular outlines are nested. Each tier has a marker in the region for which that tier is the smallest enclosing outline.
- **Overlap:** a later intact outline crosses and overwrites part of an earlier outline. The earlier color is therefore only an occluded outline fragment, not an exact frame; its orphan marker remains color 1. Other markers are recolored by the intact frames that enclose them.

For every color-1 marker, find all **intact same-color 4-connected rectangular outlines** that strictly enclose it. Recolor the marker to the color of the enclosing outline with the smallest area. If no intact outline encloses the marker, leave it color 1.

The generator exposes exact controls for `grid_h`, `grid_w`, `n_frames`, `layout_kind`, and `palette_kind`; rejects unknown or invalid controls; and alternates nested/overlap defaults so every four-demo lesson contains both decisive scene types. Its executable semantic contract refutes two canonical shortcuts: treating a color's bounding box as a frame after occlusion, and choosing the outermost rather than smallest enclosing frame.

Kind: `per_puzzle`. Selected version: `3.0.0`. Canonical rule hash: `d763a0664108`.
Approval is derived by the catalog from current code and retained evidence.
