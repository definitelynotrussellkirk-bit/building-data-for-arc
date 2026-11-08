# 5cb854cd43c4

Extract every nonzero same-color 4-connected object. Sort objects by decreasing cell count, break equal-size ties by ascending color, and emit one row containing a run of each object's color with one zero between adjacent runs.

Kind: `per_puzzle`. Current version: `5.0.0`.

The three public canvas/object-count profiles and the historical exact axes (`scene_profile`, `size_regime`) remain stable. The default three-step curriculum now cycles through a disconnected-same-color witness, an equal-size/different-color tie witness, and an ordinary canonical-profile draw. Thus every three-demo lesson directly contradicts both public-example shortcuts: merging objects by color and ignoring or reversing the color tie-break.

The canonical Racket authority is unchanged (`RULE_HASH = e1a351c73552`). Final review evidence is under `checks/after/`; the source-bound 300-lesson probe is `checks/lesson_probe_300.json`.
