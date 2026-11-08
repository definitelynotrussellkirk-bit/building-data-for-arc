# 7ef325b21961

0-bg grid (h, w~14-24) with 1-3 CLOSED SINGLE-COLOR RECT FRAMES of dims 5-8 each at non-overlapping interior positions (with 1-cell padding). EACH FRAME has INTERIOR DOTS at scattered positions: n_maj cells of MAJORITY color + n_min cells of MINORITY color (n_maj > n_min, both in non-frame colors). Plus 0-6 DISTRACTOR NOISE cells OUTSIDE all frames in colors not used by any frame. Rule (FILL FRAME INTERIORS WITH MAJORITY DOT COLOR, ERASE DISTRACTOR NOISE): For EACH FRAME: keep the BORDER. Identify the MAJORITY DOT COLOR (most common non-frame, non-0 color among interior dots). FILL the entire INTERIOR with the majority color (solid). All DISTRACTOR NOISE OUTSIDE frames is ERASED to 0. Frame borders stay. Net: frames keep borders, interiors become solid with majority color, outside noise gone.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
