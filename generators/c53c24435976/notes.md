# Working notes: c53c24435976

## Current decision

The base generator is retained and repaired, and the task now has a two-setting native parametric family under `workspace/parametric/`. The canonical setting is byte-identical to the catalog program; the nearby setting is a genuinely sequential command chain.

## Base repair

- `generator.py` now honors the declared `code=1..4` override instead of drawing a different command from its private RNG.
- Unknown overrides are rejected rather than silently ignored.
- `self_check` accepts all five canonical examples, including same-color command/object cases and the canonical three-cell crop, while generated examples still require a visible nontrivial transform.
- Current generator SHA-256: `80bdaa5490a00013933e2ce11da8035e759632759edbba2e21d4d19458d2f58a`.

## Parametric design

- Parameter: `command_chain` with `outer_only` and `outer_then_corner`.
- `outer_only`: crop nonzero content excluding `(0,0)`, then apply the command at `(0,0)` exactly once. Canonical program SHA-256: `f1e4f960e8ed2b669446dcd20ce6d28cf8903faa131cdcf813a05233df3a3835`.
- `outer_then_corner`: perform the canonical transform to obtain `stage1`, read `stage1[0][0]` as an input-dependent second command, then transform `stage1` again. Variant program SHA-256: `a422403c56e6e8e08893f5c24a7c586d7e585271bad7e60261d24f10677ec893`.
- Demonstrations are count-independent over 2–6; each episode has four distinct queries, including a substantive 30×30 query with a 29×29 crop touching the lower/right boundary.

## Adversarial findings and repairs

1. The first two-demo selector allowed several color-frequency/rank rules to fit both demonstrations for some seeds. Added eight explicit statistical rivals and changed demo selection to jointly refute every declared/task-relevant shortcut at the two-demo minimum. A reconstructed seed-0 `stat_last_command` ambiguity remains as the regression witness.
2. The first crossed-control helper assumed one fixed construction attempt; seed 3 collapsed. It now searches a bounded shared geometry and separately searches a nuisance control, with regression coverage across 32 seeds.
3. Certificate tampering (duplicate input, forged output, wrong program, bool cell), private/public mutation, fixed-command, wrong-corner, skip-A, wrong-order, and frequency/rank attacks are retained in the task-local adversarial report.

## Evidence and limits

- `workspace/parametric/evidence/adversarial/report.json`: 384 Python jobs over 64 seeds × 2 settings × demo counts 2/3/6, 50 protected-Racket evaluations, 32-seed crossed controls, and verifier/export attacks.
- `workspace/parametric/evidence/manifest.json`: exact source/evidence inventory, SHA-256 `6458f34a435cf85495187a365d9e46507e440447523b9cb702bba9e7a85508c6`.
- Native authoring preflight: `checks/c53c24435976/qualification/qualification.json` (28 parametric labeled pairs, 5 canonical pairs, 40 protected-Racket evaluations).
- Causal witness: `checks/c53c24435976/causal/witness.json`; protected replay confirms that skipping step A changes the final output.
- Public projection: `checks/c53c24435976/preview-verify.json` and `checks/c53c24435976/first-turn/report.json`.

Finite seeds and named shortcut classes do not prove universal learnability or uniqueness. The next action is owner source review followed by unchanged native qualification/acceptance; no owner acceptance or training admission is claimed here.
