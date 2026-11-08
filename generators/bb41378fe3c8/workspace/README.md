# Workspace

The selected implementation is `../generator.py`; workspace files are diagnostic
helpers and are never selected automatically.

`qualification_probe.py` is the compact source-bound regression tool for this
repair. It checks:

- the historical 6×6 / seven-marker exact-override failure over seeds 0–199;
- that every currently declared canonical shortcut fits every public pair;
- all eight cyclic schedule starts, four query positions, eight seeds, and four
  difficulty labels against every currently declared lesson competitor.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/bb41378fe3c8/workspace/qualification_probe.py \
  --out ../checks/qualification.json
```

The probe uses `rule_mirror` on generated inputs. The Racket-backed battery and
lesson census remain the authoritative output checks.
