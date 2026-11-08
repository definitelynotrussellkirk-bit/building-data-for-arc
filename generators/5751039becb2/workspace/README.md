# Review workspace for `5751039becb2`

`curriculum_probe.py` is a fast, source-bound preflight for this generator's
four-slot teaching schedule. It uses an independent Python implementation of the
diagonal-neighbour rule, dynamically reads every declared lesson competitor and
witness, enumerates all cyclic three-demo starts, and records source hashes and
counterexamples in JSON.

Run from the packet repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/5751039becb2/workspace/curriculum_probe.py \
  --per-band 100 --out ../checks/curriculum-probe.json
```

This probe is deliberately not a replacement for the shared Racket-backed
`lesson-census`, `rule_smoke`, or full battery. Its purpose is quick regression
feedback and complete cyclic-window coverage during future edits.
