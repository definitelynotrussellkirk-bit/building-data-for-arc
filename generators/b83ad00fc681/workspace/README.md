# Reviewer workspace for `b83ad00fc681`

The selected implementation is `../generator.py`; files here are independent review tools and are not label authority.

- `reference_probe.py` parses the visible prototype dictionary independently, implements the intended stamper, implements the canonical-fitting fixed-dictionary rival, exposes the portable canonical pairs, and can batch-check the real selected Racket rule.
- `audit_sampler.py` runs a deterministic three-band sampler audit, checks the public validator/observer contracts, measures axis support and uniqueness, saves an exact rival counterexample, and optionally verifies Python/Racket parity.

From the packet's `repo/` directory in a Racket-enabled environment:

```bash
python3 generators/b83ad00fc681/workspace/audit_sampler.py \
  --count 100 --racket --out ../checks/sampler-audit.json
```

The report records the generator and probe SHA-256 values and the replay tuple for its first fixed-dictionary counterexample. It is a finite declared-rival audit, not a proof of universal identifiability.
