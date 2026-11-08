# Working notes: c7f337af82e5

## Version 3.0.0 review

The selected 2.1.0 baseline already fixed overlapping-object placement. This
review found ignored control/texture overrides, no canonical-profile support in
the hard-band check, and a stronger semantic defect: every supported frame had
a larger exposed perimeter than every supported solid. A perimeter-ranking
rule therefore fit the entire ordinary default support and all canonical pairs.
The retained return contains baseline measurements and exact Racket witnesses.

The canonical Racket text and behavior are unchanged. The selected base
`racket_target.target_code` is synchronized to that text by removing only
comments; its raw archival code already matched the canonical authority.

## Distribution and exact controls

`grid_h=8..16`, `grid_w=9..18`, `control=1..2`, and `n_objects=2..4` are jointly
supported in every band. Values must be integers; `None` means no override.
Unknown controls fail explicitly. The old palette/texture/density/count aliases
were inert or fixed facts, so they are no longer advertised or silently accepted.
Palette roles remain fixed by this task's authority: 0, 1/2, 7, and output 8.
Changing only an explicit control value changes only the control pixel.

Constructive placement uses four rectangular slots separated by an empty row
and column. Feasible slot assignments are enumerated before sampling; there is
no capped layout retry or silently dropped object. Contrast cuts reserve enough
space for a 3×5 solid even on an 8×9 canvas. Shapes may touch outer borders while
remaining separate. Small rectangles include the canonical 2×2 solid, and
additional objects allow multiple selected and unselected components.

## Teaching policy

The ten-position schedule is `C1,C2,C1,C2,B1,C1,C2,C1,C2,B2`, with a seed-dependent
phase. `C` is a geometric contrast; `B` samples broader shapes. Every five
consecutive positions include two contrasts per control. A contrast contains a
3×3 frame and a 3×5/5×3 solid, with the frame to the right and not above the solid.
Their exposed perimeters tie at 16, while areas are 8 and 15. The same scene
defeats size, perimeter, position, bounding-box, threshold, and square-area rivals.

An intermediate production census exposed duplicate rejection despite a clean
direct-window probe. Nearby same-control contrasts now alternate canonical and
noncanonical canvas sizes; the two canonical sizes (8×9 and 11×10) swap between
controls in the second half-cycle. Broad scenes exclude 15-pixel solids, making
their support disjoint from contrasts. Thus the five default consecutive inputs
are distinct, and production deduplication cannot remove a teaching contrast.
The exact failed lesson is retained in the return.

The semantic contract declares canonical-fitting rivals, their versions that
apply under only one control, and ordinary control-ignoring lesson competitors.
Geometric witnesses are checked against authoritative Racket labels. Predicates
and rivals never supply training labels. The optional probe uses an independent
Python interpretation and explicitly reports that weaker evidence basis.

## Limits

The declared domain remains separate, exact rectangular frames and filled
rectangles. Open frames, irregular components, nesting, and arbitrary palettes
are not supported teaching extensions. The Racket interior-zero predicate can
act on broader shapes, but that does not establish canonical intent for them.
Four-slot construction and frequent 3×3 contrast frames remain sampling biases.
Finite rival tests do not establish unique induction against every possible rule.
The lesson guarantee concerns default sampling with four demonstrations and one
query; arbitrary overrides or different lesson assembly need their own checks.

See `tests/test_generator_contract.py` and `workspace/probe_distribution.py` for
portable regression and distribution diagnostics. Full source-bound evidence,
including failures and command logs, travels in this assignment's return ZIP.
## Current reviewer considerations

Source SHA-256: `435e528f6ba99da6d8f887c71f5c23e187ae20ec3e059240a9e20511fba45f01`.

# Decisions — c7f337af82e5

All final-source statements refer to generator SHA-256 `435e528f6ba99da6d8f887c71f5c23e187ae20ec3e059240a9e20511fba45f01`, version 3.0.0, and canonical rule `4441279127ff`. The baseline was `267155e043939b3339d3ab18844571b72a34396e620e5529af109040d2901866`. The retained associated notes are empty, so original author intent is unknown where the code does not explain it.

## D1 / M1: preserve the rectangle domain and the Racket rule

