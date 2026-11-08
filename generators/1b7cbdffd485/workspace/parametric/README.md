# Output-order parametric family

This native prototype preserves the exact canonical `first_seen` Racket program
and adds one bounded alternative, `reverse_first_seen`. For the same seed and
requested counts, both settings receive byte-identical inputs; only the private
setting and the executed labels differ.

Both settings preserve the source task's real two-step dependency:

1. **A — first-hit scan:** traverse row-major and record ordered
   `(color,row,column)` triples for each color's first occurrence.
2. **B — projection:** compare the row and column spans of those triples, choose
   row versus column output, and place the colors in the episode's forward or
   reversed first-hit order.

B cannot be selected before A: the intermediate supplies both the orientation
and the color sequence. `adapter.causal_witness()` retains a same-input witness
where replacing the qualified forward order with the reversed intermediate
changes the final Racket output.

The minimum two-example lesson is constructive. Demo 1 is an exact span tie,
so it teaches the canonical `>=` boundary and a column output. Demo 2 has a
horizontal-dominant first-hit spread and therefore a row output; its region
sizes also defeat frequency sorting. Nonmonotone palettes reject numeric order.
Together the two examples distinguish both settings from the declared numeric,
frequency, column-major, fixed-orientation, and strict-tie rivals. Additional
demonstrations broaden morphology without changing the rule.

A discarded scan-order prototype could not meet the same two-demo teaching
standard: because the top-left color anchors both scans, row-major vertical
dominance and column-major horizontal dominance cannot occur on a fully colored
canvas. One setting therefore remained observationally confounded with a fixed
orientation. The output-order parameter avoids dropping that meaningful rival.

Every episode supports 2–6 demonstrations and exactly four distinct novel
queries. Two queries are substantive 30×30 partitions. `public_turn()` exposes
all demonstration labels and exactly one query input while omitting settings,
programs, future inputs, and all query answers.

From the packet root:

```bash
python3 review.py task-tests 1b7cbdffd485 --phase after \
  --out ../checks/1b7cbdffd485-task-tests
python3 review.py run python3 -m arcpuzzles parametric qualify 1b7cbdffd485 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/1b7cbdffd485/qualification --summary
```

Qualification and the finite shortcut certificate cover only the declared
settings, generated grammar, and exercised seeds. They do not prove universal
uniqueness, owner acceptance, or training admission.
