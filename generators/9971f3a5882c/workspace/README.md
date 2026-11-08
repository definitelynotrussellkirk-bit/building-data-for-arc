# Workspace: 9971f3a5882c

The selected implementation is `../generator.py`. Workspace files are support tools only and are not automatically selected.

## `lesson_probe.py`

This task-local probe checks explicit consecutive schedule starts. The shared
Racket-backed lesson census separately checks the production sampler. This probe:

- loads rival functions dynamically from `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS`;
- verifies every declared rival against all usable canonical pairs;
- materializes four-example windows beginning at all 60 joint profile phases
  (canvas period 5, lattice period 4, marker period 12), without wrapping sample indices;
- rotates each of the four positions into the query role;
- requires the remaining three demonstrations to refute every declared rival;
- reports exact generator SHA, profiles, witness coverage, failures, and unique-input hashes.

Run from the outer packet root:

```bash
python3 review.py run python3 \
  generators/9971f3a5882c/workspace/lesson_probe.py \
  --seed 7331 \
  --out ../checks/consecutive-lesson-probe-replay.json
```

The default checks 960 rotations: 60 starts × four bands × four query positions.
An explicit shorter `--period` is allowed and reports partial profile coverage.
The period describes profile choices; exact grids depend on the full sample
index. A fixed seed does not establish coverage over all random layouts.

The portable selected-source loader also supports a retained copy under a
packet's `checks/` directory. The probe's generated outputs use the independent
Python mirror for speed. The standard aggregate battery and `lesson-census`
separately bind the same final generator bytes to the selected canonical Racket
rule. A probe pass means the declared finite rivals are eliminated under the
tested query rotations. See `parametric/README.md` for the separate proposed
rule extension and its exact Racket verification.
