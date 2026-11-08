# Workspace for 901c6034f67e

The selected implementation is `../generator.py`. Workspace scripts are review
tools and are never automatically selected as generators.

## Quick cyclic-window probe

`probe_lessons.py` uses the actual default sampler and iterates the generator's
current `LESSON_COMPETITORS` declaration. For every start position, it treats
three consecutive samples as demonstrations and the fourth as the query. It
records source hashes, observed profiles/palettes, unique inputs, per-rival
refutation counts, and complete window records.

Run from the extracted packet root:

```bash
python3 run_with_racket.py python3 \
  generators/901c6034f67e/workspace/probe_lessons.py \
  --starts 18 --out ../checks/cyclic-probe-new.json
```

A zero exit means every measured demonstration window refuted every currently
declared rival. It is a fast Python-mirror regression, not a replacement for the
Racket authority battery or the shared source-bound lesson census.

## Full source-bound census

```bash
python3 run_with_racket.py python3 -m arcpuzzles lesson-census \
  901c6034f67e --per-band 100 --timeout 1800 \
  --out ../checks/lesson-census-final-v311.json
```

The census supplies Racket-bound labels and production episode assembly. Neither
tool proves universal learnability; add a concrete rival and witness before
claiming a newly suspected shortcut is repaired.
