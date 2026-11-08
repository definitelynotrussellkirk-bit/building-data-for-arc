## ddf6f818956c

**Disposition: corroborated existing unresolved findings, with selected Racket replay pending.** This is a findings-only audit; the audited generator was not edited. The current source SHA-256 is `8c3a652d2bd2aaa66cabf07b3321af39fa5e5cf3f08fe7be892d229dfc693f70`, exactly matching the unresolved audit already retained in `generators/ddf6f818956c/evidence/review_index.json` (`review-02d147bb3756aa81:v0001`). These observations corroborate that same-source report; they are not newly introduced regressions or an approval decision.

### Canonical coverage is excluded by the current sampler and hook

The canonical ledger contains two task records with the same Racket program and eight labeled input/output occurrences, representing **four unique canonical inputs**. Fresh inspection rejects **8/8 occurrences, 4/4 unique inputs** through the selected generator's `self_check`. All canonical gray sources are inside the red bounding box. The canonical rule reflects them outward through the selected boundary. By contrast, all **600/600** sampled generated inputs place every gray source outside the box, and all are accepted by `self_check`.

The bounded generated census uses seeds `0..199`, `sample_index=seed*19`, each of `easy`, `medium`, and `hard`, with no overrides. It contains 294 vertical and 306 horizontal cases. A concrete simpler rival, **apply the reference reflection only to exterior gray sources and preserve interior gray sources**, agrees with the Python reference mirror on 600/600 sampled generated inputs while disagreeing with all supplied canonical labels. Thus these draws provide no witness against this exterior-only shortcut. This is a generated-input coverage observation, not a proof about every seed, an episode identifiability result, or a claim of wrong executed labels.

For a precise canonical counterexample, primary `train[0]` is 15×15, with red bounding box `(top=3,left=3,bottom=10,right=10)`. Its eight gray cells are inside that box; the first is `(5,5)`. `self_check` reports `horizontal marker (5, 5) must sit outside frame horizontally`. Primary `train[1]` has a solid top bar but incomplete left/right walls, another canonical topology excluded by the hook: it reports `red bbox must have complete left and right walls`.

The direction/topology limitation is **hook-detected** on canonical inputs. It should not be described as a silent wrong-output bug. The Racket rule supports the inward extension as well as the canonical outward cases; the observed problem is that production sampling and validation exclude the canonical subdomain.

Evidence: `checks/audit/ddf6f818956c/python-report.json` records every canonical occurrence, its exact input hash, bounding-box facts and hook errors, plus the bounded generated census. Python mirror outputs match the supplied canonical labels 8/8; that statement is explicitly Python-only pending selected reference execution.

### Declared size controls are silently ignored

The API problem is independently reproduced and remains silent when requested overrides are passed to `self_check` through `meta`:

| Call | Declared request | Actual result | Hook errors |
|---|---|---|---|
| `generate(0,0,difficulty="medium",grid_h=10,grid_w=10)` | 10×10 grid | 12×12 grid | `[]` |
| `generate(0,0,difficulty="medium",frame_h=8,frame_w=8)` | 8×8 frame | 5×4 frame | `[]` |
| `generate(0,0,difficulty="medium",grid_h=18,grid_w=18,reflection_axis="horizontal")` | 18×18 grid | 13×12 grid | `[]` |

The requested dimension values are within the generator's declared `AXES` ranges. The implementation samples grid and frame dimensions from difficulty ranges and never reads these four override keys. Exact returned inputs, seeds, indices, requested overrides, shapes, bounding boxes and hook results are retained in `python-report.json`. This is an **accepted-input API contract defect**, distinct from the canonical cases that the hook visibly rejects.

### Execution scope and selected reference replay

The Python probe completed with exit **0**. Exact argv, cwd, `PYTHONPATH`, stdout and stderr are retained in `checks/audit/ddf6f818956c/python-command.json`. It performs no Racket execution and no full battery. The audited source snapshot is `generator-source.py`; the exact common Racket source is `reference-program.rkt`. Generator, canonical ledger, raw Racket, normalized rule, notes, current review index, probe and command-receipt hashes are bound in `source-bindings.json` and `python-report.json`.

Selected Racket replay is pending at draft time. `input.json` provides five cases: primary canonical `train[0]` and `train[2]`; generated `seed=0,sample_index=0` at `easy` and `hard`; and the accepted `grid_h=10,grid_w=10` override mismatch at medium difficulty. `selected-expected-rivals.json` supplies exact identities, input grids, expected outputs and rival outputs. Canonical expectations are supplied labels; generated expectations and rival predictions are explicitly Python-derived until the root reviewer executes the selected batch. Root should append the actual Racket command, receipt, exit and equality result after that replay.

Recommendation: retain this audit as actionable against the unchanged source. Restore the canonical interior-source/outward-reflection cases and horizontal-bar topology in sampling/validation, retain inward reflection as an explicit extension if desired, and honor or reject declared dimension overrides. No target patch is included.
