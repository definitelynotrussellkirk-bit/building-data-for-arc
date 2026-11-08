# Workspace tools

`analyze_contact_graph_distribution.py` is the task-linked diagnostic created
for this review. Generic uniqueness metrics missed the original failure because
random colors and positions looked diverse even though most scenes exercised
only degree 0.

Run it from the generator directory or from anywhere by path:

```bash
python3 workspace/analyze_contact_graph_distribution.py \
  --samples-per-band 20 \
  --json-out workspace/contact_graph_report.json
```

It reports generated profile/style histograms, degree-branch coverage, canonical
acceptance, and survival rates for every declared semantic rival. It exits
nonzero for malformed draws, rejected canonical inputs, or missing degree
branches (unless `--allow-missing-degree-branches` is explicitly supplied).
