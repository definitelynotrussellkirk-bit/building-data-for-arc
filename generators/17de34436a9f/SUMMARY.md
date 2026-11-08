# 17de34436a9f — corner-cued crop rotation

A 0-background input contains exactly two non-background objects:

1. one maroon (`9`) marker in exactly one grid corner; and
2. one separate, 4-connected, single-color body of 4–7 cells.

Remove the marker, crop the body to its bounding box, and rotate that crop according
to the marker corner:

| Marker | Output transform |
| --- | --- |
| top-left | identity |
| top-right | 90° clockwise |
| bottom-right | 180° |
| bottom-left | 90° counter-clockwise |

Version `3.0.0` pins canonical rule hash `9f94f78b9fd2`. Ordinary lessons use a
canonical-like 9×9 profile, body sizes 4–6, and the deterministic four-example
corner schedule `tl → tr → br → bl`. Exact controls additionally support 7–14
rows/columns and body size 7. Generated bodies are compact asymmetric
polyominoes, so every scheduled rotation is observable.

The Racket authority was not changed. The Python rule mirror, named semantic
rivals, witnesses, and lesson probe are auxiliary review instrumentation.
