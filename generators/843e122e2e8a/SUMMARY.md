# 843e122e2e8a

0-bg grid (h~10-14, w~11-16) with THREE OBJECTS, each a RANDOM POLYOMINO of a DISTINCT area (areas sampled distinct from 2..6) in a DISTINCT non-bg colour, scattered at non-overlapping buffered positions. Rule (CROP EACH OBJECT, PACK LEFT-TO-RIGHT BY DESCENDING AREA): extract every 4-connected non-bg component, crop to bbox, sort crops by area descending (ties per demos), pack left-to-right with bg gaps, bottom-aligned, into a tight output grid. Net: 3 scattered objects collapse into a horizontal pack ordered biggest-to-smallest; varied shapes+colours make the pack differ per sample.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
