
# L-ray crossing postprocess family

`postprocess=none` is the byte-exact canonical L-tromino ray rule. The
`mark_crossings` setting executes that ray stage first, then detects input-empty
cells where same-color rays of both diagonal orientations cross and paints a
color-9 plus centered there. Inputs are matched across settings, contain a
constructed crossing in every lesson, support 2–6 demonstrations and four
independent queries, and include a substantive 30×30 long-ray query.

The required dependency is: **A** extends all L rays; the private intermediate
is the resulting ray grid and its crossing coordinates; **B** reads that grid
to find two-orientation crossings and mark them. The retained skip-A program
cannot see those crossings and changes the final output.

At the two-demonstration minimum, crossing centers follow a seed-shuffled,
without-replacement schedule over all nine offsets in the 3×3 neighborhood of
the geometric center. This prevents a fixed-center or fixed-near-center marker
from fitting both demonstrations while preserving deterministic matched inputs.
A bounded audit over 128 seeds observed all nine offsets and independently
replayed 72 generated labels through protected Racket.
