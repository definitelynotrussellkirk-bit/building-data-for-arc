# Task-local qualification workspace

`qualify.py` is a source-bound regression probe for generator `3ef5f8be2639`.
It complements the shared battery by checking:

- every one of the 24 selected-pair offsets across all four 1/2-seed count combinations and canonical 7×7/8×8 shapes;
- deterministic default draws, canonical-profile support, distance-1/distance-2 support, and effective scan-order distractors;
- both declared canonical-fitting rivals against the public canonical pairs; and
- every cyclic query rotation of contiguous four-item lesson windows.

Run from the packet root:

```bash
python3 run_with_racket.py python3 generators/3ef5f8be2639/workspace/qualify.py \
  --per-band 100 --out ../checks/qualification-final.json
```

This is finite Python-side evidence. The shared `rule_smoke` and
`authority_sync` stages remain the binding Racket checks.
