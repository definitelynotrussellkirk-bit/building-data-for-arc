# 5f44ead2dbcd

0-bg grid (h~12-16, w~12-17) with: (a) a SCALE CONTROL at (0, 0) — color 1 means scale-factor 1 (keep size), other (color 2) means scale-factor 2 (2×2 upscale); (b) a ROTATION CONTROL at (0, 1) — color 3 means rotate 0°, 4 means 90° CW, 5 means 180°, else (color 6) means 270° CW; (c) a small color-7 (orange) TEMPLATE polyomino somewhere in the top-left region; (d) a single color-8 (cyan) ANCHOR cell placed somewhere with room. Rule: (1) NORMALIZE the template's cells. (2) UPSCALE by the scale factor (each template cell becomes a k×k block). (3) ROTATE by the rotation count. (4) PAINT the resulting shape in color 7 onto a BLANK CANVAS at the anchor's position (anchor becomes the shape's top-left). Net: only the transformed orange shape remains, stamped at the cyan anchor location, on an otherwise-empty grid.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
