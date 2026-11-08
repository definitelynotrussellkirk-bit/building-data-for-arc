# Workspace tools

`reference_probe.py` is a source-bound diagnostic for future reviewers. It uses
an independent Python row scanner (not the Racket authority), samples ordinary
draws in all four difficulty settings, checks the generator's strict grammar and
axis observer, and retains one full input/truth/rival counterexample for every
declared lesson competitor.

From the repository root:

```bash
PYTHONPATH=shared/runtime:src python3 generators/7e7614405852/workspace/reference_probe.py \
  --per-band 100 \
  --out ../checks/reference-probe.json
```

A nonzero exit means an invalid draw, an oracle/mirror disagreement, a missing
default witness, a surviving declared rival, or failure to retain a rival
counterexample. This is a finite regression probe, not a uniqueness proof and
not a substitute for the Racket authority or the shared lesson census.
