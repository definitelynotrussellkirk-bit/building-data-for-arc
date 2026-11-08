# Workspace

`reference_probe.py` is independent reviewer tooling for task
`af373b71d67d`. It can check canonical ownership, deterministic distribution
coverage, named semantic rivals, schedule witnesses, and real Racket parity:

```bash
python3 run_with_racket.py python3 \
  generators/af373b71d67d/workspace/reference_probe.py \
  --count 250 --racket --out ../checks/independent-audit.json
```

The selected implementation remains `../generator.py`. Workspace tools and
drafts are never automatically selected as label authority.
