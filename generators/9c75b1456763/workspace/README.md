# Task workspace

The selected implementation is `../generator.py`. Workspace files are never automatically selected.

## Source-bound semantic probe

Run from the packet root:

```bash
python3 repo/generators/9c75b1456763/workspace/semantic_probe.py \
  --per-band 120 --seed-base 31000 \
  --out checks/semantic_probe_final.json
```

The probe imports the selected generator by path and records its SHA-256 and declared rule hash. It reads the generator's actual `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `EXAMPLES_NEEDED`, and schedule rather than duplicating a rival-name list. It reports strict validity, unique inputs/outputs, exact-axis counts, changed-cell ranges, witness/rival disagreement, canonical shortcut fit, and all cyclic lesson starts.

The report is finite generated-domain evidence. Do not interpret it as universal induction, masked-query accuracy, or correctness outside `self_check`.
