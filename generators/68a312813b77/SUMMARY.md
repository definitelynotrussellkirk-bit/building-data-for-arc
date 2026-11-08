# 68a312813b77

A 0-background grid contains one to five separated, monochrome, non-rectangular 8-connected objects. Every default scene includes both a bbox touching the canvas boundary and a fully interior bbox. For each component, fill every background cell in its own bounding box with color 7 while preserving the original object cells.

Kind: `per_puzzle`. Current version: `2.3.0`. Canonical rule hash: `0515ffa9320e`.

The generator selects a feasible `(grid_h, grid_w, n_objects, size_distribution)` tuple before drawing unspecified axes, then uses cached constructive shelf layouts instead of exponential backtracking. It realizes valid single-axis controls, reports incompatible multi-axis geometry with named axes, and refutes the former `skip_boundary`, converse `boundary_only`, and one-global-bbox shortcuts.
