# Review workspace for 46580cfcca75

## `reference_oracle.py`

An independent visible-grid transcription of the canonical operation. It finds
same-color four-connected components and paints each component's tight bounding
box perimeter on a blank grid. It also provides the task-derived rivals used by
regression tests. It deliberately does not import `generator.py`.

## `lesson_probe.py`

A reusable source-bound probe for future reviewers:

```bash
cd repo
PYTHONPATH=shared/runtime python3 \
  generators/46580cfcca75/workspace/lesson_probe.py \
  --per-band 100 --seed-base 91000 \
  --out ../checks/46580cfcca75-lesson-probe.json
```

The probe loads the current generator, discovers its live
`LESSON_COMPETITORS` and `SEMANTIC_WITNESSES`, validates canonical parity against
the independent oracle, materializes consecutive four-pair windows in every
band, and holds out each pair once. The Racket battery remains label authority;
this tool is a cheap regression/curriculum probe, not a replacement for it.
