# Midpoint selection — native parametric family

This family preserves the exact canonical midpoint rule as
`selection=all_pairs`. The alternative `selection=cue_gap` adds a genuine
input-dependent sequence:

1. **A:** find the unique row whose two 8 endpoints have a color-1 cell at their
   integer midpoint and read that endpoint gap;
2. **intermediate:** the cue row's even endpoint gap;
3. **B:** paint red only empty integer midpoints whose endpoint gap equals that
   intermediate.

The cue row itself is unchanged because its midpoint is occupied. Every normal
input also contains matching and nonmatching candidate gaps, an odd-distance
pair, and an occupied-midpoint witness. Inputs are matched across settings and
independent of requested query count.

## Teaching construction

A second adversarial pass found that the original two demonstrations admitted
several unintended shortcuts on some seeds: modal-gap selection, fixed two-result
caps, smallest/largest-gap selection, and cue-relative position rules. The
current constructor makes those correlations disagree with the intended rule:

- cue gaps are internal values rather than the smallest or largest available gap;
- the number of cue-matching candidates cycles through 2, 3, and 4;
- a non-cue decoy appears one more time than the cue gap, while a second non-cue
  gap appears exactly once;
- top, bottom, nearest-above, nearest-below, nearest, and farthest candidate rows
  are guarded against carrying the cue gap.

The source-local rival catalog now contains 25 rules covering identity,
`all_pairs`, `cue_gap`, six fixed gaps, output-count caps, minimum/maximum and
frequency rules, and positional rules. Across 5,000 seeds and both settings,
the minimum two-demo lessons produced 10,000 cases and 500,000 named-rival
evaluations with no unexpected survivor. This is a finite named-rival audit,
not a proof of universal identifiability.

The adapter supports 2–6 demonstrations and 1–4 queries independently. Four-query
requests end with a substantive 30×30 scene spanning both row and column
boundaries. The fourth query is not empty padding: it has 24 candidate rows plus
cue and near-miss witnesses.

From the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/02fcd49e49d6/tests
python3 review.py run python3 \
  generators/02fcd49e49d6/workspace/parametric/probe.py
python3 review.py run python3 -m arcpuzzles.review_base_preflight \
  02fcd49e49d6 --out ../checks/02fcd49e49d6/qualification
```

Current evidence: 22 focused tests plus 11 subtests; 20 coverage cases over
seeds 0/17, demo counts 2–6, four queries, and both settings; four
protected-Racket jobs with 32 label evaluations; source-bound authoring
preflight; and a protected counterfactual witness. `canonical.rkt` is
byte-for-byte the selected authority. `cue_gap.rkt` is the alternative complete
rule. No owner acceptance or training admission is claimed.
