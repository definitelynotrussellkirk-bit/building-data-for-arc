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
