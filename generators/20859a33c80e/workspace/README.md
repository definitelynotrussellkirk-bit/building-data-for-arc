# Reusable lesson diagnostics

The selected implementation is `../generator.py`. These tools read that adjacent
source, record its SHA-256, and iterate its actual `CANONICAL_SHORTCUTS` and
`LESSON_COMPETITORS`; they do not silently use a copied registry.

## Consecutive-window census

From the extracted packet root:

```sh
python3 run_with_racket.py python3 generators/20859a33c80e/workspace/lesson_probe.py --seeds 20 --out ../checks/my-lesson-probe.json
```

For each band and seed 0–19, draw indices 0–14; examine starts 0–9 with five demos
and one query. This is 200 overlapping lessons per band, 600 total, derived from
900 draw occurrences. Report exact unique-input hashes, witnesses, competitor
survival and query disagreements. The independent global-color diagnostic catches
a rival missing from the old registry. Labels here come from the Python mirror;
this is not a Racket measurement. **Exit zero means the census ran, not that it
found no problems.** Inspect `accepted_ambiguous_lessons`, `hook_rejected`,
`selfcheck_failures`, `strict_failures`, and all canonical-shortcut match counts.

The ten starts exhaust the scene/color schedule, not all possible layouts or the
combined seventy-position size-anchor cycle. The focused tests separately check
every size-anchor scene/color combination. Local windows overlap and must not be
reported as independent trials.

## Public sampler and Racket verification

```sh
python3 run_with_racket.py python3 generators/20859a33c80e/workspace/verify_public_lessons.py --count 100 --seed 1000 --out ../checks/my-public-lessons
```

The output directory must not already exist. Calls the public `Catalog.generate`
API, with `allow_unapproved=True` explicitly for research, canonical Racket labels,
5 demos, 1 query, requested start index 0, and seeds 1000–1099 in each band.
Retains complete episodes, rejections, accepted sample indices, source/rule hashes,
and episode-file hashes. Checks every pair against the Python mirror and both
validators; checks the lesson hook and every declared rival. Returns nonzero on
reported failures; source/rule identity mismatches raise an assertion. Rejections
and nonconsecutive accepted indices are reported rather than automatically errors.
This does not change catalog approval or implement a shared training-export gate.

## Focused regressions

```sh
python3 run_with_racket.py python3 -m pytest generators/20859a33c80e/tests -q
```

The root suite and standard battery do not discover these 37 tests automatically.
Retained frozen fixtures also need their separate selected portable runtime run;
new workspace/test files are not silently included by portable preparation.

## Measured limits

The 3.1.0 final review had zero accepted ambiguities in 600 local windows and
zero mirror/validator/lesson errors in 300 public-sampler lessons (1,800 Racket
pairs, 1,570 distinct inputs across bands). Shared 11×11 anchors explain some
cross-band duplicates. This is bounded evidence against a finite rival set, not
proof of arbitrary-rule identifiability or a measured model-training gain.
