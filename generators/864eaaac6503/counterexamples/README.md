# Reproducible findings

`partial-foreground-first-repair.json` retains the first repair's actual searched
Racket-labelled construction-mutation witnesses, with their query positions and
source hash. The measured mutation is a bounded diagnostic, not an independent
solver. The repaired generator declares input-only partial-foreground rivals and
requires extended examples to distinguish them.

`duplicate-removal-first-repair.json` (copied from independent review evidence)
records the seed 21212, easy, start 0 failure: identical extended pairs at indices
1 and 3 yield accepted indices 0,1,2,4. The query at accepted position 1 is
ambiguous against `only_three_by_three`. A four-index dimension-parity schedule
prevents neighboring extended duplicates; focused tests replay this exact seed.

Original version 1.1.0 control failures are minimal calls, requiring no grid file:
`generate(17,0,difficulty='easy',grid_h=30,grid_w=2,palette_size=10)` did not honor
the advertised joint controls; `generate(True,0)` and unknown override keys were
accepted/coerced. Exact failing calls, expected exceptions, and corrected outputs
are covered by `tests/test_rotation_contract.py` and retained before/TDD logs.

The shared checker's `solid_2x2` impostor is exactly the first canonical input:
`[[0,0,9],[0,0,9],[9,9,9]]`. Other accepted singleton/line/block probes are lawful
rotation inputs. Evidence and optional calibration proposals live in the return's
`checks/gate-calibration/` and `checks/authority-calibration/`; shared code remains
unchanged.
