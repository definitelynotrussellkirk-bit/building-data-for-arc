# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Reusable review tools

`probe_curriculum.py` counts five input features seen in this task's canonical
examples. It records source/probe/canonical hashes, exact seeds and indices,
per-band counts, and validator failures. It does not create output labels.
From WORK/repo, use a new output path:

```bash
python3 generators/d07c7972d183/workspace/probe_curriculum.py --per-band 400 --require-canonical-features --out ../checks/feature-support/recheck.json
```

Omit `--require-canonical-features` for observation-only mode. Add
`--generator PATH` to compare another source against the same canonical ledger
and shared runtime. A finite zero count may miss a rare feature; the gate is
task-specific and is not a universal ARC feature policy.

`check_witness.py` verifies that the current declared lesson rivals disagree
with a retained public Racket answer. It rejects a receipt with a different
generator or rule hash. From the outer packet root:

```bash
python3 review.py run python3 -m arcpuzzles apply d07c7972d183 --input generators/d07c7972d183/counterexamples/review-914736475a6098c8/input.json --out ../checks/witness-recheck-racket.json
python3 review.py run python3 generators/d07c7972d183/workspace/check_witness.py --receipt ../checks/witness-recheck-racket.json --out ../checks/witness-recheck-comparison.json
```

These tools are authoring/review aids. They expose canonical examples or
reference outputs and must remain closed during a visible-only solve.
