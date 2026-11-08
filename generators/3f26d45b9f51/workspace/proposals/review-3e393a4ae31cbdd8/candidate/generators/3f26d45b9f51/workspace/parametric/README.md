# Proposed `axis_mode` episode parameter

This task-local prototype keeps the approved production generator and canonical
Racket rule untouched. It selects exactly one rule setting for an entire ARC
episode:

- `both_axes` — exact canonical program text and behavior.
- `horizontal_only` — connect same-color markers only across shared coarse rows.
- `vertical_only` — connect same-color markers only down shared coarse columns.

Every label is executed by the matching Racket program. Each episode contains
three demonstrations and four distinct queries by default. The production
input generator always provides an L-shaped marker color, so every generated
example distinguishes all three declared settings; demonstrations alone must
leave exactly the selected setting consistent.

From the packet root, materialize review evidence with:

```bash
python3 review.py run python3 \
  generators/3f26d45b9f51/workspace/parametric/prototype.py \
  --seed 31 --all-settings --demo-count 3 --query-count 4 \
  --out ../checks/parametric/axis-mode-final
```

The output is create-only. Public challenge filenames are SHA-256 IDs of the
exact visible challenge bytes. Hidden settings, programs, query outputs, and
provenance remain under `private/`.

## Scope limits

This is an unapproved research proposal. Rival completeness is claimed only
for the three declared `axis_mode` settings, and no production admission or
canonical-rule change is implied.
