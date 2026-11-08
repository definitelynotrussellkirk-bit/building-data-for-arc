# Parametric phase-anchor prototype

This proposal keeps the canonical `source`-anchored vertical tiling program byte-for-byte and adds one episode-fixed alternative, `grid_top`, which begins the period at output row zero. The constructive grammar always places a 2–5-row source block away from both borders and deliberately chooses a placement where the two anchors disagree. Thus even the minimum two demonstrations identify the setting without query labels.

The native adapter contract is in `promotion.json`. Generated episodes support 2–6 demonstrations and 1–8 independent queries; the retained review evidence uses four queries, including a content-bearing 30×30 case. `phase_anchor.py` contains a protected-Racket batch runner and certificate helper. This is a prototype only and does not alter canonical authority or imply training admission.
