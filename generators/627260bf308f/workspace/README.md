# Reusable palette-rank coverage probe

`coverage_probe.py` is an **authoring/review** tool. It reads canonical answers;
do not use it during a visible-only solve. It discovers current declared rivals
dynamically rather than maintaining a second hard-coded list.

From the extracted packet root:

```sh
python3 run_with_racket.py python3 generators/627260bf308f/workspace/coverage_probe.py --seeds 32 --joint-axes --out ../checks/coverage-new.json
python3 run_with_racket.py python3 generators/627260bf308f/workspace/coverage_probe.py --seeds 32 --baseline --out ../checks/coverage-baseline-new.json
```

Outputs must be new paths. The baseline option needs the assignment-created
`.review/baseline/repo/generators/627260bf308f/generator.py` in the original packet.
It hashes the input generator and the current rival definitions separately.

Each run examines seeds 0 through `seeds-1`, indices 0..10, all three bands,
and overlapping four-pair windows starting at 0..7. It tests the normal last
query and all four possible single-query positions, records unique input hashes,
and retains exact first counterexamples. `--joint-axes` adds all 12,240 legal
joint axis/band/parity cases at seed 867. A failure exits nonzero; it is not
silently treated as an incomplete success.

The expected-label calculation is an independent Python diagnostic, not Racket
label authority. Use `arcpuzzles lesson-census ... --rotate-query` for the real
production sampler with Racket labels. The retained baseline decisive case was
separately checked with the supported `arcpuzzles apply` interface.

Current evidence: 768 overlapping windows and 3,072 holdouts have no declared-rival
ambiguity, and 12,240 joint-axis cases validate. These are bounded observations,
not an assertion that all possible input distributions or rival programs are
covered. Reusing the same seeds across difficulty bands can produce duplicate
inputs; the probe reports 443 unique inputs for 1,056 examined final-source grids.
The production census used distinct replay seeds and reported 1,200/1,200 unique.
