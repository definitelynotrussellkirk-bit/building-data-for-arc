# Canonical lesson curator (opt-in proposal)

`lesson_curator.py` repairs a labeled **three-demonstration, one-query** lesson
for this task. It preserves the query exactly, executes the canonical Racket
rule to verify every supplied label, and replaces demonstration pairs only when
their replacements improve support against the two existing named rivals:
`globally_unique_seeds` and `translate_copies`.

The exported lesson must refute **both rivals in every single-query holdout**.
With four pairs this means at least two distinct refuting pairs per rival, so
holding either out still leaves a refuting demonstration. This is a finite
policy; it does not establish unique induction against all conceivable rules.

## Run from the outer packet directory

```bash
WORK/.venv-review/bin/python review.py run ../.venv-review/bin/python \
  generators/dc2c4869445c/workspace/lesson_curator.py \
  --lesson generators/dc2c4869445c/counterexamples/review-7d25a1f0d766d596/production-ambiguity.lesson.json \
  --seed 1776932124 --difficulty easy --start-index 29 --max-attempts 128 \
  --out ../checks/my-curated-lesson
```

Use a new output directory. The existing public lesson-census can produce other
labeled inputs. Pass a plain JSON object containing only `train` and `test`, with
three and one labeled pairs respectively; each pair contains only `input` and
`output`. A wrong saved label is an error, not silently relabeled evidence.

The callable `curate_lesson(lesson, *, seed, difficulty="easy", start_index=0,
max_attempts=256, executor=None)` returns `public`, `private` and `report` objects.
An optional actual `RuleExecutor` lets a batch reuse one Racket process. The
CLI's default is 256 candidate draws; an explicit zero bound is useful to verify
already-supported lessons without drawing replacements. Negative integer seeds
remain supported by the selected generator.

## Selection and failure behavior

Original input pairs must be distinct. Every candidate's input is checked against
all original and previously seen inputs, including the frozen query. A candidate
is drawn from the unchanged generator at the supplied seed and successive sample
indices, checked against the original domain, and labeled by actual canonical
Racket. It can replace one of the three demonstrations only when the capped
number of refuting pairs increases. Ties resolve by demonstration order.

The selection is deterministic and bounded. A candidate may be rejected for a
duplicate input, generation/domain failure or no coverage gain. Sampling
exhaustion refuses export and retains its attempts/rejections; no query changes,
extra demonstrations, truncated episodes or Python-generated labels are used.
Rival errors, input mutation, inconsistent repeated predictions, missing rivals,
and label mismatches also refuse export. The final exported lesson is rescored.

A successful directory contains `public.json` (demo labels and unlabeled query),
`private.json` (all four labels), `report.json`, and exact canonical raw/callable/
bridge-definition Racket files. The report binds source and program hashes,
input-lesson bytes, accepted/rejected indices, before/after production and
rotation judgments, actual Racket label calls and runtime identity. Failure
receipts distinguish unsupported lessons from completed exports.

## Measured scope and adoption

The raw 300-lesson census found 11 original-order ambiguities and 44 ambiguous
rotations, all from global rather than local seed-color roles. Another 27
four-pair sets contain no example refuting that rival, although it agrees with
all four labels. The return's independent batch keeps the 229 already-strict
sets and applies this policy to the other 71, then checks their labels again
through the public Racket controller. See `checks/lesson-curator/` and REVIEW.md
for actual final results; original failures remain under `checks/lesson-census/`.

This tool is separate from default production generation and does not modify
approval or training-admission state. Its selection favors distinguishing
color-role examples and changes lesson distribution. The accepted domain still
excludes clipping, so the all-or-nothing clipping rival cannot be distinguished
here. The gap prototype is a different proposal and has a different rival set.
