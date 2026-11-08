# ee602abaa45a

A canonical 14/15×22–24 canvas contains two distinct rectangular frames. Each
frame holds **both** candidate templates (color 1 in the left 3×3 slot and color
2 in the right 3×3 slot), then a bottom selector cell and transform code
(3 identity, 4 rotate-CW, 5 rotate-180, 6 flip-LR). Select locally, transform
the tight crop, recolor it to the frame border, and h-stack the two pieces in
frame reading order, vertically centered with one blank column.

The four-profile schedule supplies explicit counterexamples to always choosing
one candidate, ignoring transforms, packing left-to-right instead of reading
order, and top-aligning instead of centering. Exact controls are restricted to
pixel-observable canvas, selector, code-pair, and order axes.

Kind: `per_puzzle`. Reviewed version: `3.0.0`.
