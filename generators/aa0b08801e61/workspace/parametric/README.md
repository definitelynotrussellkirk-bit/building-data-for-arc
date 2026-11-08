# Symmetry signal-rank parametric family

The default `selection=classify_all` is the exact selected canonical Racket
program: classify every nonzero four-connected object's tight mask by left-right
and up-down symmetry and recolor it 8/2/3/4. The alternative
`selection=signal_rank` keeps the same symmetry reasoning but adds an
input-dependent selector:

1. **A:** find the unique blue object and count its cells.
2. **Intermediate:** the count is a one-based rank among all non-blue objects in
   row-major component order.
3. **B:** select that payload, classify its tight-mask reflection symmetries, and
   paint only it with the canonical class color.

B cannot choose an answer object before A produces the rank. Inputs are identical
between settings for the same seed and count request. The first two demonstrations
use ranks two and four and different selected symmetry classes; they reject fixed
rank, first/last, size-extrema, reverse-order, column-major, signal-class, original
source-color, and fixed-output shortcuts.

The adapter supports 2–6 demonstrations and 1–4 independently requested queries.
Query prefixes are stable, while an input-only seed stream shuffles the four query
profiles before any one-query prefix is selected. The bank always contains 15×17,
19×22, 24×27, and substantive 30×30 scenes. The 30×30 scene has eight distributed
payloads and active cells on all four boundaries. Settings, exact programs, seeds,
query answers, source indices, future queries, and the total query count remain
private.

From the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/aa0b08801e61/tests/test_parametric_signal_rank.py \
  --import-mode=importlib -p no:cacheprovider
python3 review.py run python3 \
  generators/aa0b08801e61/workspace/parametric/audit_lessons.py \
  --seeds 64 --out ../checks/aa0b08801e61/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify aa0b08801e61 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/aa0b08801e61/qualification --summary
```

Python outputs are sampler claims. Native qualification re-executes every label
through protected Racket. Reviewer readiness grants neither owner acceptance nor
training admission.
