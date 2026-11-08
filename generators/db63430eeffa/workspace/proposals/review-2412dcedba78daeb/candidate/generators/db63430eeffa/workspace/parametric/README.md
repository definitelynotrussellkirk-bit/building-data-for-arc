# Proposed `path_mode` extension for `db63430eeffa`

This is a **task-local research prototype**, not a production-generator or catalog change. It preserves the original two color-8 endpoints, the diagonal and major-axis straight segments, color 3 path, color 8 endpoints, and reading-order endpoint selection. One hidden setting is fixed for the entire episode:

- `both` — canonical default; paint the union of diagonal-first and straight-first paths.
- `diagonal_first` — paint only the diagonal-then-straight path.
- `straight_first` — paint only the straight-then-diagonal path.

Each retained episode contains three labeled demonstrations and four distinct queries. Inputs are sampled from a rule-independent stream and always have unequal row/column gaps so all three settings produce distinct outputs.

Run focused tests:

```bash
cd WORK
python3 ../review.py run python3 -m pytest generators/db63430eeffa/tests/test_parametric_path_mode.py -q
```

Build real-Racket evidence:

```bash
cd WORK
python3 ../review.py run python3 generators/db63430eeffa/workspace/parametric/prototype.py \
  --out ../checks/parametric/db63430eeffa-path-mode-v1 \
  --base-seed 20261023
```

The evidence writer executes all three Racket programs on all 21 retained inputs (63 logical rule applications), checks every result against an independent Python mirror, verifies both rivals are refuted by the three demonstrations for every episode, and audits public files for hidden-rule/query-label leakage. Public filenames are SHA-256 content IDs of exactly their visible demonstrations and query inputs.
