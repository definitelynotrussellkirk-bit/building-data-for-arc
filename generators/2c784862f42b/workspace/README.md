# Workspace

`reference_probe.py` is the reusable independent probe for this task. It:

- loads all five canonical pairs and selected Racket source from the repository ledger;
- computes the normalized rule hash;
- reconstructs all six transforms and cumulative gallery assembly without importing production transform helpers;
- extracts prototype cells and opcode sequences;
- implements the three semantic rival outputs;
- loads either `../generator.py` or a retained candidate selected by `GENERATOR_UNDER_TEST`.

The selected implementation remains `../generator.py`; workspace files are never automatically selected. Focused tests live in `../tests/test_generator_2c784862f42b.py`.
