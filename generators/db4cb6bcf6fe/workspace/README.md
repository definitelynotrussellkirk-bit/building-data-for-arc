# Review workspace: `db4cb6bcf6fe`

The selected implementation is `../generator.py`.

The reusable review tool for future changes is the focused suite at:

```text
../tests/test_generator_db4cb6bcf6fe.py
```

Run it from the repository root with:

```bash
PYTHONPATH=shared/runtime pytest -q generators/db4cb6bcf6fe/tests/test_generator_db4cb6bcf6fe.py
```

It is intentionally more than a smoke test. It proves that:

- the rule pin and Python mirror match every canonical pair;
- three plausible shortcuts fit every canonical pair;
- every ordinary generated case refutes all three shortcuts;
- every consecutive three-demo lesson identifies the intended rule against those rivals;
- the only public override is observable and typo-safe;
- generation is deterministic and does not alter global RNG state;
- both equal and unequal relations occur in every output;
- all thirteen reachable four-object relation matrices are realized.

For a stable manual probe, use `generate(0, 0, difficulty="easy")`. Its intended output differs from raw-marker, bounding-box, and completed-area rivals and is reproduced in the packet-level `QUESTION_ANSWER.md`.
