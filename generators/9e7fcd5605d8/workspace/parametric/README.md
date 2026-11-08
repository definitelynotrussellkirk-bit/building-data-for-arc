# Enclosed-region thresholds

This opt-in native family preserves the canonical topology puzzle and adds
`min_holes=2`. Each same-color 4-connected object is recolored cyan (8) when it
encloses at least the episode's threshold of 4-connected background regions;
otherwise it becomes yellow (4). Shapes and black background stay unchanged.
The `min_holes=1` program is the exact selected canonical source, including its
original bytes. Production `generator.py` and the canonical ledger are unchanged.

## Run it

From the packet directory containing `review.py`, using its prepared interpreter:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/9e7fcd5605d8/workspace/parametric/verify.py \
  --out ../checks/9e7fcd5605d8/new-self-review
```

Choose a fresh output directory. The verifier executes labels and finite rivals
through protected Racket and writes private four-query examples, a compact
self-review receipt, and hash-named first-query public challenges.

Native adapter calls are `program(settings)` and
`generate(seed, settings, demos=3, queries=4)`. Settings are exactly
`{"min_holes": 1}` or `{"min_holes": 2}`. Supported counts are 2–6 demonstrations
and 1–4 queries independently. Seeds are exact integers in `0..2**63-1`.
The sampler's outputs are Python claims until independently executed by the
verifier or native worker; the retained examples contain executed labels.

The native owner gate after source intake is:

```bash
python3 -m arcpuzzles parametric qualify 9e7fcd5605d8 \
  --demos 3 --queries 4 --out var/review/topology-qualification --summary
python3 -m arcpuzzles parametric accept 9e7fcd5605d8 \
  --qualification var/review/topology-qualification/qualification.json \
  --reason 'Reviewed topology thresholds, grammar and source-bound evidence'
```

Reviewer qualification does not constitute owner acceptance or training admission.
Rebuild the native evidence manifest and rerun qualification after source edits.

## Teaching and causality

Stage A segments each object's bounding-box complement, removes regions that
reach its rim, and derives the number of enclosed regions. Stage B uses that
input-dependent count to choose the whole object's output color. A large open
concavity and a closed cavity can have the same missing-cell count yet require
different output colors. Replacing enclosed-region count with missing-cell count
is the recorded wrong-intermediate ablation; merely counting vacant pixels is
insufficient.

The first demonstration includes an open concavity, a large single cavity,
diagonally adjacent separate cavities, and three holes. All objects share one
color, so input color cannot identify the output class. The second demonstration
adds a diagonal escape, an exterior bay, and a different distribution of hole
counts. These contrasts fit within two demonstrations. Additional demos vary
geometry, placement, cavity area, rotation/reflection, and colors.

The finite rival set checks wrong thresholds, non-full bounding boxes, missing
cell count, enclosed area, rim inclusion, 8-connected background, exact counts,
and constant labels. Positive enclosed area and positive enclosed-region count
are equivalent at threshold one; that survivor is reported as equivalent rather
than falsely refuted. Finite checks do not establish universal rule uniqueness.

## Sampling and visibility

Input RNG streams depend on seed, split and pair index only. Both settings get
identical inputs, and changing demo/query counts preserves existing prefixes.
The first query is 11×11; the four-query schedule also uses 18×24, 24×21 and
30×30. Large scenes contain 12–16 objects across the canvas, including edge
contacts and independently varied colors and hole counts. All inputs are distinct
within an episode and every query contains a one-hole object, where settings differ.

Objects remain separated monochromatic components. Nested or touching multicolor
scenes are outside the sampler. Foreground-connectivity alternatives that agree
on this grammar are not claimed to be distinguished. This is topology inference
followed by a conditional recolor, not a claim of iterative state simulation.

All four queries and their answers stay in controller-side private examples.
The retained public artifact projects demonstrations plus the first query input
only, with no setting, seed, program, future-input or total-count hint. Its name
is the SHA-256 of exactly the visible bytes. The existing consumer must continue
to reveal later query inputs one at a time; the native all-query export is a
controller artifact, not the initial model prompt.
