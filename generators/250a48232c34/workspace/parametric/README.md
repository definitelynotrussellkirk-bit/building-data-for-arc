# `250a48232c34` rotation-direction family

`rotation_direction=clockwise` is the exact selected canonical Racket rule:
anchor colors 1, 2, 3 and 4 request 0°, 90°, 180° and 270° clockwise copies of
the largest gray template. `counterclockwise` keeps color 1/3 unchanged and
swaps the 90° roles of colors 2/4.

Inputs are matched between settings. Every scene contains an asymmetric source
template and all four anchor colors, with color-to-corner assignments shuffled
per scene. The adapter supports 2–6 demonstrations and 1–4 queries independently;
the four-query bank ends with a distributed 30×30 case using a 6–7 cell source.
`audit.py` checks a bounded set of direction, no-rotation, fixed-template and
wrong-turn rivals. Protected Racket preflight and the causal witness remain the
execution authorities.
