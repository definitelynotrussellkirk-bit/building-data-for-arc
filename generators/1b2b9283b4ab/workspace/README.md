# Room-graph reviewer tools

Run these commands from the packet's `WORK/` directory. The supplied wrapper selects the offline Racket runtime and executes payloads from `WORK/repo/`. Use a new output directory for each run.

## Structural and semantic probe

```bash
python3 run_with_racket.py python3 generators/1b2b9283b4ab/workspace/probe_room_graph.py --out ../checks/room-graph/replay
```

The probe loads the selected generator with public reviewer support and verifies the pinned canonical program SHA. It derives rooms and doorway edges from cells, discovers eight distinct witness orientations, executes actual Racket labels, compares the diagnostic model and declared rivals, verifies every declared canonical shortcut against all usable labelled canonical pairs, checks 44 bounded joint-control cases, and writes an exact 4×10 same-color counterexample. Python predictions are labelled as comparisons; Racket remains the label authority.

The checked orientation-discovery range defaults to seeds 0..127 and can be changed with `--seed-start` and `--seed-limit`. This is bounded evidence, not a certification of all seeds or rival rules. It does not open or score private solve queries.

## Focused tests

The three files under the task's `tests/` contain 34 unittest methods: room-graph and override regressions, strict call-argument regressions, and the proposed parametric prototype checks. They can run without pytest through the same public wrapper:

```bash
python3 run_with_racket.py python3 -m unittest discover -s generators/1b2b9283b4ab/tests -p 'test_*.py' -v
```

For the official portable task-test gate, pass an interpreter containing pytest, NumPy and Pillow:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 1b2b9283b4ab --stage task_tests --phase after --timeout 600 --out ../checks/task-tests-replay
```

If the wrapper-selected `python3` lacks those dependencies, replace the payload `python3` with the absolute path to the complete test interpreter. The controller records that interpreter and its actual staged runtime; a missing dependency or all-skipped result is not a pass.

## Proposed rule variant

`parametric/README.md` documents the independent tie_marker prototype, whose two allowed settings are 8 and 6. It chooses the setting once per episode and executes matching Racket. It is separate from canonical production generation and approval.

```bash
python3 run_with_racket.py python3 generators/1b2b9283b4ab/workspace/parametric/prototype.py --seeds 0 1 --out ../checks/parametric/replay
```

The default program is byte-identical to the canonical authority. The alternative changes only the tie fill marker and uses a seed palette that excludes that marker. Public challenge JSON omits rule settings and query answers; authoring receipts retain both programs and their labelled examples.
