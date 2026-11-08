# Reusable authoring tools for 95524d104174

Run from the outer extracted packet directory after `review.py setup` and
installing the packet's Python dependencies. The wrapper runs payloads from
`WORK/repo`, so output paths use `../checks/`. Use a fresh output path each run.

## Cross-contract and shortcut probe

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python generators/95524d104174/workspace/probe_cross_contract.py --seed 2026 --per-band 100 --out ../checks/cross-probe-replay.json
```

The probe loads the selected source through public reviewer helpers, verifies
all four canonical labels with Racket, and checks generated Racket outputs
against a separate pixel specification. It measures actual controls, canonical
shape/color-count support, margins, winning centers, and each declared rival.
It retains source/rule/script hashes, exact input/output hashes, the first
generated witnesses, and a complete 4-by-6 modal-center counterexample.

Repeated difficulty bands can share input grids. Read `total_generated` and
`unique_inputs` separately. A successful probe concerns individual grids; use
the production lesson census to assess demonstration/query assembly:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles lesson-census 95524d104174 --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-replay.json
WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles lesson-census 95524d104174 --enumerate-schedule-period --schedule-seed 0 --rotation-policy require --out ../checks/schedule-replay.json
```

The schedule receipt covers one fixed seed and all declared start residues.
The larger census uses its recorded seed recipe. Neither proves identifiability
against hypotheses outside the checked rival set. Rival declaration aliases
are not separate independent behaviors.

## Tests and proposed parameter

The portable check deliberately separates the selected generator path from
the task tests/workspace paths. Use `reviewer_support.find_root(__file__)` and
resolve workspace assets from that root's `generators/95524d104174/` directory.
Do not derive workspace paths from the selected executable's parent directory.

```bash
WORK/.venv/bin/python review.py check --stage task_tests --phase after --timeout 600 --out ../checks/task-tests-replay
```

See `parametric/README.md` for the executable episode-level frame-color
prototype, exact Racket variants, public challenge boundary, tests, and limits.
These authoring tools expose labels and belong outside a visible-only solve.
