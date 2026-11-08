# Workspace

The selected implementation is `../generator.py`. Workspace utilities are review aids and are never selected automatically.

## Independent review probe

`review_probe.py` independently loads canonical pairs, extracts 4-connected components, compares cell-count and bbox-area solvers, checks observable overrides/determinism across difficulty bands, and can compare a bounded sample with the packet's real Racket authority.

From the extracted packet root:

```bash
python3 run_with_racket.py python3 generators/148cea0afb09/workspace/review_probe.py \
  --count 250 --racket --out ../checks/generator-independent-audit.json
```

The report is supplemental evidence: Python mirrors do not replace the canonical Racket program.
