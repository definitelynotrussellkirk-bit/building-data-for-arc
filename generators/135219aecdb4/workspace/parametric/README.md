# Proposed episode-level pass budget

This workspace adds one bounded curriculum parameter without changing the
selected generator or canonical Racket authority:

- `pass_count` is one of the exact integers `1`, `2`, or `3`.
- The default is `3`, whose program text is byte-for-byte the canonical rule.
- One value is selected once for the whole episode, never per example.
- Demonstration and query counts are independent authoring controls; retained
  evidence uses 2 demonstrations and 4 queries.
- Every sampled input is a lawful 4x4 partial Latin square that needs exactly
  three synchronous passes to finish. Therefore all three settings produce
  distinct states and the demonstrations identify the hidden setting.
- Sampling is bounded by actual generator draws, not only by accepted candidates.
  Evidence runs must include the canonical default and at least one alternative.

`prototype.py` builds deterministic fixed-setting episodes. `build_evidence.py`
executes every retained label through the packet-protected Racket runtime,
checks an independent Python mirror, evaluates every alternative setting on
every example, and writes separate public and private artifacts. Public file
names are SHA-256 identifiers over exactly the visible challenge bytes; query
answers, seeds, settings, and source metadata are excluded.

From the packet root:

```bash
python3 review.py run \
  python3 generators/135219aecdb4/workspace/parametric/build_evidence.py \
  --seed 17 \
  --pass-count 1 --pass-count 2 --pass-count 3 \
  --demo-count 2 --query-count 4 \
  --out ../checks/parametric/pass-budget-s17-v1
```

The output directory must be absent or empty. The retained manifest classifies
this as `prototype_proposed_not_production_approved`; production remains the
canonical three-pass task.
