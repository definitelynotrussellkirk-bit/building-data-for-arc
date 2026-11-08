# Parametric horizontal-sandwich family

Status: reviewer-ready proposal; owner exact-source acceptance remains required.
The production generator and selected canonical authority are unchanged.

Each episode fixes one private `completion` setting while sharing identical
inputs across settings:

| setting | rule |
| --- | --- |
| `horizontal_all` | fill every equal-color horizontal sandwich; exact canonical default |
| `ranked_vertical` | fill the canonical horizontal sandwiches, count them, then fill the same-ranked vertical sandwich in row-major order |

The family supports 2–6 demonstrations and 1–4 independently requested,
prefix-stable queries. The first two demonstrations use horizontal counts two
and four and reject fixed-rank, first/last, row-count, color-count, reverse-rank,
all-vertical, and candidate-color-extreme shortcuts. Four queries cover
15×17, 20×22, 25×27, and a substantive 30×30 scene with all four boundaries,
dense distractor blocks, four possible horizontal counts, and six vertical
candidates.

Sequential dependency: step A finds and completes the canonical horizontal
sandwiches; their input-dependent count is the one-based intermediate rank.
Step B cannot select which vertical sandwich to complete until that count is
known. The protected witness replaces the measured rank with rank one on the
same qualified input and changes two final cells.

Focused tests:

```bash
python3 review.py run python3 -m pytest \
  generators/dfc7297269cc/tests/test_parametric.py -q
```

The native qualification executes every claimed label through protected Racket.
Public projections contain only demonstrations and one masked query; settings,
programs, answers, future queries, seeds, and total query count remain private.
