## 8f6a6ec3ae21 — generated query rotations admit one-sided color-filter rivals

**Finding: a concrete lesson teaching gap within ordinary generated support.**
The two named-role rules below each fit every canonical demonstration (2/2)
and the canonical test (1/1):

- `filter_left_only`: select rows from color 1 on the left border, but select
  columns from **every nonzero** top-border marker.
- `filter_top_only`: select columns from color 2 on the top border, but select
  rows from **every nonzero** left-border marker.

Both clear the input and paint the resulting Cartesian product with color 8.
These are simpler one-sided variants of the intended color-and-border rule.

Audited version `3.0.0`, generator SHA-256
`a30551fabf7d39bc1056441e22e0a9153c2457be1f5d488d9307f5eee57e6475`,
canonical rule `ca6d5269f15c`. The assigned source matches
`WORK/AUDIT_ASSIGNMENT.json`; no generator, rule, test, note, contract, or
approval file was changed.

### Exact generated lesson and actual Racket witness

Generate seed **10401**, sample indices **0, 1, 2**, difficulty **medium**, with
**no overrides**. Use samples **0 and 2 as demonstrations** and sample **1 as
the query**. All three inputs are actual default generator outputs, and all
pass `self_check` and `strict_canonical_like`. This is not a hand-built
validator-only or out-of-domain counterexample.

The two demonstrations contain a wrong-role color-2 mark on the left border
and no wrong-role color-1 mark on the top border. Consequently
`filter_left_only` produces both demonstration outputs exactly. The query has
a wrong-role color-1 mark at top-border column 1; the rival wrongly treats this
as a selected column.

Exact query input (`checks/audit/8f6a6ec3ae21/input.json`):

```json
[
  [0,1,0,2,2,0,0,0,0,2],
  [0,0,0,0,0,0,0,0,0,0],
  [1,0,0,0,0,0,0,0,0,0],
  [1,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0],
  [1,0,0,0,0,0,0,0,0,0]
]
```

Actual canonical Racket output:

```json
[
  [0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0],
  [0,0,0,8,8,0,0,0,0,8],
  [0,0,0,8,8,0,0,0,0,8],
  [0,0,0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0,0,0],
  [0,0,0,8,8,0,0,0,0,8]
]
```

The rival additionally paints 8 at zero-based coordinates **(2,1), (3,1),
(6,1)**. `checks/audit/8f6a6ec3ae21/witness.json` retains all three exact inputs,
their seed/index/band/override settings, the outputs of both rivals, and the
rotated lesson configuration. `checks/audit/8f6a6ec3ae21/racket.json` contains
fresh public-reference outputs for all three inputs. The comparisons confirm
that this rival fits both actual-Racket demonstration labels and changes the
actual-Racket query label.

### Bounded count and source-level explanation

The independent Python probe inspected **36 lessons**, formed from seeds
10401–10403, starting sample indices 0–3, and easy/medium/hard, with three
consecutive generated inputs per lesson. All **108 input slots** passed the
validator. Of **108 held-out query rotations**, **36 were ambiguous** under one
of these two rivals. The current `lesson_identifiable` reported no issue for
all 36 because its declared competitor list does not include them. The ordinary
production view, where the first two consecutive inputs are demonstrations and
the third is the query, had **0/36 ambiguities** against these rivals.

The schedule explains the result beyond the finite sample: exactly one decoy
appears per default input, and its side alternates with sample-index parity.
Every consecutive three-input lesson therefore has side pattern **A, B, A**.
Holding out its middle input removes the only demonstration of filtering on B.
Alternating decoy sides prevents the one-sided shortcut in the production
two-demo order, but it does not make every held-out query rotation identifiable.

This does **not** show incorrect reference labels or invalidate the earlier
reported pass against four declared competitors. It identifies a plausible,
canonical-fitting competitor omitted from that bounded grammar. The existing
notes already limit their claim to named rivals; the more general comments
about preventing one-sided shortcuts and robust query rotation need this
qualification.

### Narrow recommendation; not implemented in this audit

Add both one-sided rivals to the lesson competitors and regression checks.
If every two-demo holdout must teach both border roles, ensure each role has
decoy evidence in at least two of each three consecutive inputs. One constructive
default schedule is a repeated three-phase cycle **both borders, left only,
top only**, with explicit override behavior preserved. Then every held-out pair
of demonstrations still contains evidence for both roles. Existing allowed
overrides already support one decoy on each border simultaneously.

A focused regression can first use the exact lesson above and assert that the
expanded rival set flags query index 1. After a repair, check all three holdouts
over the complete declared schedule period. No audit-target repair is included.

### Execution and evidence scope

All final commands exited **0**, invoked from
`/workspace/scratch/de8a534dedae/arc_review` and executed in
`/workspace/scratch/de8a534dedae/arc_review/WORK/repo`. Exact commands and source,
rule-text, input, and output hashes are retained in
`checks/audit/8f6a6ec3ae21/confirmation.json` and the public `racket.json` receipt.

```bash
PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/de8a534dedae/arc_review/WORK/.venv/bin/python review.py run /workspace/scratch/de8a534dedae/arc_review/WORK/.venv/bin/python ../checks/audit/8f6a6ec3ae21/probe.py
PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/de8a534dedae/arc_review/WORK/.venv/bin/python review.py run /workspace/scratch/de8a534dedae/arc_review/WORK/.venv/bin/python -m arcpuzzles apply 8f6a6ec3ae21 --input ../checks/audit/8f6a6ec3ae21/lesson-inputs.json --out ../checks/audit/8f6a6ec3ae21/racket.json
PYTHONDONTWRITEBYTECODE=1 /workspace/scratch/de8a534dedae/arc_review/WORK/.venv/bin/python review.py run /workspace/scratch/de8a534dedae/arc_review/WORK/.venv/bin/python ../checks/audit/8f6a6ec3ae21/confirm.py
```

The **36-lesson census uses Python**, while **three exact witness inputs have
fresh canonical Racket outputs**. Existing task tests and the combined public
audit preset were not rerun. The retained `authority.json` contains the exact
canonical source and all three normalized labeled pairs. `manifest.json` hashes
every authored file in this audit folder.