**Observed behavior.** The control at (0,0) is cleared; control 1 selects hollow orange rectangular frames, and control 2 selects filled orange rectangles. All other cells remain as they were. The canonical Racket rule detects an interior zero inside each object's bounding box. Canonical examples show exact, separated frames and filled rectangles.

**Choice.** Generate only exact frames and filled rectangles, with both kinds in every scene. Keep fixed color roles 0, 1/2, 7 and output 8. Implement a strict-domain validator and executable geometric witnesses.

**Alternative considered.** Open/gapped frames or irregular connected shapes can trigger the broader Racket predicate. A retained handmade open-frame case confirms that boundary, but canonical support does not establish that those shapes are the intended teaching manifold. They remain diagnostics instead of unrequested training-domain expansion.

**Evidence and limits.** [Baseline analysis](checks/semantic-review/baseline_report.json), [Racket witnesses](checks/semantic-review/racket_witnesses.json), and [oracle parity](checks/semantic-review/oracle_check.json). The independent Python probe is appropriate only on the declared rectangle domain; it deliberately rejects broader shapes.

## D2 / M2: keep four meaningful exact axes

**Observed defect.** The baseline advertised control and shape/palette-style knobs that were ignored, internally fixed, or incompatible with the canonical palette. Its override stage failed repeatedly. The original rationale for advertising them is not recorded.

**Choice.** Support exact integer `grid_h=8..16`, `grid_w=9..18`, `control=1..2`, and `n_objects=2..4` jointly in every band. `None` means no override; unknown axes, booleans, nonintegers and out-of-range values fail clearly. Explicitly changing only the control changes only the corner pixel, so intervention on this answer-bearing role is observable.

**Alternative rejected.** Silently clamping dimensions, adjusting object counts, randomizing a requested control, or retaining inert metadata would make the exact-control contract misleading. A broad palette knob would require an authority change. Removing inert aliases is an intentional version-3 API change; callers must use the documented four controls.

**Evidence.** The [baseline override report](checks/before/checks/c7f337af82e5_before_override_results.json), [final override report](checks/after-final/checks/c7f337af82e5_after_override_results.json.gz), and the control/joint-boundary/malformed-input tests in the [37-test suite](repo/generators/c7f337af82e5/tests/test_generator_contract.py).

## D3 / M2: constructive placement instead of capped retries

**Observed restriction.** The 768 baseline diagnostic draws (seeds 0–255, index 0, 256 per band) all contained two objects, no border-touching component, and no 2×2 solid. The baseline's permitted solid bounds did not reverse the frame/solid size hierarchy.

**Choice.** Construct four rectangular slots separated by an empty row and column, enumerate feasible slot assignments, and place the requested 2–4 objects. A complete assignment is selected before drawing shapes. The primary contrast needs a 3×5 or 5×3 solid; contrast cuts reserve row 4 and column 5 as the minimum feasible split so an 8×9 canvas still works without overwriting the corner control. Ordinary solids include 1×1, 1×2, 2×1, 2×2, 2×3 and 3×2; broad slots permit larger rectangles. Outer borders are allowed.

**Alternatives rejected.** A capped retry with fewer returned objects violates exact counts. Reusing naive minimum cuts failed during implementation because a 3×5 solid could not fit or touched the control reservation. Limiting every scene to two objects would retain a canonical-count restriction. Tests caught and corrected the actual feasibility failure; [regression-after-v3.log](checks/regression-after-v3.log) is preserved.

**Remaining bias.** Slot separation excludes nesting and touching components and favors a small family of spatial arrangements. This is a deliberate constructive subset of the declared domain, not full support over all legal placements.

## D4 / M1: choose a contrast that defeats perimeter and area proxies together

**Strongest baseline rival.** Select objects by exposed edge perimeter: for control 1 paint those above the minimum; for control 2 paint those at the minimum. All three canonical labels fit. The baseline's single frame always has perimeter 16, 20 or 24, while its single solid has perimeter 10 or 12. This gives a source-level argument that the rival matches ordinary default support; 768/768 Python-oracle draws agree. It is stronger than area/bounding-box rank rivals, which occasional equal-area baseline scenes already refute.

