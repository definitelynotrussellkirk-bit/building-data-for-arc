# Working notes: fcd2e3748e0e

## 2026-10-25 native parametric review

- Repaired the retained generator contract: removed ignored palette/position
  controls and made `reflect_ctrl`, `rotate_ctrl`, and `template_size` exact.
  Also fixed iterator-consuming shape normalization and retained missing-control
  fixtures only as unadvertised diagnostics.
- Preserved the catalog-selected canonical `reflect_then_rotate` Racket program
  byte-for-byte; added `rotate_then_reflect` as the only new rule setting.
- Historical canonical examples contain color-5 distractor objects after the
  row-major rotation control.  Canonical replay therefore follows the source
  rule's first-match semantics, while the new parametric grammar separately
  enforces one control of each kind and a clean stamp footprint.
- Sequential interpretation: A applies the first controlled transform to the
  normalized asymmetric template; the intermediate is that transformed cell
  set; B applies the remaining transform and stamps it at the color-9 anchor.
- Teaching inputs use reflection code 3 and odd rotations 5/7 so the operations
  provably do not commute.  The sampler supports 2–6 demonstrations and 1–4
  queries, matched deterministic inputs, and a 30×30 query with 22 stamped cells.
- Bounded demo-only audits at seeds 0, 17, and 97 found no tested rival that fit
  demonstrations while changing a private query.  This remains finite evidence.
- Protected authoring preflight, wrong-order causal replay, sequential public
  export, first-turn invariance, and task-local tests all passed.  Evidence is
  under `WORK/checks/fcd2e3748e0e/` and
  `WORK/checks/fcd2e3748e0e-task-tests/`.
- Next action: owner reviews the exact two Racket sources and sampler grammar,
  then runs fresh native qualification/acceptance.  No owner acceptance or
  training admission is claimed here.


## Owner control-contract repair

Explicit integer controls now use the full advertised AXES bounds at every
difficulty; difficulty bands only select ordinary values. The generator version
and unoverridden draw bounds are unchanged to preserve seeded examples. Values
outside AXES and non-integer controls fail closed before geometry generation.
Callable diagnostic textures remain outside the lawful AXES contract and can
fail self_check. Only listed axes are supported; removed palette/count controls
are not restored.

Focused owner regressions cover each scalar endpoint at None/easy/medium/hard,
ordinary seeds 17/43, and invalid values. This is finite evidence, not an
exhaustive Cartesian or historical override-battery claim. The retained old
audit's targeted ignored-control/domain findings are addressed by these source
changes; its other historical findings and original evidence remain retained
for explicit owner disposition, not automatically marked resolved.

Transform controls and template size are exact. Layout requires an isolated
template and an empty in-bounds square covering all transformed stamp bounds.
If no feasible placement is found, generation raises RuntimeError rather than
clipping a template, reducing its size, overwriting a feature, or changing a
requested control. A bounded minimum-grid / maximum-template coupling is tested;
this does not promise every seed and full Cartesian combination.
