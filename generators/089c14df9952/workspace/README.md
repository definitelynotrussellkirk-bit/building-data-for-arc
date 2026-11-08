# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace drafts are never automatically selected.

## Retained review evidence

`scene_uniform_hint_policy_counterexample.json` is a fully materialized replay fixture for the strongest canonical-fitting shortcut found in the 2026-09-28 review. It includes:

- generation coordinates (`seed=4201`, `sample_index=2`, medium, explicit clip overrides);
- the exact input, intended output, and rival output;
- analyzed target cue/clipping facts;
- four disagreeing cells;
- frozen-before and revised-after 600-draw census totals;
- the focused test and authoritative semantic-gate evidence path.

The source of truth remains the deterministic generator plus its regression test; the JSON is for inspection and future-agent debugging.
