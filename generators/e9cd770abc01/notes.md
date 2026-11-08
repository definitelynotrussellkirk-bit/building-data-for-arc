# Working notes: e9cd770abc01

## 2026-10-26 parametric build, adversarial round 2

The production generator and exact canonical rule remain unchanged. The native family is under `workspace/parametric/`:

- `paint_scope=nearest_only` is the exact canonical rule: select the color-3 component whose bounding-box center minimizes Manhattan distance to the grid center (bbox lexicographic tie-break), then repaint only that component 7.
- `paint_scope=nearest_size_class` preserves that selection as step A, binds the selected component's occupied-cell count as the input-dependent intermediate, then repaints every color-3 component with that count as step B.

The constructive teaching pair now checks 14 declared alternatives: Euclidean and centroid-Euclidean selection; first, last, smallest, largest, and nearest-cell object selection; paint-all and fixed-size rules; bbox-area/dimensions and normalized-shape equivalence classes; and at-least/at-most selected-size thresholds.

A broader search found two selectors—centroid Manhattan and nearest bbox edge—that fit the demonstrations. They also produce exactly the same answers as the intended selector on every generated query in the audited domain. They are therefore retained as explicit `SHADOW_SELECTORS`, not misreported as distinguished rivals. The probe now fails if a shadow selector fits the demonstrations but changes any generated query.

Fresh bounded evidence:

- 43 focused behavioral tests pass, including seven-seed checks of all added selector/class rivals and both shadow selectors.
- `probe.py` passes 70/70 jobs over seeds `0,1,2,9,17,23,100`, both settings, demo counts 2..6, and four queries.
- All 14 declared rivals are rejected from demonstrations alone; both demo-equivalent shadow selectors are query-safe with zero disagreements.
- Settings share inputs, query prefixes are stable, and the largest query is a content-bearing 30×30 canvas.

Source inventory: `workspace/parametric/evidence/manifest.json`.
Protected-Racket preflight, causal witness, public projection, and first-turn receipts are regenerated after this source inventory in the return package. Those are authoring evidence only; owner review, native acceptance, and training admission remain pending and are not claimed.