**Choice.** Use a 3×3 frame (8 orange pixels, perimeter 16) with a 3×5 or 5×3 filled rectangle (15 pixels, perimeter 16). Place the frame to the right and not above the primary solid. The tied perimeter refutes the perimeter rival; the larger, nonsquare solid refutes area, bounding-box, dimension-threshold and square-pixel-count proxies. The relative position also refutes the canonical-fitting rightmost/lowest exclusions.

**Rejected intermediates.** A 3×4 solid has exposed perimeter 14, so the frame still has the larger perimeter; [perimeter-before.log](checks/perimeter-before.log) records the regression. A 4×4 solid ties perimeter 16 but has square area 16, leaving a different plausible shortcut. A 3×5 solid addresses both. With additional objects, simply reversing position for two-object scenes was insufficient; the positional constraint now applies at every advertised count.

**Small default witness.** Easy seed 0, indices 2 and 28 produce the same 8×9 geometry under controls 1 and 2. Both pass the validator. Public Racket and the rival differ on eight frame cells in each case. Full grids and the supported public-apply receipt are in [shortcut-witness](checks/shortcut-witness/counterexample.json).

## D5 / M3: teach both control branches within every supported lesson

**Observed failure mode.** Globally refuting a rival once does not make each demonstration set informative. A rival may behave correctly under control 2 and apply its shortcut only under control 1, or vice versa. An early four-position schedule supplied insufficient repeated branch contrasts under query rotation; [branch-schedule-before.log](checks/branch-schedule-before.log) records the failed test.

**Choice.** Use the ten-phase schedule `C1,C2,C1,C2,B1,C1,C2,C1,C2,B2`, shifted by a seed-derived phase. C is the strong geometric contrast and B is a broader scene. Every consecutive five positions contain two C1 examples, two C2 examples, and one broad example. Holding out any one pair therefore leaves a contrast under both controls among four demonstrations.

The contract declares 32 canonical-fitting shortcuts, including applicable versions restricted to one control. It adds two control-ignoring competitors, for 34 distinct lesson rivals. A control-1-only border-painting variant is omitted because it is answer-equivalent on exact frames. Witnesses are input geometry predicates; `WITNESS_RIVALS` connects them to actual rival functions. Each canonical shortcut has a mapped refutation. The first after-battery correctly warned when mappings were incomplete; [the failed semantic stage](checks/after/result.json) is retained.

**Scope.** `EXAMPLES_NEEDED=4`. The guarantee concerns one held-out query in a default five-pair window. Forcing a fixed control or canvas size with overrides, using fewer demonstrations, or changing assembly requires new identifiability checks.

## D6 / M3: preserve that curriculum through actual duplicate rejection

**Reproduced intermediate defect.** An initial direct Python probe found no ambiguous windows. The authoritative production census nevertheless found 1 ambiguous rotation out of 1,500. Easy census index 7, seed 1115388330, requested start 7 accepted sample indices `[7,8,9,11,12]`; index 10 was rejected as a duplicate. Holding out pair 1 left a control-1-only size rival consistent with the demonstrations but wrong on the query. See [exact lesson](checks/rotation-counterexample.json) and [initial census](checks/lesson-census.json.gz).

**Choice.** Nearby same-control contrast scenes alternate canonical canvas sizes and sizes excluding both canonical anchors. The two canonical sizes, 8×9 and 11×10, swap between controls in the second five-phase block, preserving both profiles under each control. Every contrast contains a 15-pixel solid; broad primary solids exclude area 15 and small extras cannot have area 15. Thus broad and contrast supports are disjoint.

**Why this is sufficient for default deduplication.** In a five-position window, contrasts with different controls have different corner pixels. The two same-control contrasts use disjoint canvas-size classes. The broad scene has no 15-pixel solid and therefore cannot duplicate a contrast. All five inputs are distinct, so the production materializer cannot drop one as a repeated pair.

**Evidence and rejected shortcut fix.** The exact production regression was red before this change and passes now. The final production census reports zero rejected draws, zero ambiguous production queries and zero ambiguous rotations. Merely increasing a retry limit or accepting duplicate demonstrations would hide the semantic failure instead of maintaining the intended lesson.

