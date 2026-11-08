# 9c26c4b2c305 review workspace

The selected implementation is `../generator.py`. Workspace tools are retained
for reproducibility and are never automatically selected as production code.

## `lesson_probe.py`

This source-bound census loads the selected generator, dynamically iterates its
actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, verifies canonical-fit
claims against all usable canonical pairs, and audits complete four-example
lessons across easy, medium, and hard. It records cyclic starts, palette and
width counts, exact-byte uniqueness, same-color coverage, rival disagreements,
source hashes, and limitations.

From the packet root:

```bash
python3 repo/generators/9c26c4b2c305/workspace/lesson_probe.py \
  --lessons-per-band 100 \
  --seed-base 90000 \
  --out checks/lesson-probe/final.json
```

The tool uses an independent occupancy-OR implementation for expected outputs.
Its census is finite and only covers competitors declared by the final source;
it is not a universal induction proof.

## `width_control_probe.py`

This bounded probe records 10 invalid width requests and 18 lawful recipes:
all four schedule slots plus exact width endpoints in each difficulty band.
It binds the selected generator and canonical rule hashes. `--racket` executes
every lawful label through the real Racket runtime, and `--baseline` checks that
the same lawful requests retain identical input bytes.

From the outer directory containing `review.py`, with `WORK/.venv` active:

```bash
python review.py run python generators/9c26c4b2c305/workspace/width_control_probe.py \
  --out ../checks/width-control/final.json --racket
```

The output path must be new. A pre-repair report can be supplied with
`--baseline ../checks/width-control/before.json`. The command returns 1 when an
invalid request is accepted, Racket labels disagree, or lawful inputs drift.
