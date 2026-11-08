# d1bf9a8e4c69 — show every component's bounding-box corners

Generator version `3.0.0`; rule hash `dc30ef9952c0`.

For every nonzero 4-connected component, erase the component and paint exactly the four corners of that component's bounding box in the component's original color. Connectivity, not color identity, defines an object: two separated objects may deliberately share a color and must still be transformed independently.

## Generated domain

- Grid height: 8–13; width: 9–14.
- Two to four orthogonally separated objects.
- Shape families: L shapes, zigzags, irregular connected shapes, or a mixed scene.
- Palette patterns: all-distinct colors or exactly one separated repeated-color pair.
- Every object spans at least two rows and columns and contains both a non-corner cell to erase and a missing bounding-box corner to add.
- A deterministic four-profile schedule makes every consecutive two-example lesson include a mixed-shape scene and a repeated-color scene.
- Half of default draws use one of the three canonical size/object-count profiles so every difficulty band retains canonical-scale support.

The exact public override axes are `grid_h`, `grid_w`, `object_count`, `shape_family`, and `palette_pattern`; unknown overrides are rejected. There are no declared texture axes.

## Teaching contract

The canonical examples are compatible with the shortcut “merge all cells of each color and use one bounding box per color,” because their objects have distinct colors. Generated repeated-color pairs refute that shortcut. The semantic contract also checks identity, retain-existing-corners, bbox-outline, solid-bbox, and L-shapes-only rivals. `EXAMPLES_NEEDED = 2`, and every cyclic two-example schedule window refutes every named competitor.

Measured final evidence for generator SHA-256 `458e1558ab9ada63796e1b5ab6a9601f4bd28094c0687140aedf17390105c86b` is in `../../../checks/final_distribution_probe.json` and `../../../checks/after/`. The selected implementation is `generator.py`; the imported baseline is preserved in `workspace/baseline_generator.py`.
