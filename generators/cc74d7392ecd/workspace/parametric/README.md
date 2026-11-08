# Proposed orthogonal/diagonal seed-neighborhood family

This task-local prototype keeps the source puzzle's causal operation: every
nonzero seed preserves its color and grows a radius-one neighborhood, clipped by
the canvas. The episode-fixed `neighborhood` parameter chooses:

- `orthogonal` — the exact canonical cross (default), using the selected Racket
  program byte-for-byte;
- `diagonal` — an X consisting of the seed and four diagonal neighbors.

The production generator, rule authority, approval, and training admission are
unchanged. This family is proposed authoring evidence only.

## Focused replay

From the packet directory containing `review.py`:

```bash
python3 review.py run python3 -m pytest -q \
  generators/cc74d7392ecd/tests/test_parametric.py
```

The adapter supports exact integer seeds in `0..2**63-1`, 2–6 demonstrations,
and 1–4 queries. Inputs are setting-neutral and split/index keyed: changing the
setting changes labels only, adding demonstrations preserves earlier examples,
and requesting one query gives the same first query as requesting four.

The four-query schedule is 7×7, 16×20, 23×29, and 30×30. The 30×30 scene has 24
seeds spanning all four boundaries and at least five colors; it is not a padded
small puzzle. Seed centers are separated so the two declared neighborhoods do
not overlap. Demonstrations include clipped corner/edge cases and distinguish
the two exact Racket programs from labels alone.

For protected-Racket evidence, use the repository's native worker or, after the
source/evidence manifest is current, the owner qualification workflow documented
in `docs/parametric-promotion.md`. Public model turns should be projected with
`reviewer_support.public_challenge_bytes`, exposing all demonstrations and only
one query input; settings, programs, answers, future queries, and query counts
remain controller-side.
