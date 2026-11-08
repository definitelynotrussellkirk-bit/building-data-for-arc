# Proposed parametric rotation prototype v2

This task-local authoring prototype varies one private episode-level setting:
`direction=ccw|cw`. The default `ccw` program is the exact canonical source,
`(rule! rotate-ccw)`; the alternate is `(rule! rotate-cw)`. It does not alter the
canonical generator, catalog, approval state, allocation, or training admission.

## Episode contract

- 2–6 demonstrations and exactly four queries.
- One direction is selected once and held fixed across the full episode.
- Inputs are distinct, rectangular exact-color grids with profiles from 3×5
  through a substantive 30×30 query; both square and nonsquare cases occur.
- Explicit settings use identical inputs for the same seed and counts.
- Authoring exports label every pair by executing the exact selected Racket rule.
- Demonstrations alone must leave the selected direction as the only declared
  survivor; query answers never participate in setting identification.

Generate and freshly replay two episodes from the outer packet directory:

```bash
python3 review.py run python3 \
  generators/864eaaac6503/workspace/parametric/rotation_episodes.py \
  --out ../checks/rotation-v2 --seeds 0 1 --demos 3 --queries 4
python3 WORK/check_public_exports.py WORK/checks/rotation-v2/public \
  --demos 3 --queries 4
```

The output path must not already exist. Public files are sorted and named by the
SHA-256 of their exact visible challenge bytes. They contain demonstration
inputs/outputs and query inputs only. Seeds, settings, programs, rival checks,
and query labels remain under `private/`. Duplicate visible challenges fail
before the destination is created, and `verify_batch` replays labels in Racket
and checks every public-byte/identifier binding.

`sequential_turn(episode, i)` is a controller-side projection. Turn zero is byte
identical to an ordinary single-query challenge; later turns expose only their
one query input, with no future-query, count, setting, or answer metadata.

## Native promotion boundary

`promotion.json` declares the finite setting and count bounds. `adapter.py` loads
`rotation_episodes.py` by its exact adjacent path and exports:

- `program(settings)`: exact Racket source for the setting.
- `generate(seed, settings, demos, queries)`: deterministic Python label claims.

The adapter intentionally does not start Racket. Native qualification executes
all claimed labels independently through protected Racket and requires the chosen
setting to be the sole demonstration survivor. The retained qualification used
both settings at seeds 0 and 17 with three demonstrations and four queries.

```bash
python3 review.py run python3 -m unittest \
  generators/864eaaac6503/tests/test_parametric_rotations.py -v
python3 review.py run python3 -m arcpuzzles parametric qualify 864eaaac6503 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/main-parametric-qualification
```

## Scope

Evidence is finite and checks only the declared clockwise/counterclockwise
family. Identity, half-turn, arbitrary programs, universal identifiability, and
measured learning benefit are outside scope. The current manifest is an
inventoried reviewer report; qualification is not acceptance, production use,
or training admission.
