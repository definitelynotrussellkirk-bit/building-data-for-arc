# Authoring workspace

The selected implementation is `../generator.py`. Workspace tools are never
automatically selected as generators. Do not use this probe during a blind solve:
it reads the canonical program and retained reference labels.

## Exhaustive vote-support probe

`probe_vote_support.py` checks all 729 ordered triples from
`(0,1,2,3,4,6,7,8,9)`. It packs 42 triples into each `h=7, pw=6` input, producing
18 grids with full-height gray separators and 27 zero-padding cells. The
independent Python expectation counts nonzero colors and breaks frequency ties
by the larger numeric color. It never calls the generator's `apply_rule`.

Run these commands from the repository root with the authoring runtime on
`PYTHONPATH` (the review packet's `run_with_racket.py` sets it):

```bash
python generators/2ca05c7eef24/workspace/probe_vote_support.py prepare --out ../checks/vote-tool/votes.json
python -m arcpuzzles apply 2ca05c7eef24 --input ../checks/vote-tool/votes.json --out ../checks/vote-tool/racket.json
python generators/2ca05c7eef24/workspace/probe_vote_support.py score --prepared ../checks/vote-tool/votes.json --racket ../checks/vote-tool/racket.json --out ../checks/vote-tool/score.json
```

Preparation writes exactly `{"inputs":[...]}` and a separate
`votes.meta.json` sidecar. The sidecar records every triple's grid/cell mapping,
request and input digests, adjacent generator and tool source digests, and the
selected canonical raw program and hashes. Score reconstructs the full expected
preparation, recomputes the loaded sidecar's metadata digest, and compares its
normalized JSON serialization with reconstructed metadata. Numeric types remain
distinct: `false`, `0`, and `0.0` cannot substitute for one another, even when a
modified sidecar's digest is recomputed. Score rejects tampered or stale files, missing/extra/misordered results,
wrong returned inputs or digests, reference errors, wrong dimensions, rule/hash
binding failures, and any of the 729 vote labels or padding cells disagreeing
with the independent expectation. It exits nonzero and writes no new score
report on failure. Reprepare and rerun public apply after any generator or tool
source edit.

Public apply receipts are unsigned JSON. Score verifies their internal
consistency and binding; it cannot establish that an identical forged JSON file
was produced by Racket. Retain the recorded public apply invocation and its
receipt/log as provenance. Synthetic fixtures in focused tests exercise rejection
paths only and are labeled parsing tests, never reference evidence. Apply does
not grant generator approval.

In a review packet, record each command from the packet root. For example:

```bash
python3 WORK/checks/run_recorded.py --name vote-tool-prepare-final --evidence checks/vote-tool/votes.json --evidence checks/vote-tool/votes.meta.json -- WORK/.venv-review/bin/python WORK/run_with_racket.py /absolute/path/to/WORK/.venv-review/bin/python generators/2ca05c7eef24/workspace/probe_vote_support.py prepare --out ../checks/vote-tool/votes.json
```

Use the same wrapper and absolute payload interpreter for apply and score, with
unique recorder names. Payload paths resolve from the repository, while recorder
evidence paths resolve from `WORK`.

## Cheap generator coverage

```bash
python generators/2ca05c7eef24/workspace/probe_vote_support.py coverage --out ../checks/vote-tool/coverage.json
```

The default measures four seeds `0,1,2,3`, twelve sample indices, and the
`easy,medium,hard` bands: 144 generated inputs. Options are `--seeds 0,1,2,3`,
`--indices 12`, and `--bands easy,medium,hard`; `default` selects `difficulty=None`.

Coverage uses only the adjacent generator's `generate` and `self_check` plus the
tool's independent expectation. It counts `empty`, `singleton`, `pair_same`,
`pair_distinct`, `triple_same`, `triple_majority`, and `triple_distinct` local vote
classes and per-cell/per-input competitor disagreements. When present,
`LESSON_COMPETITORS` supplies named `callable(grid)->grid` competitors dynamically.
For older generators without that declaration, explicit operator adapters in the
tool are labeled as a fallback. Coverage is a Python-proxy measurement, not an
actual Racket audit or a universal lesson-identifiability claim.

Direct APIs are `prepare(out)`, `score(prepared, racket, out)`, and
`coverage(seeds=..., indices=..., bands=...)`. Focused tests live in
`../tests/test_vote_support_probe.py`.
