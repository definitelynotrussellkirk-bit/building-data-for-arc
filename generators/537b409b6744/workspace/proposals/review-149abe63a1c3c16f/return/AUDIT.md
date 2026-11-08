# Adversarial audits — review-149abe63a1c3c16f

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

## 64a8d13b4024

**Reproduced override-contract defect; source left unchanged.** The advertised
exact controls are not reliable:

- `grid_h=8`, `grid_h=14`, `grid_w=8`, and `grid_w=14` are declared valid but
  raise `ValueError` because generation internally requests only 9..12.
- `n1=n2=n3=2` silently returns counts `2,2,3` by rewriting `n3`.
- an unknown `typo=1` key is accepted;
- `palette_kind=default` and `palette_kind=warm` produce byte-identical grids;
- `texture=missing_color` bypasses requested 14x14 dimensions and 6/6/6 counts,
  returning a fixed 10x10 scene with counts 0/2/3.

The exact calls and deterministic output hashes are in
`checks/audit/64a8d13b4024/override-contract-evidence.json`. The isolated official
override stage failed after 83,160 draws with 4,586 findings: 3,240 override
mismatches, 1,320 generation errors, 22 axis-effect findings, 2 metadata findings,
1 provenance finding, and 1 accepted unknown key. Concise official evidence is
`checks/audit/64a8d13b4024-override/checks/64a8d13b4024_audit_battery_summary.json`
and its override log.

Audited generator SHA-256:
`c814a464d558cc1d3df388a88a67850ab4adfd553eeb95c5af027d599e4b4f71`.
No files under `generators/64a8d13b4024/` were edited.
