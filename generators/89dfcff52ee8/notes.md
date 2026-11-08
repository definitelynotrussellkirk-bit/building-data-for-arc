# Working notes: `89dfcff52ee8`

## Current decisions

- Preserve the selected canonical Racket program byte-for-byte as the default
  setting, `closure=rows_only`.
- Repair the base generator's canonical-domain hole: singleton active rows are
  valid one-cell intervals, are accepted by `self_check`, and are deliberately
  sampled by `texture=singleton_mix`.
- Replace the legacy inert/misleading control surface with four strict observable
  controls: `grid_h`, `grid_w`, `active_rows`, and `texture`.
- Use one nearby episode-fixed alternative, `rows_then_columns`: A computes the
  input-dependent horizontal row closure; B vertically closes the occupied
  columns of that intermediate.
- Support 2–6 independent demonstrations and exactly four distinct private
  queries. Inputs are matched across settings and the 30×30 query is substantive.

## Findings and repairs

1. The retained base rejected a canonical singleton row and ordinary draws did
   not teach that branch. The rewritten base now accepts and samples it; canonical
   pairs and a Python mirror agree.
2. The first alternate sampler reused marker columns too broadly, allowing
   column-first/parallel shortcuts to collapse toward the intended composition.
   The sampler was repaired to use mostly unique span endpoints plus one controlled
   shared interior probe column. Two demonstrations now refute both declared-rule
   alternatives and eight finite shortcut families across the exercised seeds.
3. Saved certificates are not trusted. `certify` recomputes labels, setting
   survivors, distinct-input checks, and shortcut disagreements; malformed counts,
   duplicate inputs, bool cells, forged settings/programs, and wrong labels fail.
4. Public projection exposes all demos plus exactly one query input. Settings,
   program, certificate, answers, future queries, order hints, and total-count
   hints remain controller-side.

## Verification and limits

- 15 focused tests and the source-bound task-test run passed.
- The reusable adversarial probe covered 128 episodes over 32 seeds, both settings,
  and the 2/6-demo boundaries; it performed 74 protected-Racket evaluations.
- Authoring preflight passed 3 canonical pairs and 24 parametric labels with 32
  protected-Racket evaluations. The causal witness replayed two counterfactuals
  (`skip_a` and `wrong_order`) that change the final output.
- First-turn/export reports passed for 16 single-query views.
- These are finite reviewer checks, not universal uniqueness. The next action is
  owner review of the exact patch, native qualification/acceptance replay, and a
  separate decision on training admission.
