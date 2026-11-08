# Orbit, then trace to the first hit

This native prototype preserves the selected canonical program exactly at
`{"links":"none"}`. `{"links":"first_hit"}` first places the original motif
north of the unique maroon marker and its successive clockwise quarter-turns
east, south and west. It then traces four cardinal rays in the **rendered**
collage, painting intervening zero cells maroon and stopping before the first
occupied cell. The hit and all cells behind it remain unchanged. Rotation and
relocation determine those stopping cells; the original source position does
not. The no-hit fallback paints nothing, although the connected sampled motif
guarantees hits in the correctly rendered four arms.

## Native API and domain

`adapter.program(settings)` returns complete Racket source.
`adapter.generate(seed, settings=None, demos=3, queries=4)` returns private
labeled pairs and `program_solution`. A missing setting selects deterministically
by seed parity; explicit settings require exactly the `links` key.
Seeds are exact integers 0..2**63-1; demonstrations 3..6 and queries 1..4 are
independent exact-integer requests. Booleans and floats are rejected.

Inputs are square 9..30, background 0, one marker 9, and one four-connected
single-color motif using 1..8. It spans at least two rows/columns and has four
distinct rotations; its bounding box excludes the marker. All four rendered
nonzero copies must be in bounds and mutually disjoint, including the marker.
This extends only the prototype: unchanged production remains 9..15 with a
3..5-cell motif within 3×3 and eight demonstrations.

The full six-demo/four-query bank is built before slicing. Local SHA-derived RNG
streams separate demonstrations from queries and are independent of settings.
The mandatory three demonstrations show an off-center marker and displaced north source,
a deep-notched southern diagonal source, and an even-width source on the
opposite horizontal side. Together they teach all four source half-planes,
long links, zeros behind a blocker, and unequal opposite ray lengths.

Query sizes are 13, 21, 26 and 30 in independently shuffled order. The 30×30 query
has a 12×3 asymmetric comb with at least 22 occupied motif cells; its four
copies span 27×27 and touch the canvas boundary. Other motif sizes, palettes,
source sectors, markers, branches and occasional enclosed holes vary. The
constructive large-shape grammar deliberately favors tall narrow motifs; it
is not an unrestricted topology sampler.

## Run and inspect

From the packet outer directory, use its ready Python interpreter:

```sh
WORK/.venv/bin/python review.py run python3 generators/7fe59337a0b4/workspace/parametric/audit.py --out ../checks/7fe59337a0b4/audit-new
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 7fe59337a0b4 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/7fe59337a0b4/qualification-new --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/7fe59337a0b4/qualification-new/qualification.json --out ../checks/7fe59337a0b4/preview-new
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/7fe59337a0b4/preview-new
```

A current native manifest is required before qualification. Use the existing
`arcpuzzles parametric manifest` helper to refresh it after code changes;
its replacement guard requires the exact old manifest hash. Existing output
directories are refused.

`audit.py` is a reusable protected-Racket demo-only rival audit. It records
private full episodes, competing programs, first demo refutations, surviving
query conflicts, runtime identities and exact source hashes. It never treats
a runtime error as evidence of refutation. The companion checks scripts retain
maximum-count/seed labels and negative saved-public-view probes.

## Teaching repair and limits

The original seed 17 lesson had sources N, NE, E. A wrong rule reversing rotation
only for sources below the marker fit all three demonstrations under both settings and changed
12 cells on its 13×13 query. The full Racket-confirmed lesson is retained in
`checks/7fe59337a0b4/self-review-below-source-v1.json`, with the original sampler
source. The revised three-demo bank closes that half-plane gap; all four conditional
reverse-turn rules are now explicit audit rivals. The initial narrower audit
is superseded by the final expanded audit.

Finite rivals and seeds do not establish universal rule uniqueness. The
prototype does not claim production's eight-profile rotation-safe lesson hook.
Only one hash-named file under a preview's `public/` is a model-visible turn;
the bundle listing and private receipts contain future queries and answers.
Single-query and four-query use have the same first visible turn. Serialized
projection verification does not replay Racket or authenticate an adversarially
rewritten private receipt. Reviewer qualification requires separate owner
acceptance of the exact integrated source; training admission remains false.
