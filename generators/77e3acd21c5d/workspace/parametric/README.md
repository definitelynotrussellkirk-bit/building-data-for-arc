# Native tie-policy family for `77e3acd21c5d`

This task-local family varies how an exact nearest-edge tie is resolved while
preserving the original object grammar and exact canonical default program.
It does not modify the selected production generator, canonical ledger, or
training status.

## Episode-fixed settings

`row_ties` and `column_ties` each accept `both`, `low`, or `high`.
`both/both` returns the canonical Racket bytes exactly. `low` keeps the
source's top/left edge interpretation; `high` keeps bottom/right. Ordinary
non-tied markers, clipping, widest-source selection, and Cartesian composition
remain unchanged.

The adapter supports 2–6 demonstrations and 1–4 queries independently. It
constructs a fixed six-demonstration/four-query pool and slices prefixes, so a
single-query request is byte-identical to the first query of a four-query
request. Inputs are independent of the private setting.

The first teaching scene is constructive rather than rejection-sampled: the
true source is uniquely widest but is neither the first nor the largest-area
multicolor object. Its central marker ties on both axes. Consequently the first
two demonstrations distinguish all nine settings and reject first-source,
largest-area, and diagonal-zip shortcuts. Query four is a dense lawful 30×30
scene with content distributed near every boundary.

## Sequential dependency

Step A derives row and column anchor sets from each source marker's distances
to opposite source edges and the episode's tie policies. The intermediate is
the selected row/column anchor sets. Step B paints their Cartesian product in
the output canvas. Replacing the intermediate for a tied marker changes the
final protected-Racket output on the same input.

## Reusable checks

`audit_lessons.py` checks all nine settings, every supported demonstration
count, four-query prefix stability, exact 30×30 coverage, and three structural
rivals over a requested seed range. The retained 64-seed run covers 2,880
episodes with zero findings. This is a finite audit, not a universal uniqueness
proof.

From the packet root:

```bash
python3 review.py run pytest -q generators/77e3acd21c5d/tests/test_parametric_native_contract.py
python3 review.py run python3 generators/77e3acd21c5d/workspace/parametric/audit_lessons.py --seeds 64 --out generators/77e3acd21c5d/workspace/parametric/evidence/current/lesson-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 77e3acd21c5d --out ../checks/77e3acd21c5d/qualification --summary
```

Qualification and any witness remain owner-pending evidence, not acceptance or
training admission.
