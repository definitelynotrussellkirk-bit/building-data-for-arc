# Working notes: f8b9516df05e

## 2026-10-05 review-81a161b804acb61f

Baseline v3.1.0 source hash: `a8e8eea74c36b9b94853d368b6d554223d99ba8a895406108163b6d5efd283df`.
Final v4.0.0 source hash: `1fd382c592775506b3e97df1da68f409f65fd7c3794c5b23ff63b992c9e9a62b`.

### Root cause

The selected Racket authority was correct. The Python generator had drifted away from the canonical domain: medium/hard grids were much larger and denser, a synthetic post-blocker decoy was mandatory, every canonical input failed `self_check`, several axes were aliases/dead/invalid, unknown keys were accepted, and `RULE_HASH` plus an executable semantic contract were missing.

### Repair

- Pinned rule hash `d469cd5280c8`; no Racket or canonical-data edit.
- Replaced stale axes with exact observable `grid_h`, `grid_w`, `rays`, and `post_blocker_cells` controls.
- Restored a sparse canonical-centred default distribution while preserving legal tails.
- Split broad lawful-domain validation (`self_check`) from canonical-scale measurement (`strict_canonical_like`).
- Added unit-gap and trailing-background witnesses with `skip_unit_gap` and `ignore_blocker` rivals.
- Added 42 focused tests plus independent probes in `workspace/reference_probe.py`.

### Final evidence

- 12/12 after-battery stages green.
- 42/42 focused tests pass.
- 29,880/29,880 exact override draws accepted with zero findings.
- 300 lessons, 1,200 query rotations, 1,200 unique inputs, zero ambiguity/errors against declared rivals.
- Post-repair solve revision 1 passes 3/3 visible examples; masked labels remain unknown.

### Known limitation

Every generated grid carries both anti-shortcut witnesses. This is a deliberate teaching restriction, not a statement that every lawful input must contain them. The census is finite and covers declared rivals only.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

Maintainer collision merge: combined review-ef399102e8a4504c first-versus-last gray-blocker evidence with accepted review-81a161b804acb61f controls and unit-gap/ignore-blocker witnesses. Version 4.1.0 has focused 51-test/five-Racket-fixture evidence only; neither old 12/12 battery report applies to these merged bytes. See evidence/maintainer-merge-review-ef399102e8a4504c.json.
