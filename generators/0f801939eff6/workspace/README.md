# Workspace tools

`shortcut_probe.py` is a source-bound reproducer for the strongest canonical
shortcut and the repaired curriculum. It independently extracts 4-connected
components, compares the intended rule with color-frequency aggregation and a
position-based tie-break, generates both repaired witness profiles, and (unless
`--no-authority` is used) checks the examples through the selected canonical
Racket rule.

From the packet root:

```bash
python3 review.py run python3 generators/0f801939eff6/workspace/shortcut_probe.py \
  --samples-per-band 100 --out ../checks/final-shortcut-probe.json
```

The selected implementation remains `../generator.py`; workspace scripts are
review/audit tools only.
