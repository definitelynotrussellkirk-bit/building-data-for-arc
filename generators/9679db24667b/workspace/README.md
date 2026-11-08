# Reviewer workspace for 9679db24667b

`reference_probe.py` is an independent, portable checker for this task. It does
not call the generator's `rule_mirror`, row-analysis helpers, witness predicates,
or a copied list of rival names.

From the packet root:

```bash
PYTHONPATH=repo/shared/runtime python3 \
  repo/generators/9679db24667b/workspace/reference_probe.py \
  --samples-per-band 100 \
  --out checks/probes/9679db24667b-independent-probe.json
```

It checks:

- the independent row oracle against every labeled canonical pair;
- generated self-check validity, uniqueness, and profile counts by band;
- that every declared canonical shortcut really fits the canonical labels;
- that every declared lesson competitor is refuted by a teaching input;
- all cyclic starts across two complete schedule cycles and every 3-of-4 query
  rotation.

The report is source-bound with generator and probe SHA-256 hashes. It is
supplementary evidence only; use the repository battery and Racket authority for
final validation.
