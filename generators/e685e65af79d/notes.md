# Working notes: e685e65af79d

## 2026-10-25 source review and native parametric build

The retained episode admitted a half-turn-only shortcut: demonstrations could be matched by the original shape plus its 180° copy even though the selected rule requires all four rotations. The old shape control also did not provide reliable exact selection. Version 3.0.0 uses a validated connected square-bounding-box shape bank, guarantees at least one object whose 90° copies add cells beyond half-turn closure, honors `blob_shape_idx` exactly, and fails loudly if all requested objects cannot be placed.

The first alternative prototype completed every object under the full dihedral group. A later adversarial review rejected it: the sampled D4 closures filled their entire 4×4 boxes, so a learner could bypass the claimed intermediate with a simple “fill each bounding box” rule. That prototype and its evidence were discarded before final qualification.

The replacement family adds `symmetry_closure`:

- `rotational_4` preserves the selected canonical Racket program byte-for-byte.
- `largest_closure_dihedral` has a selector-dependent sequential rule. Step A constructs every object’s four-rotation closure and measures its unique-cell area. Step B selects the unique largest Step-A closure, horizontally reflects that entire closure inside its bounding box, and unions it back. All other objects remain rotationally closed.

The sampler uses four connected chiral 5×5 families with distinct rotational-closure areas (13, 16, 17, and 20) and non-full dihedral masks. The winner is never the first row-major object. Finite executable rivals include original-only, half-turn-only, first-object-only, fill-each-box, all-dihedral, wrong-first selector, smallest-closure selector, and largest-original-area selector. The protected Racket counterfactual uses the wrong row-major-first selector, so it preserves the computation but corrupts the intermediate chosen by Step A.

Authored limits are 2–6 demonstrations and 1–4 private queries, with a substantive 30×30 eight-object stress query. Evidence and qualification are source-bound under `workspace/parametric/evidence/current/` and `WORK/checks/e685e65af79d/`. Training admission remains false pending owner review and integration.
