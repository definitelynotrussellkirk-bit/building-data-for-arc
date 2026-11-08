# Native dominant-gap family for `ac4b61e7b230`

This task-local family preserves the exact canonical default and adds one
input-derived translation rule. It leaves the selected production generator,
canonical ledger, and training status unchanged.

## Episode-fixed setting

`translation_mode` accepts:

- `all_separated_axes` — the exact canonical rule: compute the signed row and
  column shifts needed for the red bounding box to abut cyan, then apply both.
- `dominant_gap_axis` — compute the same signed shifts, compare their absolute
  magnitudes, and apply only the larger-gap axis; an exact magnitude tie selects
  the row shift.

Inputs are identical across settings. The adapter supports 2–6 demonstrations
and 1–4 prefix-stable queries. The first demonstration is column-dominant and
the second has equal negative row/column gaps. Together they distinguish both
settings and reject fixed-row, fixed-column, smaller-gap, and wrong-tie-break
rules. The fourth query is a dense 30×30 scene with more than 100 active cells;
red touches the top/left boundaries and cyan touches bottom/right.

## Sequential dependency

Step A measures the signed row and column abutment gaps. The intermediate is
the selected axis and signed displacement after comparing gap magnitudes. Step
B translates every red cell by that intermediate. Replacing the selected axis
on the same input changes the final protected-Racket output.

## Reusable checks

`audit_lessons.py` checks both settings, every supported demonstration count,
four-query prefix stability, the 30×30 stress scene, and four plausible rival
rules. The retained 64-seed run covers 640 episodes with zero findings. It is a
finite audit, not a universal uniqueness proof.

From the packet root:

```bash
python3 review.py run pytest -q generators/ac4b61e7b230/tests/test_parametric_native_contract.py
python3 review.py run python3 generators/ac4b61e7b230/workspace/parametric/audit_lessons.py --seeds 64 --out generators/ac4b61e7b230/workspace/parametric/evidence/current/lesson-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify ac4b61e7b230 --out ../checks/ac4b61e7b230/qualification --summary
```

The inherited task test now locates canonical data through portable reviewer
helpers. Its base-source assertion intentionally checks normalized equivalence
because the stored base copy is whitespace-minified; the native adapter's
default is separately asserted byte-exact against canonical authority.
Qualification and any witness remain owner-pending evidence, not acceptance or
training admission.
