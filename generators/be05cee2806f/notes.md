# Working notes: be05cee2806f

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 production repair and native parametric family

- **Observed base defects:** the generator advertised several unused combinatorial axes, silently accepted unknown overrides, weakly checked only the presence of colors 0 and 1, and did not guarantee either side of the canonical zero-component discriminator.
- **Production repair:** the only production axes are now strict `grid_h`/`grid_w` controls over 10–30. Ordinary draws deterministically include every ARC color, at least one zero component touching an original `1`, and at least one isolated zero component. Unknown controls and non-exact integers fail closed. Legacy negative texture names (`no_holes`, `all_holes`, `single_hole`) remain supported as compatibility aliases.
- **Canonical authority:** the exact selected Racket source and rule hash `546de66737cf` remain unchanged; every selected canonical input and both ordinary difficulty draws pass the repaired source checks.
- **Family:** `followup=canonical|activated_neighbors`. Stage A executes canonical absorption. Stage B uses only cells newly changed from `0` to `1` as an activation mask and recolors adjacent original nonzero/non-1 cells to `1`.
- **Causal witness:** substituting original `1` cells for the newly absorbed intermediate activates a different target set and changes the protected-Racket final output.
- **Teaching/export contract:** matched inputs, 2–6 demonstrations, four distinct private queries, stable query prefixes, distributed dense scenes through 30×30, and verified one-query public projections.
- **Bounded evidence:** 18 focused tests; 32 seeds; 8,320 labeled pairs; 320 causal separations; 640 plausible-rival rejections; 40 protected family labels plus 20 protected counterfactual labels; 16 public views and 24 private-field invariance mutations. No findings in that finite scope.
- **Status:** reviewer-ready repaired source plus prototype only. Exact-source owner integration, native qualification/acceptance, variant approval, and any training admission remain pending.
- **Next useful action:** owner-review the generator API change and run fresh native qualification/acceptance on the exact integrated source.
