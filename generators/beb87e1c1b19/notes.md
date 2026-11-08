# Review notes: `beb87e1c1b19`

## Result

The retained base generator and canonical labels passed focused inspection, so the
base source was left unchanged. A complete task-local parametric family was added
under `workspace/parametric/`.

- `composition=union` is the exact canonical/default Racket program.
- `composition=xor` infers the same A→B dihedral transform, applies it to C, and
  keeps cells occupied by exactly one of C and T(C).
- Demonstration and query streams are independent and prefix-stable; inputs are
  matched across settings. Supported counts are 2–6 demonstrations and 1–4
  queries. The fourth query is a substantive 30×30 rectangular-panel case.
- The sequential dependency is transform inference/application → transformed C
  → episode-fixed composition. The protected `wrong_identity_intermediate`
  witness changes 6 cells when C is substituted for T(C).

## Retained verification

- 7/7 staged task tests.
- 16-seed audit: 32 episodes, 320 pairs, 640 demonstration-prefix checks, 320
  query-prefix checks, 320 setting-output changes, 320 identity-intermediate
  ablation changes, and 32 30×30 queries.
- Authoring preflight: four source-bound jobs and 32 protected-Racket labels.
- Public projection: 16 independent one-query views; 24 private-field invariance
  checks and four positive controls.

## Handoff limits

This is reviewer-ready authoring work, not owner acceptance or training admission.
The owner must review the exact source, run native qualification, and freshly
accept the integrated bytes. Finite seeds/settings do not prove universal
identifiability against every possible rival rule.
