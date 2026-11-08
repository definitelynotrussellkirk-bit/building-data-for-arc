# fe947dc3e12c workspace

This workspace contains non-selected authoring material for the assigned generator.

## Parametric prototype

`parametric/prototype.py` implements one small rule parameter:

- `rank_order=largest_first` — canonical default;
- `rank_order=smallest_first` — proposed variant.

Both settings retain the same object extraction, size ranking, shape preservation, and custom rank palette. The tool instantiates a Racket rule, creates three demonstrations plus one query, verifies all labels against live Racket, and checks that the demonstrations distinguish the selected setting from the other declared setting.

Run from the repository with the protected Racket runtime available:

```bash
python3 generators/fe947dc3e12c/workspace/parametric/prototype.py \
  --seed 20261020 --out-dir /tmp/fe947dc3e12c-parametric
```

Retained review evidence is under `WORK/checks/parametric-final/`. Status is `proposed_not_selected`; this directory does not alter the selected production rule or generator path.
