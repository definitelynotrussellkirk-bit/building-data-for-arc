# Workspace

The selected implementation is `../generator.py`, version 4.0.0. Files in this
directory are authoring tools and are never automatically selected generators.

## Extent and teaching probe

`probe_extents.py` binds retained evidence to the selected generator's SHA-256
and the canonical rule hash. It calls the canonical Racket authority on three
tiny fixtures, all ten labeled canonical pairs and indices 0..7 at all three
difficulties for seed 17. It compares the Python authoring model with those
actual Racket outputs, checks the four canonical shortcuts against the canonical
labels and enumerates the complete finite teaching geometry.

After creating the independent `.venv-review` environment and running packet
setup, run from `WORK/`. The wrapper supplies the local source paths and Racket
runtime; the payload uses the same local Python environment:

```bash
.venv-review/bin/python run_with_racket.py "$PWD/.venv-review/bin/python" \
  generators/ec9cf2c80d58/workspace/probe_extents.py \
  --out ../checks/extents-probe-replay.json
```

Choose a new output filename: the probe deliberately refuses to overwrite
existing evidence. The retained final run is
`WORK/checks/extents-probe-final.json`. It reports **37/37** valid Racket results,
zero model/canonical-label mismatches and **3,992** successful geometry checks.
Those geometry checks use Python plus an independent closed form, not per-grid
Racket. The authority receipt records canonical rule hash `899eb4e6a25d` and
does not grant catalog approval.

The geometry census spans m=7..10, p=1..m-2, every q/k=0..m-1 and both left/right
reflections using colors 1/2. It expects both selected columns plus the lower
paired row in its band and checks disagreement with the six declared rivals.
The full semantics, exact independent axes, zero-inclusive compatibility
aliases, scheduled profiles and limitations are explained in
[`../notes.md`](../notes.md) and [`../SUMMARY.md`](../SUMMARY.md).

Two small extracted receipts live under `../counterexamples/`: the combined
3x4 authoring fixture and an actual default teaching input from
`generate(17,1,difficulty="easy")`. Each retains authoritative Racket output,
separate Python rival outputs, hashes and provenance. The tiny fixture itself
is not default emitted; larger teaching versions are.

The independent final code-review commands and results are retained unchanged
in `WORK/checks/code-review-final`. The final task suite passes all 42 cases;
the final battery and lesson census results are summarized in `../SUMMARY.md`.

This probe reads public canonical authoring labels. Keep it closed during
visible-only solve sessions; it is not a solve aid. The finite six-rival/default
lesson contract does not establish universal identifiability, and explicit
overrides are outside the default lesson guarantee.
