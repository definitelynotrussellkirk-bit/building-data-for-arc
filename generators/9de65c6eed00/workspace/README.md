# Task-owned review tools for 9de65c6eed00

These tools use the live declarations from `generator.py`; they do not contain a
copied rival-name list or private runner imports.

## Exhaustive joint controls

From the extracted packet root (`WORK/`):

```bash
python3 run_with_racket.py python3 \
  generators/9de65c6eed00/workspace/probe_controls.py \
  --out ../checks/control-probe.json
```

This enumerates every combination of four difficulty values, 9 heights, 10
widths, 4 profiles, and 6 palettes: 8,640 cases. It independently compares the
returned pixels with `observe_overrides` and runs `self_check`.

## Cyclic lesson/query audit

```bash
python3 run_with_racket.py python3 \
  generators/9de65c6eed00/workspace/probe_semantics.py \
  --seed 0 --out ../checks/semantic-probe.json
```

This labels all four profile windows in all three bands with the real Racket
authority, then holds out each of the four pairs once. It tests every live
`LESSON_COMPETITORS` callable for mutation, determinism, demonstration fit, and
a differing query prediction. The final run covers 12 lessons and 48 rotations.
