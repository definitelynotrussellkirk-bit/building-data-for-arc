# aea1d569d78b

Generator version `3.0.0`; canonical rule hash `5074f7d7c8b5`.

On a background-0 canvas, find every row and every column containing exactly two blue (`1`) cells. Paint the cells strictly between those endpoints green (`3`) only when every interior cell in the original input is background. Any nonzero interior cell blocks the whole segment. Endpoints and all unrelated cells remain unchanged.

The main-path generator stays close to the five canonical pairs: it uses one of the canonical dimensions (`8×10`, `9×8`, `9×9`, `10×10`), exactly six blue cells forming three disjoint pairs, and a four-color input palette. Every generated example contains one clear horizontal pair, one clear vertical pair, and one blocked pair with a blocker other than color `5`, plus a second singleton distractor. This makes each example distinguish the intended rule from horizontal-only, vertical-only, connect-through-blockers, identity, and the canonical-fitting shortcut “only color 5 blocks.”

Exact override axes are `canvas_profile` and `blocked_orientation`. Difficulty controls composition rather than canvas size: easy keeps the clear pairs separated, medium mixes separated and crossing layouts, and hard makes the clear horizontal and vertical paths cross while retaining orientation-exclusive painted cells.

`rule_mirror` is a task-local independent Python oracle for tests and probes. The canonical Racket implementation remains the label authority; its semantics were not changed. The base authority record was synchronized so `raw_code` and `target_code` contain the same executable source.

Approval is derived by the catalog from current code and retained evidence.
