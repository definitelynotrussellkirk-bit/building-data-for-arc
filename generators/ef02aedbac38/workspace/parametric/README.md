# Proposed selector-role extension for `ef02aedbac38`

This task-local prototype varies one bounded episode-level rule parameter while
keeping the original two-color reasoning structure intact.

| Parameter | Allowed values | Original/default | Executed transformation |
|---|---|---|---|
| `selector_role` | `five`, `companion` | `five` | Select that input color role, paint its cells with the opposite role color, and write 0 elsewhere. |

`five` is byte-for-byte the canonical Racket authority: locate color 5, copy its
mask, recolor it with the sole companion color, and zero every other cell.
`companion` is the proposed nearby behavior: locate the companion-color mask,
recolor it 5, and zero every other cell. Grid shape, input grammar, color-role
identification, opposite-color painting, and background handling remain fixed.
The production generator and `RULE_HASH=0e568f927b22` are not changed by this
prototype.

The parameter is chosen exactly once with
`("five", "companion")[episode_seed % 2]` and reused for every pair in the
episode. Demonstration and query counts are separate command-line settings;
the retained default is three demonstrations and four distinct queries. Input
generation is independent of the setting. Because every lawful input contains
both roles, every demonstration and query distinguishes the two declared
settings.

Public files contain labeled demonstrations and unlabeled query inputs only.
Their opaque filename is the SHA-256 of the exact canonical bytes written, so
changing a visible demonstration output or any visible input changes the ID.
Hidden settings, rule text, seeds, metadata, and query answers remain private
and cannot affect either the public bytes or the public ID.

From the outer extracted packet directory, build fresh Racket-verified evidence:

```bash
python3 review.py run python3 \
  generators/ef02aedbac38/workspace/parametric/prototype.py \
  --out ../checks/parametric/selector-role-v1_1 \
  --seeds 0 1 --demo-count 3 --query-count 4
```

Run focused prototype tests through the task-local portable test stage:

```bash
python3 review.py run python3 -m arcpuzzles check ef02aedbac38 \
  --stage task_tests --timeout 600 --phase after \
  --out ../checks/task-tests
```

The evidence builder writes exact programs, two complete private episodes, two
content-addressed public challenges, direct Racket predictions for both
settings, all canonical-default checks, four distinct queries per episode, a
setting-difference witness, source/runtime hashes, and a file manifest. A
Python mirror is used only as an independent parity check; every retained label
is produced by the bundled Racket runtime.

This is a **proposed prototype**, not a production parametric API, catalog
approval, or training-admission claim. Evidence is bounded to the declared
settings and retained seeds, and does not exclude arbitrary competing programs.
