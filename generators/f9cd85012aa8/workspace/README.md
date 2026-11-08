# Reusable authoring probes

Run these from the packet's `WORK/` directory. `run_with_racket.py` sets up
the public API and runs its payload from `WORK/repo/`. Use an environment
with NumPy, Pillow, and pytest installed for the test command.

```sh
python3 run_with_racket.py python3 -m pytest -q generators/f9cd85012aa8/tests
python3 run_with_racket.py python3 generators/f9cd85012aa8/workspace/probe_joint_axes.py --out ../checks/my-joint-probe.json
python3 run_with_racket.py python3 generators/f9cd85012aa8/workspace/probe_counterexamples.py --out ../checks/my-witness-pack
python3 run_with_racket.py python3 -m arcpuzzles lesson-census f9cd85012aa8 --enumerate-schedule-period --schedule-seed 0 --rotation-policy require --out ../checks/my-schedule.json
```

`probe_joint_axes.py` checks the Cartesian corners of both grid dimensions,
every advertised target count and distractor count, two seeds, and all three
bands: 960 parameter cases, with a second draw per case to check determinism.
It independently counts components and pixels, compares the generator's
observer, checkpoints progress, and retains exact failing grids. CLI options
can narrow or extend the seed/band/control lists. It evaluates input controls;
it does not label grids or claim lesson identifiability.

`probe_counterexamples.py` creates a small witness pack containing all labeled
canonical inputs, a hand-built 5×6 largest-object counterexample, and one
eight-index generated cycle. It labels them through the public Racket apply
command with domain checking explicitly enabled. It reads the current
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, checks canonical fits, and
records actual outputs, refutations, commands, dimensions and source hashes.
It refuses to overwrite an existing output directory. Use `--seed` and
`--band` for another bounded replay; use the shared census for larger coverage.

`semantic_candidates.py` and `semantic_review.json` retain the original
16-candidate exploratory review against the baseline. Its fixed candidate
set is historical authoring evidence, not the final 21-rival contract. Prefer
the declaration-driven witness pack for current-source checks.

These tools expose canonical or reference outputs and belong exclusively to
the authoring lane. They must not be used during a visible-only solve.
