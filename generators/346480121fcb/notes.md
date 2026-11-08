# Working notes: 346480121fcb

## Current decision

Retain the exact canonical default and add one episode-fixed selector parameter:
`selection_mode=color` uses the upper-left marker as a color, while
`selection_mode=area` uses it as the unique selected object's cell count. Both
settings receive byte-identical inputs. The selected object's crop is the
input-dependent intermediate consumed by the unchanged key-coded transform.

## Base repairs

- Replaced the former easy-only identity behavior with full key 1–5 sampling at
  every difficulty, while preserving difficulty only as a size-distribution
  bias.
- Restricted the public override surface to four honest axes: `grid_h`,
  `grid_w`, `key`, and `blob_count`; unknown controls and Boolean integers fail
  loudly.
- Removed diagnostic texture fixtures from the advertised production contract
  because they ignored other requested overrides.
- Added `observe_overrides(grid)` and strict `self_check()` coverage. The final
  override audit accepted 22,590 draws with zero findings.

## Adversarial findings and repairs

1. A minimum lesson at one seed allowed an `always transform with key 2` rival
   because two transforms happened to coincide on a teaching shape. Minimum
   teaching shapes now have five pairwise-distinct transform results; the
   bounded 128-seed / 256-episode probe reports zero full-lesson survivals for
   ten tested selection and transform shortcuts.
2. The episode verifier initially allowed a forged output to replace a zero
   with `False`, because Python equality treats `False == 0`. Outputs now receive
   an independent rectangular exact-integer ARC-grid check, and the reusable
   adversarial probe retains this regression.
3. Crossed controls cover both candidate scan orders, size relations, and color
   ranks. Certificate attacks also cover duplicates, one-demo forgeries,
   Boolean input/output cells, stale programs, wrong labels, undeclared settings,
   first-turn prefix stability, and private/future-field leakage.

## Evidence and limits

The final authoring preflight executed 24 parametric labels plus four canonical
base labels through protected Racket (32 evaluations total), with two settings,
two demonstrations, and four distinct queries per episode. A protected
wrong-intermediate witness changes the final output under the same transform key.
The public projection verifies 16 single-query views, 24 private-field invariance
checks, and four positive controls. These are finite reviewer checks, not a proof
of universal lesson uniqueness. Owner source review, native qualification,
acceptance, and any training admission remain pending; no approval flags changed.

Next action: the owner should inspect the exact source bound by
`checks/346480121fcb/qualification-v2/qualification.json`, replay native
qualification/acceptance, and decide whether to admit the family.
