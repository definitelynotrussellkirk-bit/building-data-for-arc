# af0ae766e671 — current generator contract

Version **3.0.0**, canonical rule **c5ef698a2a19**. Split the input into equal
upper and lower panels. The output has one panel's dimensions; a cell is 6
exactly when one aligned input cell is zero and the other is nonzero, otherwise
0. Racket remains the label authority. The canonical program and ledger are
unchanged; the selected base solution's active `target_code` now agrees with
that program. Its archival `raw_code` is preserved.

## Ordinary input domain

Input height is even in 2..30, width is 1..30, and each panel has at least four
cells. Each panel uses zero and one foreground color in 1..9; the foregrounds
differ. All four aligned occupancy states 00, 01, 10 and 11 occur. All seven
usable canonical pairs meet this contract. Foreground 6 is legal: output 6 is
a fixed result color, not a color-role inference.

`half_h`, `grid_w`, `top_color` and `bot_color` are exact, observed controls.
Difficulty weights defaults without narrowing their legal override ranges.
`None` means an omitted override. Seeds and sample indices must be nonnegative
integers; seed identities have no imposed uint32 bound. Unknown axes, wrong
scalar types, nonfinite densities and infeasible joint requests raise
`ValueError`; incompatible requests name the participating axes.

`top_density`, `bot_density`, `panel_pattern` and its `texture` alias guide
proposals. They are explicitly non-exact because coverage repairs can change
the realized density or pattern. `xor_target` is a lower bound: ordinary draws
contain at least `max(2, xor_target)` XOR cells. Its feasible range is
1..`half_h*grid_w-2`, retaining one cell of each agreement state. If a dimension
is unpinned, the sampler can choose a feasible shape; a fully incompatible
request fails. The three named negative diagnostic textures are retained for
validator tests and excluded from the ordinary advertised domain.

## Lessons and distribution

The intended export has three consecutive demonstrations and one query. A
four-phase schedule alternates `(core, canonical palette)`, `(core, varied)`,
`(broad, canonical)`, `(broad, varied)`. Core means a 6×5 input; broad excludes
that shape. Canonical colors are upper 9/lower 4; varied upper colors exclude 9.
Broad draws retain the full legal shape support with difficulty weights.
Explicit pins take precedence and need separate lesson checks.

Every three-phase window, including any three of a four-pair episode, contains
a noncanonical shape and a varied palette. All four occupancy states refute
the 15 alternative pointwise Boolean tables; shape and palette examples refute
the two declared canonical shortcuts. The executable contract declares these
17 competitors. This supports the stated production and query-rotation policy,
not arbitrary nonconsecutive sampling or uniqueness against every program.

## Reversed choices and evidence

The 2.1.0 repair helpers could leave all-filled proposals unchanged, underfill
`xor_target`, or copy the lower foreground into the upper panel. Structured
patterns also repeatedly omitted a truth-table branch. Version 3.0.0 constructs
occupancy states first, repairs random surplus positions, then colors each
panel using its own foreground. It removes the fixed-corner repair shortcut.
Minimal baseline witnesses are in `counterexamples/baseline_contract_failures.json`;
tests are in `tests/`. Full provenance and failed iterations are retained in the
return's `checks/` and `DECISIONS.md`.

An intermediate repair incorrectly imposed a uint32 seed limit; native
48-bit sampler failures required removing it. Another intermediate fix orders
density bounds before `math.isfinite`, so huge invalid integers raise the
documented `ValueError`. Neither failure is hidden by the final checks.

The reusable `workspace/probe_occupancy.py` measures input branch coverage,
validator results and uniqueness, with a full first counterexample per group.
Use the public Racket apply and lesson-census commands for labels and lesson
claims. Remaining limits: repairs can dominate tiny grids or extreme density
proposals; periodic semantic profiles are intentional; finite rival evidence
does not establish universal identifiability or training approval. No unresolved
task-local defect is currently known. Original design rationale beyond the
baseline source and placeholder notes is unknown.

## Parametric authoring extension (proposed)

`workspace/parametric/prototype.py` keeps the same two-panel alignment and
zero/nonzero occupancy reasoning while varying two episode-level rule choices:
`operation` is `xor`, `and`, or `or`; `output_color` is an integer in 1..9.
The canonical/default setting is `xor` with output color 6. All 27 combinations
are proposed research variants, separate from the selected fixed-rule execution
path and its approval. Parameters are chosen once for a complete three-demo,
one-query episode. The input domain does not change with the setting.

Every ordinary input includes 00, 01, 10, and 11 occupancy states. Those cells
separate the three declared operations and expose the nonzero output color in
each demonstration. This is identifiability within the declared parameter
family, not a proof against all possible programs. Outputs and parameter-rival
checks use the actual Racket bridge. Public challenges contain demonstrations
and query inputs only; authoring evidence retains parameters, exact programs,
query labels, seeds, and hashes separately. See the prototype README for commands
and tests/test_parametric_extension.py for executable checks.

The canonical generator is still version 3.0.0 with SHA-256
`ca35dac54282e7e95b6588a43c28b42cbdc21a2ceaa25e23c6c271cc8eb7368d`.
The selected Racket rule is unchanged. The previous accepted source decision is
`review-81dda37af2c069ca:v0001`; its counts are historical, not measurements from
this review. The new return retains fresh canonical checks and variant evidence.

Current default palette support is intentionally narrower than exact overrides:
canonical phases use 9/4, and varied phases exclude upper color 9, so unpinned
sampling covers 65 of 72 lawful ordered distinct foreground pairs. All 72 remain
available through exact controls. This round preserves that documented sampling
policy and deterministic seed mapping; it does not claim full unpinned palette
coverage. Area-four or extreme-density inputs can still be dominated by coverage
repair. No new canonical defect or unresolved audit was found in the bounded
review; evidence limitations remain explicit in the return.

## Native parametric handoff — review-1e27b399ba9aad55 (2026-10-25)

Added the task-local `selection={xor,sparser_panel_only}` family. The default is
the exact selected canonical XOR program. The alternative first derives upper
and lower occupancy totals, selects the uniquely sparser panel, and then paints
only exclusive cells owned by that panel. Inputs are setting-neutral; requests
support 2–6 demos and 1–4 queries with stable prefixes and four distinct
controller-side queries. The audited 30×30 case has 539 nonzero input cells and
the settings disagree on 140 output cells.

The prior 27-setting exploratory prototype remains in `legacy_27_settings.py`.
A compatibility regression exposed recursion when its audit monkeypatched
`make_episode`; `_audit` now drives the compatibility surface directly while
preserving public/private JSONL row indices. Fresh evidence: 239/239 staged task
tests; 59/59 focused old-plus-new tests; 42 protected-Racket self-audit
executions; four qualification jobs with 32 protected labels; 16/16 sequential
public projections; and an 8-cell causal counterfactual. The final deterministic
sweep covered 67 seeds through `2^63-1`, 268 episodes and 2,680 typed grids for
this target. Exact paths: `workspace/parametric/evidence/manifest.json`,
`checks/af0ae766e671/qualification/qualification.json`, and
`checks/af0ae766e671/causal/witness.json`.

Limit: finite declared rivals and seeds do not prove universal identifiability.
Owner exact-source acceptance and training admission remain pending.
