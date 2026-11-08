# `dbecc530afd0` inset-depth prototype

This directory is an isolated review prototype. It does **not** change the
production generator or canonical rule. The episode parameter is chosen once:

- `inset_depth=1` — the exact canonical Racket program, byte for byte.
- `inset_depth=2` — the same rectangle detector and composition logic, but only
  cells at least two steps inside every rectangle are painted red.

All retained episode labels and counterfactual labels are executed through the
bundled Racket bridge. Inputs are shared across settings, contain one or two
complete corner-disjoint rectangles of at least 5x5, and every input visibly
distinguishes the two settings.

Demonstration and query counts are independent. The bounded writer accepts 1–8
of each with at most 12 total pairs. Its retained command uses three shared
labeled demonstrations and **four distinct, simultaneously unlabeled public
queries** per episode. Each query is checked against the opposite-depth rival
using only those demonstrations.

Public files contain only visible demonstration inputs/outputs and query inputs.
They are named `challenge-<sha256>.json`, where the hash is computed from the
exact canonical public bytes. Seeds, settings, programs, private ordinals, and
query answers do not enter the filename or identifier. Duplicate public payloads
are rejected; batch output is sorted by public ID. Private files retain settings,
program hashes, Racket labels, and rival analysis.

From `WORK/`, build immutable evidence with:

```bash
python3 run_with_racket.py \
  python3 generators/dbecc530afd0/workspace/parametric/prototype.py \
  --seed 0 \
  --demo-count 3 \
  --query-count 4 \
  --out ../checks/parametric/inset-depth-v2
```

The command refuses to overwrite an existing directory. This is finite evidence
for two consecutive seeds and one declared rival, not production approval or a
claim of unique induction against every hypothesis.
