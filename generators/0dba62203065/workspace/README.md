# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The
selected implementation is `../generator.py`; workspace drafts are never
automatically selected.

## Focused review probe

`review_probe.py` is a fast, source-bound pre-battery contract check for this
task. It reports the exact generator hash, canonical rival behavior, unique
input counts, the deterministic sampler, legend-profile counts, rival
refutations, sliding-window identifiability, difficulty contrasts, and override
boundaries.

From the repository root, use the assignment-strength 100-per-band census:

```bash
python3 generators/0dba62203065/workspace/review_probe.py \
  --samples-per-band 100 \
  --json-out ../checks/probe/0dba62203065_review_probe_100.json
```

For a quick edit loop, reduce `--samples-per-band` to 6 or 12. The probe exits
nonzero on any contract failure. It checks canonical parity, the canonical
first-cell/size/cycle shortcuts, randomized grammar, declared semantic-rival
refutations, every two-demo sliding window, equal-seed easy/hard contrasts, all
64 legacy boundary-override combinations, and unknown-key rejection.
