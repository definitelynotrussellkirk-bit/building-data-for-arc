# Workspace for e42b0a4cc753

The selected implementation is `../generator.py`; workspace modules are reviewer tools and are never selected automatically.

## `voronoi_probe.py`

An independent Manhattan-Voronoi oracle and rival library. It deliberately does not import the production generator. Available helpers include:

- `frame_bbox` and `seed_cells`;
- nearest-seed ownership under Manhattan, squared Euclidean, or Chebyshev distance;
- fills using reading-order, reverse-reading, lower-color, or higher-color tie rules;
- owner counts, tie cells, metric-disagreement cells, and output-disagreement cells;
- ready-made lower-color, ignore-after-first-two, and Euclidean rivals.

The task tests load this file directly, which prevents the generator from proving itself correct solely through shared implementation code. It is also suitable for future shortcut probes on canonical or generated grids.
