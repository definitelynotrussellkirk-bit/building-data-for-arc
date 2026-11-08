# Proposed legend-selected population sort

This is a **task-local prototype**, not part of the selected canonical generator,
its approval path, or training admission. The default `all_slots` setting uses
the canonical Racket program byte-for-byte: every bit column is stable-sorted by
ascending foreground population while carriers and separators stay fixed.

The proposed `contains_key` setting gives the first bit column a legend role.
Its foreground **body rows** (the universal top marker is ignored) name required
features. The key remains fixed; later bit columns containing every required row
participate in the same stable ascending population sort, while nonmatching
columns remain fixed.

| parameter | allowed values | canonical/default |
|---|---|---|
| `selection_mode` | `all_slots`, `contains_key` | `all_slots` |

The setting is chosen once per episode. Each private episode has three
labeled demonstrations and four distinct labeled queries. Every retained input
has one key, three matching candidates, and two nonmatching candidates; the
matching candidates are deliberately out of population order, so every
example distinguishes the two declared settings. Public challenge files omit
the setting, exact program, private metadata, and all query outputs; they are
written as canonical visible bytes under opaque content-derived IDs rather
than setting- or seed-bearing names.

## Public-evaluation inspiration

Parent `d59b0160` has a 3x3 legend inside a color-3 L border. Its non-background
legend colors form a required set; every external four-connected non-7 region
containing that full set is erased to background 7. `public_focus.py` exactly
matches all three supplied demonstrations and produces the retained query
prediction.

The extension transfers the **legend → containment test → selected larger
objects** dependency, not the erasure action or the parent geometry. Colors in
the parent become foreground body-row features; connected regions become bit
columns; selected columns retain the assigned family’s population-sort action.
The canonical family and the proposed extension remain separate.

## Focused tests

From the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/89ab40aedfe4/tests/test_parametric_legend_selector.py
```

## Exact Racket verification and masked export

After `python3 review.py setup`, from the packet root:

```bash
python3 review.py run python3 \
  generators/89ab40aedfe4/workspace/parametric/verify.py \
  --seed 20261023 \
  --out ../checks/parametric-legend-selector/report.json \
  --artifact-dir ../checks/parametric-legend-selector/materialized
```

The verifier executes both exact Racket programs on every demonstration and
query for both forced episode settings, checks each output against an
independent Python mirror, validates every generated input with the selected
production checker, confirms that all seven inputs per setting are unique and
distinguish the settings, and records source/program/runtime hashes. Reusing an
artifact directory is allowed only when its recognized prior manifest names
known generated artifacts and matches every byte; unknown or modified files
abort without deletion. Focused regressions also execute the proposed Racket
rule on an empty key and on a key with fewer than
two matching candidates; both cases raise instead of vacuously selecting all
candidates. The verifier also checks the public parent demonstrations and
retains its visible-only test prediction.

## Limits

This bounded evidence covers two settings at one retained seed. The prototype
domain guarantees a nonempty key, three matching candidates, and two
nonmatching candidates. Structural parsing and the two dangerous degenerate
key cases are rejected, but the prototype does not claim useful semantics for
arbitrary malformed legends, prove uniqueness against every possible rule, change canonical
approval, or establish the private correctness of the public parent’s held-out
query.
