# 0b999a8ea028

Select the largest non-blue 4-connected component as the prototype. Treat only
color-1 components that exactly equal a rectangular border as frames. Rebuild a
blank output and stamp the prototype's normalized shape, in its source color,
centered with quotient/floor bias inside every frame interior. Erase frames,
source objects, decoys, and malformed blue components. With no exact frame, the
output is blank.

The v3 generator uses a four-example deterministic curriculum:

1. `canonical` — one 3/4-cell prototype and two or three exact 5x5 frames;
2. `size_contest` — an earlier 2-cell decoy, a later 5-cell prototype, and a
   7x7 frame, jointly refuting first-object, fixed-5x5, and top-left-placement
   shortcuts;
3. `nonframe_blue` — one exact 6x6 frame plus a one-cell-broken 5x5 blue ring;
4. `no_frames` — one connected composite of two apparent blue frames, producing
   a blank answer.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical rule pin:
`d8a130fd2a56`.
