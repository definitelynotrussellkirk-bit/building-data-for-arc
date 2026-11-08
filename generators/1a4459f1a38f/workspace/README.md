# Workspace

`review_census.py` is a standard-library, Racket-free distribution and shortcut probe for this generator. It loads the selected source directly, then measures:

- four-slot curriculum balance;
- incidence of every declared semantic witness;
- actual answer disagreement for each witness-linked rival;
- identifiability of every contiguous three-demo plus one-query window.

From the extracted packet root:

```bash
python3 repo/generators/1a4459f1a38f/workspace/review_census.py \
  --draws 32 --seed-count 8 --base-seed 17000 \
  --out checks/review_census_after.json
```

The command returns nonzero when a band has an absent witness/rival disagreement or an unidentifiable lesson window. `--allow-failures` is available for exploratory censuses. `test_review_census.py` is the focused regression for the probe itself.

This tool is supplemental: its candidate outputs are Python mirrors and do not replace the official Racket-backed battery.
