# ee5ca325d03d

0-bg grid (h, w ~10-18) with 1-3 RED(2) OUTLINE shapes — rectangular outlines (or blob/nested/U/irregular variants), each enclosing ≥1 bg cell. Outlines have ≥2 bg-cell margin from grid edges. Optional sparse decoration cells (non-{0, 2, 3}) outside outlines. Rule: (1) fill all bg(0) regions enclosed by non-bg-reachable-from-border with color 3 (green) — i.e., any bg region NOT touching the grid border gets painted 3. (2) Recolor all 2(red) cells to 0 (bg). Net effect: outlines disappear, their enclosed interiors become green; outside-the-outline decoration cells remain unchanged.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
