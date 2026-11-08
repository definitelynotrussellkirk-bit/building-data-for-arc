# b35301a51180

Fixed 11×9 0-bg grid with HARDCODED LAYOUT: (a) TWO HOLLOW 3×3 RINGS in TARGET COLOR (from {1..8}) at (1..3, 1..3) and (5..7, 4..6); (b) ONE HOLLOW 3×3 RING in OTHER COLOR at (8..10, 1..3); (c) ONE SOLID 2×2 BLOCK in OTHER COLOR at (2..3, 6..7). Hardcoded positions × ~8 × ~7 color choices = ~31 unique configs (HARDCODED-LOW). Rule (MOST-COMPONENTS COLOR's HOLES → 9): identify the COLOR with the MOST 4-conn COMPONENTS (target color has 2 components, other has 2). With tiebreak picking target. For each COMPONENT of that color, fill its ENCLOSED HOLE (interior 0-cells) with COLOR-9 (maroon). Other components, solid blocks unchanged. Net: most-component color's hollow rings get maroon centers.

Kind: `per_puzzle`. Imported version: `2.2.1`.
Approval is derived by the catalog from current code and retained evidence.
