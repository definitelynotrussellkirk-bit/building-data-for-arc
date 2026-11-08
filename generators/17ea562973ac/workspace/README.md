# Review workspace for 17ea562973ac

- `reference_probe.py` is an independent Python geometry oracle, public-axis observer, and wrong-rule model. It deliberately does not import production geometry helpers.
- `audit_generator.py` runs a deterministic canonical, distribution, oracle-parity, and semantic-counterexample census against either `../generator.py` or a candidate passed with `--generator`.

Example from this task directory:

```bash
PYTHONPATH=../../shared/runtime python3 workspace/audit_generator.py --samples 200
```
