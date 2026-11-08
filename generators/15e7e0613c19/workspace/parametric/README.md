# Parametric packing rule — prototype

This task-local prototype proposes one episode-level parameter:

| Parameter | Allowed values | Original/default |
| --- | --- | --- |
| `area_order` | `ascending`, `descending` | `ascending` |

The default returns the exact canonical Racket text. Descending changes only the primary pixel-count comparison from `<` to `>`; equal areas retain ascending bounding-box height, width, and color comparisons. Objects remain individually cropped, top aligned, and separated by exactly one zero column. Production generator interfaces, canonical rules, and approval hashes are untouched.

`parameters(seed)` draws the setting once. Every demonstration and query in `episode` uses that setting. `instantiate` is reusable independently of the controlled fixtures. There are no parameter-dependent input constraints: inputs use separated, connected, monochrome nonzero motifs with background zero. The gallery uses fixed motif families, seeded unique colors and positions, and 9-row × 25-column canvases. It covers unequal areas, equal-area dimensional ties, equal-shape color ties, and a ring whose bounding-box area differs from its pixel count. This is deliberately bounded fixture coverage, not a replacement for the repaired production sampler.

## Run from the outer packet directory

```sh
python3 review.py run python3 generators/15e7e0613c19/workspace/parametric/prototype.py --out ../checks/parametric/gallery
python3 review.py run python3 -m pytest -q generators/15e7e0613c19/tests/test_parametric_gallery.py
```

Each run uses the included Racket bridge. The `rule!` wrapper is an executor directive; the prototype binds the input to `g` and evaluates the exact instantiated body in Racket. No Python transformation mirror creates labels. The gallery saves two complete episodes (seeds 1 and 0; three demonstrations and one query each), exact Racket bytes/hashes, source hashes, a shared-input differing witness, and rival comparisons. The opposite area setting is checked against all examples; a query requiring an unresolved distinction is rejected. The all-equal-area demonstration is intentionally nondiscriminating and verifies tie preservation; other demonstrations distinguish the parameter.

`public/episode-*.json` contains demonstration inputs/outputs and masked query inputs only. `private/` contains settings, full labels, source/rule provenance and the witness; it is authoring evidence, never solver input. `report.json` is authoring evidence too. Focused tests verify exact default preservation, legal connected fixtures, all three original canonical labels in Racket, parameter rivals, tie preservation, and public masking. These checks are prototype coverage, separate from canonical generator repair coverage.

Limitations: two parameter settings, two retained seeds, controlled fixtures, one query per episode, no production parametric API or approval. The prototype is proposed and runnable; acceptance of canonical repairs does not approve variants. Main-task canonical source exposure occurred during authoring after the separate blind solve was closed.
