# Reviewer workspace

The selected implementation is `../generator.py`; files here are independent
review probes and are never selected as production code.

- `reference_probe.py` reads canonical pairs through the portable reviewer
  helper and implements rotation geometry independently of the generator. It
  supplies the intended output, the geometric-center rival, the
  full-orbits-only rival, and observable profile classification used by focused
  tests.
- `../tests/test_generator.py` is the executable regression contract. Run from
  the packet's `repo/` directory with:

  ```bash
  PYTHONPATH="$PACKET/repo/shared/runtime:$PACKET/repo/src" \
  GENERATOR_UNDER_TEST="$PACKET/repo/generators/ba0c6a5828f9/generator.py" \
  python3 -m pytest -q \
    "$PACKET/repo/generators/ba0c6a5828f9/tests/test_generator.py"
  ```

The reference probe is intentionally supplementary evidence. The selected
Racket program remains label authority, and neither visible-only solve may use
this workspace.
