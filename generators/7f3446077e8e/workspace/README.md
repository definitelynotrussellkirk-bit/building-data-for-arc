# Task-local review tools

## `shortcut_probe.py`

This source-bound probe independently reconstructs the marker-vector copy rule,
checks that the `diagonal_only` rival fits every labeled canonical pair, and then
enumerates all four single-query holdouts in consecutive four-pair generated
windows across easy, medium, and hard. It also retains an exact axial
counterexample with both outputs and differing cells.

Run from the packet root:

```sh
python3 run_with_racket.py python3 generators/7f3446077e8e/workspace/shortcut_probe.py \
  --seeds 12 --windows 12 --out ../checks/shortcut-probe.json
```

The probe uses an independent Python coordinate oracle. The official
`lesson-census` evidence is stronger for label provenance because it uses live
Racket. Neither finite check proves that no undeclared rival exists, and an
assembler that skips sample indices must re-check the schedule.
