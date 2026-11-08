## 4de2bae05c7d

**Reproduced teaching defect — unresolved.** An ordinary ordered lesson with
five demonstrations and one final query leaves four-way versus eight-way yellow
component connectivity ambiguous. This finding concerns the generated teaching
distribution; the canonical Racket labels are correct. No target source was edited.

The audited generator is version `2.0.0`, SHA-256
`3db8214f8f85fe42ca4ca0ce783b263c8dc06817787c37897d2ffa9f8aee7178`.
Its declared `RULE_HASH` is `12b3f52c8e05`. The exact canonical row is task
`4de2bae05c7d`, line 2043 of `repo/shared/data/canonical/puzzles.jsonl`; its
`program_solution` SHA-256 is
`b96ba786e8e2f592f4e9125e31bdb87a32ff4161378bc8d8f5bdbddfd3fa975a`.
The current notes were only the imported placeholder and no
`evidence/review_index.json` was present.

### Exact ordinary-production counterexample

Replay `seed=64`, `sample_index=0`, `difficulty="easy"`, `n_train=5`, `n_test=1`,
with no overrides. The shared production `runner.run_one` accepted all six
indices `0,1,2,3,4,5`, with no rejection or duplicate skipping. Every input
passed the generator's `self_check`. Outputs were executed using the selected
canonical rule through the protected Racket bridge. The same live bridge also
matched all three stored canonical outputs.

The rival applies the same yellow-only exact three-cell L recoloring operation,
using **eight-neighbor same-color components**. It matches all three canonical
pairs and all five demonstrations of the saved generated lesson. It disagrees
with the final query on all six yellow cells. The generator's
`lesson_identifiable(demos, query)` nevertheless returns `[]`.

The final query input is the following 8 × 8 grid:

```json
[
  [0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0],
  [0,0,0,0,0,4,4,0],
  [0,0,0,4,4,0,4,0],
  [0,0,0,4,0,0,0,0],
  [0,0,0,0,0,0,0,0],
  [0,0,0,0,0,0,0,0]
]
```

The exact Racket output replaces the six `4` cells with `1`. The rival leaves
this entire grid unchanged: the two cardinal L components are diagonally joined
between `(3,5)` and `(4,4)` (zero-based), producing one eight-way component of
size six. The query input SHA-256, using compact JSON encoding, is
`7d9166d5f7f03378868512f0d9cf1d9db4f19f1223e32a3ef7c01e29a1fd866f`.

Cause: `_can_place` intentionally permits diagonal contacts while the five
profiles schedule shape, color and orientation contrasts only. The declared
lesson competitors omit a connectivity rival, so the hook cannot detect this
case. A task-local improvement would add a four-way/eight-way rival and ensure
the demonstrations contain a distinguishing diagonal-contact witness whenever
the query requires that distinction. That proposed change was not implemented
or tested in this findings-only audit.

### Reproduction and evidence

Actual outer command, from `/workspace/scratch/322233981b72/review`:

```bash
.venv-review/bin/python review.py run /workspace/scratch/322233981b72/review/.venv-review/bin/python ../checks/audit/4de2bae05c7d/probe.py --out ../checks/audit/4de2bae05c7d/run2 --seeds 100
```

The wrapper's actual payload cwd was
`/workspace/scratch/322233981b72/review/WORK/repo`. Exit **1** means the audit
successfully reproduced the finding. The probe screened seeds 0 through 64 and
stopped at the first candidate, then materialized that lesson with Racket. This
adaptive sample is not a prevalence estimate; rotations were not needed or run.

- `checks/audit/4de2bae05c7d/run2/connectivity_counterexample.json` retains all
  six exact input/output pairs, rival predictions, component coordinates,
  differences, observable axes, accepted sample indices and runtime identity.
- `checks/audit/4de2bae05c7d/run2/probe_result.json` retains the source hashes,
  search receipts, canonical checks and completed verdict.
- `checks/audit/4de2bae05c7d/probe.py` is the reusable reproduction.
- `checks/audit/4de2bae05c7d/result.json` retains exact commands, working
  directories, exit statuses, evidence paths and audit limits.
- `checks/audit/4de2bae05c7d/run1/probe_result.json` retains the first attempt's
  exit-2 traceback: the shared wrapper expected `scripts.comment_solutions`
  from a prepared runtime, which is absent from repository PYTHONPATH. The
  successful probe exposes the shipped `shared/tools` directory as that
  in-memory namespace and records parser/wrapper hashes. It changes no source
  or authority. `checks/audit/4de2bae05c7d/run1/probe.py` preserves the first
  probe's exact bytes.

### Additional bounded distribution observation

At seed 101, indices 0–19 in each of easy, medium and hard, the focused profile
probe measured 12/60 exact canonical profiles and 12/60 inclusive envelope hits
(4/20 in each band). This is 20%, below the packet's documented 25% envelope
floor. The source's one-anchor-per-five schedule explains the measurement.
These counts are retained in the run2 report. This was a focused measurement,
not a public `profile_floor` run; no full battery or audit task tests were run.
It is secondary to the Racket-confirmed ordinary-production teaching defect.
