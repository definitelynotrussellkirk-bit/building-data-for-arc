# 9792326ad0cb

0-bg grid (h~9-11, w~10-13) with: (a) ONE 3-BLOB TEMPLATE — a connected blob of COLOR 3 (size 2-4) grown randomly and placed at a non-touching position; (b) 1-3 COLOR-4 SINGLETON ANCHORS — single 4-cells at positions where the TEMPLATE'S BBOX would fit without going out of bounds or overlapping the template. Rule (STAMP TEMPLATE (IN COLOR 8) AT EACH 4-ANCHOR ON A FRESH GRID): identify the TEMPLATE (largest COLOR-3 connected component) and its NORMALIZED SHAPE (cells with min row/col offsets = 0). PRODUCE a NEW BLANK h × w GRID. For EACH ANCHOR (COLOR-4 cell) at (ar, ac): STAMP the template's shape with the anchor as top-left corner, painting each stamped cell with COLOR 8 (cyan). The original template and anchors are discarded. Net: a fresh canvas with cyan copies of the template at each anchor's location.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
