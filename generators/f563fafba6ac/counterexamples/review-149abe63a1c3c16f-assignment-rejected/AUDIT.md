## f563fafba6ac

**Reproduced teaching shortcut; source left unchanged.** Sort objects by the total
number of enclosed background cells, then by color, instead of sorting by the
number of enclosed regions. This `hole_area` rival matches all 3 labeled canonical
pairs and 400/400 sampled generated inputs (100 per difficulty setting), because
the current generated shapes correlate `(hole count, enclosed area)` as
`(0,0)`, `(1,1)`, and `(2,5)`.

The exact 11x15 counterexample in
`checks/audit/f563fafba6ac/hole-area-rival-input.json` contains a solid object, a
one-hole object with a 9-cell hole, and a two-hole object with two single-cell
holes. Current `self_check` accepts it with observed hole counts `[0,1,2]`; it is
outside the narrower generated `hole_counts` axis domain. The selected Racket
output orders by region count and matches the Python rule mirror, while the rival
orders the two-hole object before the large one-hole object. Full inputs, outputs,
object statistics, source/rule hashes, canonical/sample fit, and limitations are
in `checks/audit/f563fafba6ac/hole-area-rival-evidence.json`; the supported Racket
receipt is `checks/audit/f563fafba6ac/hole-area-rival-racket.json`.

Audited generator SHA-256:
`ae0ce7c51dbe8cd9a78e2e44771b8364b523451c7ecaf34253a7f79e1f79d404`.
No files under `generators/f563fafba6ac/` were edited.
