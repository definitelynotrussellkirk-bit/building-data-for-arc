# Native `min_reds` family

This task-local adapter exposes one episode-fixed eligibility threshold while
preserving the selected rule's candidate ranking, greedy red-conflict rejection,
and first-selected gray-cell precedence.

| Parameter | Values | Canonical/default |
| --- | --- | --- |
| `min_reds` | exact integers `1`, `2`, `3` | `1` |

A candidate is a 3×3 all-red/gray window with gray at its center and at least
`min_reds` red cells. Candidates are sorted by decreasing red count and then
reading order. A candidate is selected only when none of its red cells appeared
in an earlier selected candidate. Gray cells covered by selected candidates are
recolored from the first selected hit: center to yellow 4 and all other gray
cells to orange 7.

`rules/min-reds-1.rkt` is the exact selected canonical source. The other two
retained programs replace only the unique minimum-red predicate. Loading fails
if the canonical bytes or any reviewed retained source drift.

## Native contract

`adapter.py` exports:

- `program(settings)`: exact retained Racket source for one setting;
- `generate(seed, settings, demos, queries)`: deterministic `train`, `test`, and
  `program_solution` records.

The family supports 2–6 demonstrations and 1–4 queries. Input sampling is
independent of the hidden setting; demo and query streams are independent and
prefix-stable. Every scene contains isolated one-, two-, and three-red examples,
a count-priority overlap competition, selected windows that share gray cells,
and a gray-only distractor. Thus each demonstration separates all three
thresholds while retaining the ranking, greedy rejection, and first-hit stages.

The fourth query is a substantive 30×30 grid with 25 separated motif slots,
well over 180 nonzero cells, at least 20 eligible windows, rejected red-overlap
candidates, and selected gray overlaps. Python outputs are claims only: native
qualification re-executes every label with the protected bundled Racket runtime.
A `skip_greedy_output` ablation is retained for causal review and differs on
every generated scene for every setting.

From the outer extraction directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/fc814cec3976/tests/test_parametric_threshold.py

python3 review.py run python3 -m arcpuzzles parametric qualify fc814cec3976 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/fc814cec3976/qualification --summary
```

The older `materialize(...)` evidence writer and its retained artifacts remain
available for historical inspection. The native adapter is proposed/ready for
owner review; it does not self-approve, accept, or admit the family to training.
