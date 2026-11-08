# 56e5ade4e829

Version `3.0.0` generates canonical-profile zero-background grids containing one connected color-1 shape, one connected color-2 shape, and one isolated singleton marker. Each operand is normalized to its own bounding box. Marker 3 selects intersection, marker 4 selects union, and markers 5–9 select symmetric difference; the nonempty result is cropped and painted color 8.

The production lesson uses five demonstrations plus one query. A period-three control schedule ensures every six-example window contains two examples of each operation, and every query rotation leaves all three operations demonstrated. Both partial-overlap and strict-subset operand relations are generated; all three candidate operation outputs are required to be distinct.

Exact controls: `grid_h=8..10`, `grid_w=10..13`, `ctrl=0|1|2`, and `relation=partial|subset`. All advertised overrides are observable and validated. The selected Racket program remains the canonical label authority; only source-comment drift was removed.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
