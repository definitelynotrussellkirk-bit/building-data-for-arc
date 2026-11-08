# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Reproducible laser distribution probe

`probe_laser_distribution.py` imports the selected generator, reads its actual
semantic witnesses and rival registries, and creates four demonstration pairs
plus one query pair per lesson. All reference outputs come from the public
`python -m arcpuzzles apply` command through the packet's `run_with_racket.py`;
each command has at most 64 input grids. No private runner or Python rule oracle
provides labels.

Run from the packet repository, choosing a **new** evidence directory:

```sh
python3 generators/aba5e4aeb835/workspace/probe_laser_distribution.py \
  --out ../checks/laser-distribution
```

The default sample uses seeds `104729,130363,155921,196613`, 25 consecutive
lesson starts per seed, and easy/medium/hard bands. Each band has 100 lessons;
the four-position schedule is exercised from every cyclic start. Sliding
lessons reuse draws: 29 sample indices per seed/band produce 348 total draw
uses and 1,500 lesson pair uses. Exact input SHA256 deduplication can further
reduce reference execution. These overlapping lessons are not independent
statistical trials. Reports distinguish unique inputs, generated draw uses,
and overlapping lesson uses rather than conflating their denominators.

`--seeds` accepts comma-separated integers. `--starts`, `--start-index`, and
`--stride` alter the deterministic lesson index range. `--generator PATH`
allows a saved generator baseline to be compared against the same canonical
Racket reference; the manifest separately identifies selected generator source
and the public reference execution's generator and rule hashes. `--generate-only`
retains unlabeled inputs and observations without claiming reference parity or
lesson identification. For a quick smoke run:

```sh
python3 generators/aba5e4aeb835/workspace/probe_laser_distribution.py \
  --seeds 104729 --starts 4 --out ../checks/laser-smoke
```

`report.json` records source hashes, canonical shortcut fit on all four usable
canonical pairs, per-band denominators, witness counts, cyclic start counts,
observed axes, and competitor refutation/survival/query-discrimination counts.
`draws.json` and `lessons.json` retain every audited draw and lesson row;
`failures.json` retains every detected failure. Public apply input/result files
and command receipts make every reference label replayable. Small smoke runs
explicitly report that they do not meet the 100-lessons-per-band evidence floor.
The finite census addresses declared competitors and does not establish
identifiability against every possible hypothesis.

Band names must be nonempty, distinct members of `easy,medium,hard`; invalid
band arguments are rejected before creating the evidence directory. Boolean
and violation-list checks are normalized consistently. The declared strict
fraction floor is enforced, and a strict violation is retained individually
when the floor is 1.0. Every fired `WITNESS_RIVALS` claim is checked against the
actual rival/reference output comparison on that grid; agreement or a rival
execution error is retained as a false witness claim. Raw witness counts and
verified witness counts remain distinct.

Focused probe regressions can be run with:

```sh
python3 generators/aba5e4aeb835/tests/test_probe_laser_distribution.py
```
