# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Independent reference probe

`reference_probe.py` is a task-local future-agent tool. It does not import the production generator's geometry/parser helpers. It:

- parses framed inputs directly from pixels;
- computes the Manhattan-bisector output independently;
- loads all canonical pairs and checks the canonical-fitting `diagonal_only` rival;
- constructs a concrete aligned-seed witness;
- measures default distribution support and determinism;
- audits every cyclic query position in consecutive four-pair windows;
- optionally compares selected cases with the real Racket authority.

From the packet root, run:

```bash
python3 run_with_racket.py python3 \
  generators/39abddf600eb/workspace/reference_probe.py \
  --count 250 --racket --out ../checks/reference-probe-new.json
```

For a candidate generator at another path, add:

```bash
--generator /absolute/or/repo-relative/path/to/generator.py
```

Use a new output path for every run. The report binds generator/probe hashes, exact sample design, canonical counts, distribution counts, cyclic rotations, witness cells, and Racket results. Keep task tests under `../tests/`; do not modify frozen root fixtures merely to obtain a pass.
