# Workspace

The selected implementation is `../generator.py`; workspace files are never automatically selected.

`axis_census.py` checks all 7,200 combinations of the six advertised axes on both
schedule parities at seed 98173 and hard difficulty. From the repository root:

```sh
python generators/36275402c6b2/workspace/axis_census.py --expected-rule-hash 08894540e7f2
```

It reports the actual source hash and returns nonzero for any generation,
validation, or exact-control failure. This is a Python control census, not a
14,400-case Racket equivalence check.

`sampler_evidence/` contains the exhaustive chooser probe, memory benchmark,
and retained red/green logs. See its README for reproduction and limits.
The final review return contains the authoritative Racket witness and full
battery/census receipts; task-local regressions live in `../tests/`.
