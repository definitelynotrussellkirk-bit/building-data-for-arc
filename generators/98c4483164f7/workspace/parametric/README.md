# Proposed marker-ray family: 98c4483164f7

Status: **prototype / proposed**, original ARC family `training:1f0c79e5`.
Canonical generator version `2.0.0`, source `34e2b872a68979a620411d5ea434100d2489073e19bc74fe4e72602945603a78`, rule `18ad2f5cfd8b`.

## Rule and parameters

A filled nonzero 2×2 motif contains one to three red (`2`) direction markers and a shared payload color. Each marker selects its diagonal quadrant. Recolor the complete motif to the payload, rotate the selected directions, and project from **all four** motif cells at the selected spacing.

| Parameter | Exact integer values | Canonical default | Meaning |
|---|---|---|---|
| `quarter_turns` | 0, 1, 2, 3 | 0 | Clockwise quarter turns in screen coordinates: `(dr,dc) → (dc,-dr)` |
| `stride` | 1, 2 | 1 | Paint positive multiples of this diagonal step distance |

Settings are fixed across all demonstrations and queries of an episode. All eight combinations admit the same canonical grammar: rectangular 2..30 grids, background0, one filled2×2 motif, 1..3 red cells, one nonzero/non-red payload. The original `(0,1)` setting returns the canonical Racket program **byte for byte**. Default program SHA-256: `fdc71b2be177a0197cd76c0b630fd5d8fff555a81213c965201b40aed25fb16d`.

## Generate real Racket-labelled examples

Run from the outer extraction directory with Python3.12+ and the packet's declared NumPy/Pillow dependencies:

```bash
python3 review.py setup
python3 review.py run python3 generators/98c4483164f7/workspace/parametric/build.py generate --seeds 0 17 --demos 3 --queries 4 --out ../checks/parametric/my-run
python3 review.py run python3 generators/98c4483164f7/workspace/parametric/build.py verify ../checks/parametric/my-run --replay
```

The first command includes all eight settings unless `--quarter-turns` and/or `--stride` select a subset. The output directory must be new. The retained final evidence uses `../checks/parametric/final` and exactly the same counts/seeds. Each episode has three demonstrations and four distinct queries. The protected worker executes every setting on the demonstrations, requires the chosen setting to be the sole surviving parameter setting, then executes every query with that setting. The optional replay executes all saved demonstration/query labels again.

`public/` contains only canonical visible challenge JSON, named by SHA-256 of the exact visible bytes. It includes demonstration inputs/outputs and query inputs. Give only this directory to a solver. Settings, seeds, query answers, reference code, source/runtime hashes and certificates are in `private.json` and `manifest.json`; their values never enter public filenames. Public entries are sorted by visible ID; duplicate visible content is rejected before creating the destination.

`verify` without `--replay` checks source hashes, file hashes, public/private projection, strict colors/counts, private labels using the independent Python mirror, and recomputed finite-rival certificates. It reports `racket_replayed:false`. `--replay` adds actual protected Racket execution. This verifier is not an owner acceptance receipt.

## Sampling and finite teaching support

`episodes.generate_episode(seed, settings, demos, queries, *, grid_h=None, grid_w=None, max_attempts=256)` supports exact demo counts3..8 and query counts1..8. Seed is an integer0..2^63−1; retry budget1..4096. Booleans/floats are rejected for these controls. Exact input dimension overrides6..30 reuse the production generator. Otherwise the prototype cycles through9×9,12×16,20×24,6×6,30×30,6×30,30×6,18×25. This preserves small and meaningful long-ray boundary examples. Input dimensions are sampling controls, not hidden rule parameters.

Inputs are deduplicated across the whole episode. Every attempt, including duplicates, consumes budget; weak lessons advance a distinct rolling window. Exhaustion raises `SamplingError` instead of cloning queries or reducing requested counts.

The Python lesson certificate tests eight settings plus40 named shortcut variants (no rays, all directions, marker-only origins, first marker, and one-step rays across all settings). Fitting uses demonstrations only. Query inputs determine whether any surviving hypotheses disagree; query answers cannot be supplied to this API. Racket independently checks all eight genuine parameter programs. Shortcut checks use independent Python predictors, so the evidence is finite and does not prove identifiability against arbitrary programs.

## Promotion and focused tests

`adapter.py` and `promotion.json` expose the documented owner qualification interface. The current owner prototype inventory must be updated to bind these new files before the ordinary qualification/acceptance route can promote them. This return does not modify that inventory, accept variants, or admit training data.

From the packet root:

```bash
python3 review.py run python3 -m pytest -q -p no:cacheprovider generators/98c4483164f7/tests
```

The three new stdlib unittest files can also be executed individually if pytest is unavailable. Evidence in `WORK/checks/` records the actual local dependency path used here. Existing canonical production generation/approval stays separate from this prototype.
