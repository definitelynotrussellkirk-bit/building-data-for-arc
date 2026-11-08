# Current review: retained audit and actual transpose collision

All baseline evidence binds generator SHA-256
`6940b446988027b5ca277abb707643959dfe35c593ee59ca87f957c006a4ccc9`
and canonical rule `9eb76f1bb8b7`. Canonical authoring data has labels and must
not be consulted during a visible-only solve.

- `retained-audit-reproduction.json` checks every retained asset SHA-256 and
  records independent seed 0/index 0 reproduction of the ignored two-color
  request and dimension/count default-bound rejections. Its Racket label equals
  the retained mirror; this original override audit is not a label mismatch.
- `finite-probe.json` records 256 defaults at seeds 0..255/index 0. Seed 31
  contains two destination collisions at (1,1),(1,2), silently accepted by the
  original self-check. Actual Racket reduces color 2 from three cells to one.
  Seed 26 has only a source/destination intersection at (5,4); blank-output
  Racket painting preserves all cells and paints that position color 8.
  This lawful witness guards against accidentally banning an unnecessary
  source/destination overlap or using sequential object erasure for labels.
- `racket-inputs.json` orders the original audit seed 0, lawful seed 26,
  collision seed 31. `racket-labels.json` is actual public `arcpuzzles apply`
  output for these three inputs with source and rule bindings.
- `regression-before.json` records failing test counts and commands before
  repair. Its later additions are separate commands, not a claimed single run.

Commands run from the packet root (payload cwd is `WORK/repo`):

```sh
python3 review.py run python3 generators/7071285d78ce/counterexamples/current_review/probe.py
python3 review.py run python3 -m arcpuzzles apply 7071285d78ce --input generators/7071285d78ce/counterexamples/current_review/racket-inputs.json --out generators/7071285d78ce/counterexamples/current_review/racket-labels.json
python3 review.py run python3 -m pytest generators/7071285d78ce/tests/test_transpose_regressions.py -q --tb=short
```

The probe now refuses to overwrite retained evidence. To probe changed sources,
choose a fresh `--out` and apply its new `racket-inputs.json` to a new label file.
Finite shape coverage is a distribution regression; missing a shape in this
population does not prove that the original generator can never produce it.

Post-repair `regression-after.json` and `regression-after.log` bind the selected
source and corrected tests. The initial parent-run 97/5 intermediate result
was a test-contract mismatch: alias conflicts expose structured
`ValueError.incompatible_axes`, not a required literal spelling in the human
message. Tests now verify the exact conflicting-axis set and nonempty message.
The full corrected run passes all 102 cases, including all four canonical
normalized shapes in the finite sample and actual Racket conservation checks.
