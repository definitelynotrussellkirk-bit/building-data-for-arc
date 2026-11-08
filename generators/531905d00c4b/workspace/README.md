# Task-local review tools — 531905d00c4b

The selected implementation is `../generator.py`. These files are independent test/qualification tooling, not alternate label authority. The canonical Racket program remains authoritative.

## Focused tests

From the packet root, using the bundled Racket runtime:

```bash
python3 run_with_racket.py python3 -m pytest -q \
  generators/531905d00c4b/tests
```

`reference_probe.py` implements the rule independently in Python, three explicit rivals, canonical loading, and batched real-Racket parity. The tests cover canonical ownership, exact overrides, schedule semantics, malformed inputs, deterministic keyed RNG, and authority parity.

## Source-bound lesson qualification

```bash
python3 run_with_racket.py python3 -B \
  generators/531905d00c4b/workspace/qualify.py \
  --lessons-per-band 100 --parity-per-band 16 --racket \
  --out ../checks/qualification.json \
  --witness-out ../checks/shortcut-witness.json
```

The driver uses the selected generator's actual `generate` function and iterates its actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` declarations. A lesson is four consecutive visible demonstrations plus one consecutive query slot. One hundred lessons per band are split equally over cyclic schedule starts 0–3 using disjoint sample-index ranges. It records unique-input counts, profile and witness counts, per-input rival disagreement, per-lesson rival refutation, deterministic replay, canonical fit, source hashes, and real-Racket parity. Its finite schedule does not prove universal induction.

The exact strongest-shortcut counterexample is retained in `checks/shortcut-witness.json`; it includes the input, independent intended output, real Racket output, rival output, hashes, and differing-cell coordinates.