## D7 / M4: synchronize authority text without changing semantics

The selected base file's `racket_target.target_code` contained comments absent from the canonical authority; its archival `raw_code` already matched. Remove only those comments. The canonical ledger's SHA-256 stays `55a6b98c4865097fd325615b807ffff4f27edd28ab9cb7827d57b7625083d7e0`; normalized rule hash stays `4441279127ff`. The [authority receipt](checks/after-final/checks/c7f337af82e5_after_authority_sync.json) reports exact synchronization and execution parity. No canonical output or executable expression changed.

## D8: retain the tools and keep evidence levels distinct

The [portable probe](repo/generators/c7f337af82e5/workspace/probe_distribution.py) reads the live declarations, validates every claimed canonical shortcut, enumerates consecutive starts and holdouts, and saves source hashes and first counterexamples. Its oracle is an independent flood-fill and explicit rectangle check. It resolves canonical helpers from its own source ancestry and works from a different cwd without a preset import path.

Public Racket-labelled production evidence remains the separate census. Finite Python probes, Racket smoke checks, accepted production lessons, overlapping windows, and unique input counts are reported separately. The final 16-seed/40-start probe is bound to the final source; the two smaller probes are explicitly intermediate.

The offline [environment bootstrap](checks/environment/bootstrap_offline_venv.py) solves this environment's nested pytest availability issue without disabling user-site isolation. It installs only already-available pytest distribution files and metadata into a local virtual environment. The [compression tool](checks/compress_evidence.py) preserves exact report bytes with path/size/hash mappings and reversible restoration. These helper scripts are evidence/workflow tools, not shared-source patches.

## D9: preserve failures and refrain from unsupported approval claims

Every genuine regression failure and census counterexample is retained, including the implementation syntax error and the test's initial incorrect raw-vs-normalized rule-hash assertion. The visible solves each had one genuine successful visible attempt; deliberately wrong solves were not manufactured. Masked query labels remained closed, the post-repair episode declares prior exposure, and training admission remains false.

[RESULTS.json](RESULTS.json), the final intake generated by the supplied builder, and the fresh-replay evidence identify exactly which source and patch passed. Passing these finite checks is a review result, not a universal proof of induction or permission to admit training data.

## D10 / 2026-10-24 separate parametric control-mapping proposal

**Decision.** Keep the exact canonical mapping (`control 1 → hollow frame`,
`control 2 → solid rectangle`) as `mapping=standard`; add
`mapping=reversed`. Every scene contains separated exact hollow and solid orange
rectangles, so the mapping changes the executed transformation while retaining
control reading, connected-object extraction, bounding-box/interior analysis, and
recoloring. The minimum two demonstrations use controls 1 and 2 and reject
paint-all, paint-none, always-hollow, and always-solid shortcuts.

**Boundary construction.** The fourth query has five large separated objects on a
30×30 canvas: 348 orange cells total. Standard and reversed settings select 104
or 244 cells respectively, and either selected shape class reaches all four
boundaries. Counts 2–6 preserve the query set and demonstration prefix; four
queries stay controller-private and are exposed one at a time.

**Evidence.** Forty-seven focused task tests pass (ten new plus 37 retained).
Protected Racket executed four all-setting episodes (seeds 0 and 17; 28 labeled
pairs), and the bounded adversarial report re-executed 12 minimum-lesson pairs and
passed control-branch, count, bad-label/query, and export-mutation checks. A final
RED regression showed that equal first-turn public bytes with different private records
reached Python dictionary ordering and raised `TypeError`; the writer now sorts by public
ID only and reaches the intended duplicate-ID `ValueError` before destination creation. See
`workspace/parametric/evidence/manifest.json` and
`workspace/parametric/evidence/adversarial/report.json`. The bounded semantic
pass found no defect; the later export self-review found and fixed the sorting defect above.

**Status/limit.** This is a separate runnable source-bound prototype; it does not
alter or supersede the production curriculum described above. It is not
qualified, accepted, production-parametric, or admitted to training; owner
qualification is the next action. Canonical `generator.py` and canonical rule
authority were not changed.
