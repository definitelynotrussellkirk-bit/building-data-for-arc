# Working notes: 94755460a402

## Current decision

Build one native two-setting family around **where the transformation command is
read** while preserving all canonical frame-selection and crop semantics:

- `header` is the byte-exact canonical default and reads `(0,1)`.
- `selected_marker` first selects and crops the selector-colored frame, then
  reads the cropped motif's top-left marker.

This gives a concrete sequential dependency: frame selection/cropping produces
an input-dependent command that is required before choosing the transform.
Settings share identical generated inputs; only labels/programs differ.

## Review findings and repairs

1. The first sampler randomized vertical frame offsets. That could change the
   canonical row-major frame order instead of merely varying geometry. Frame
   tops are now fixed by slot; dimensions and horizontal placement still vary.
2. One inset demonstration allowed `strict_interior_top_left` to imitate the
   selected marker. The second constructive demonstration now also uses an
   inset selected motif.
3. A 64-seed sweep found five minimum-demo failures where
   `selector_mod_five` survived both demonstrations and changed query answers.
   The selected frame color in each of the first two demonstrations is now
   chosen constructively so its modulo-derived command differs from both lawful
   command sources. The retained before-repair cases are in
   `checks/94755460a402/teaching-hole-before.json`.

## Retained evidence

- `checks/94755460a402/bounded-sweep.json`: 64 seeds × 2 settings × 5 demo
  counts; 640/640 episodes and 5,120 labeled pairs passed, with all frame counts,
  selected positions, and transform commands covered.
- `workspace/parametric/evidence/current/audit.json` and packaged copy
  `checks/94755460a402/racket-audit.json`: 26 protected Racket evaluations over
  seeds 0 and 17, including the causal counterfactual; all labels matched.
- `checks/94755460a402/qualification/`: native qualification for both settings
  on two seeds, three demonstrations, and four queries.
- `checks/94755460a402/causal/witness.json` plus `causal-check.json`: protected
  replay of selected-marker versus skip-A/header behavior.
- `checks/94755460a402/task-tests/result.json`: 18 focused staged tests passed.

## Exact bindings and limits

- canonical Racket SHA-256: `8a0dd363ab686d1cd32d3f28b8fef7ce61362233141e6bb598ef1dc624cc0e2c`
- alternative Racket SHA-256: `629f751726292196669177f0a3eb24b93cf62ecb744a29a37fb8419aa58172fe`
- prototype SHA-256: `a50afb61b71871b15eb779bad59ad5a0a8b7ffcaaebb339712946c76688f3328`
- source inventory SHA-256: `aca3547897cb6b5d745702fa790eb58189c15c52259b9e03f931c95af040836c`
- qualification SHA-256: `0410d9519984bdbfcabbd8d8fe2a50a40556c5c49a1fb1303e0baabbebe5d36a`

Evidence is finite over the declared grammar, settings, rivals, and sampled
seeds. It does not prove universal identifiability, measured learning benefit,
owner acceptance, or training admission. The next useful action is owner-side
integration followed by the required fresh native qualification/acceptance
replay on the integrated bytes.
