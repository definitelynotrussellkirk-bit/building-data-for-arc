# Working notes: 78ab57735469

## Intended rule

An `N×N` tile is expanded to a `3N×3N` mosaic of nine tile-sized blocks.
Block rows 0 and 2 reverse the tile's row order; block columns 0 and 2
reverse its column order. The center block is unchanged, edge-center blocks
apply one reflection, and corner blocks apply both (a 180-degree rotation).
The selected canonical Racket rule remains the label authority and is pinned by
`RULE_HASH = "18918c7192ef"`.

## Review lead and reproduced defect

This review used unresolved return `review-15f5f8fd63911ebe:v0001` as a lead.
That audit showed that the previous `asymmetry_force` repaired only tiles that
were symmetric on *both* axes. Tiles symmetric on exactly one axis therefore
made either the horizontal- or vertical-reflection half of the rule invisible;
an easy lesson at seed `20260928`, indices `417..419`, admitted such a rival.
The retained examples are summarized in `counterexamples/one_axis_symmetry.json`.

The baseline battery also found missing rule pinning, degenerate textures in the
ordinary override domain, weak validation, ineffective or silently clamped
controls, no executable semantic contract, and selected-target text that was
behavior-equivalent but not exact-authority text.

## Current decisions

- Ordinary tiles have side `3..5`, contain exactly 3 or 4 colors, and are
  asymmetric on each axis independently. `_force_axis_asymmetry` preserves the
  realized palette, using recoloring, a count-preserving swap, then a lawful
  constructive fallback.
- The public exact axes are only `side` and `palette_size`. Historical texture,
  noise, anchor and ambiguity switches were removed from the advertised domain;
  unknown or invalid overrides fail loudly. `observe_overrides` reports both
  retained axes exactly.
- Internal textures remain diverse but are implementation details. Every
  requested palette color is realized before asymmetry repair.
- The period-4 production schedule alternates canonical-sized and expanded
  tiles: phases 0 and 2 use side 3; phases 1 and 3 use side 4 or 5. This repaired
  an intermediate 12/60 (20%) profile-floor failure while ensuring every set of
  three demonstrations drawn from a four-example window contains at least one
  expanded tile.
- Declared rivals are `ignore_horizontal_flips`, `ignore_vertical_flips`, and
  the canonical-fitting `fixed_3x3` shortcut. The lesson hook rejects any rival
  that fits all demonstrations but changes the query.
- `strict_canonical_like` distinguishes exact canonical scale from the wider
  lawful training domain. `self_check` validates structure, color types/range,
  palette size, and visibility of each reflection axis.
- The selected base target's `target_code` was synchronized byte-for-byte to the
  canonical `program_solution`; archival `raw_code` was retained. This was a
  text synchronization only: canonical Racket behavior did not change.

## Evidence

Final generator SHA-256:
`7e22ad5afd49ca58f2c02cef3e531b55970da1444302467c8f07da99fa485342`.
The final battery is 12/12 green in
`checks/after-final/checks/78ab57735469_after_battery_summary.json`. The profile
floor has 30/60 exact canonical-profile hits (easy 12/20, medium 9/20, hard
9/20). Task-local tests pass 30/30 in `checks/task-tests-final-v2/`.

The Racket-labelled lesson census materialized 300/300 production lessons,
checked 1,200 query rotations, and found no ambiguity against the three declared
rivals (`checks/lesson-census-final.json`). The source-bound reusable probe in
`workspace/probe_schedule.py` additionally checked all query positions for 48
consecutive-start lessons (192 rotations, 576 rival checks) and found no
violations (`checks/schedule-probe-final.json`).

`counterexamples/fixed_3x3_shortcut.json` records an emitted 4×4 witness on
which the intended output is 12×12 but the canonical-fitting crop shortcut is
9×9. Its authority output is retained in
`checks/78ab57735469/shortcut_racket.json`.

## Known limits and open findings

The finite rival set does not prove universal rule identifiability. The reusable
schedule probe labels generated examples with the independent Python mirror;
the battery and large census provide the Racket-labelled checks. The exposed
post-repair solve passed all 3 visible examples, but masked-query correctness is
unknown. Training approval remains a maintainer decision; these checks do not
set catalog approval.
## Current reviewer considerations

Source SHA-256: `7e22ad5afd49ca58f2c02cef3e531b55970da1444302467c8f07da99fa485342`.

# Decisions for `78ab57735469`

Final generator SHA-256:
`7e22ad5afd49ca58f2c02cef3e531b55970da1444302467c8f07da99fa485342`.
The canonical rule hash is `18918c7192ef`.

## D1 — Require asymmetry on each reflection axis

**Prior choice.** Version 1.3.0 used an `asymmetry_force` repair only when a
tile was simultaneously left/right- and up/down-symmetric.

**Why it failed.** The unresolved audit `review-15f5f8fd63911ebe:v0001`
measured one-axis-symmetric ordinary draws in all bands and retained an easy
lesson where `ignore_horizontal_flips` fit every demonstration but changed the
query. The problem is semantic, not merely cosmetic: one invisible reflection
cannot be learned from that lesson.

**New choice.** Every ordinary tile must satisfy both
`not _is_lr_sym(grid)` and `not _is_ud_sym(grid)`. The repair first searches for
a one-cell recoloring that does not delete the last occurrence of a palette
color, then a count-preserving swap, then a deterministic lawful fallback.

**Rejected alternative.** Keeping an optional `asymmetry_force` switch would
leave ambiguity in the ordinary domain and make a typo or disabled switch a
training defect. Symmetric cases are not useful positive examples for this
rule, so the switch was retired rather than documented as a normal axis.

**Evidence.** `counterexamples/one_axis_symmetry.json`,
`tests/test_generator.py::test_audit_one_axis_symmetric_counterexample_is_rejected`,
and the final semantic reports.

## D2 — Reduce the advertised exact-control surface

**Prior choice.** The generator advertised side, palette, multiple textures,
background density, noise, anchor, color-distribution and asymmetry controls.
Several were degenerate, inert, overlapping aliases, silently clamped or absent
from provenance.

**New choice.** The exact public axes are only:

- `side`, integer 3–5;
- `palette_size`, integer 3–4.

Unknown keys, wrong types and out-of-range values raise `ValueError`. The
`observe_overrides` hook reports the realized values. Internal texture choice
remains varied but is not claimed as an exact user control.

**Rejected alternative.** Declaring a large incompatibility matrix would retain
features that did not improve rule learning. Removing unsupported controls is
smaller, more falsifiable and easier for future reviewers to probe.

**Evidence.** Baseline override and defect-lint logs under `checks/before/`;
final green override report under `checks/after-final/`; focused override tests.

## D3 — Preserve exact palette semantics

**Choice.** A requested palette of 3 or 4 distinct colors must actually appear
in the returned tile. `_ensure_palette_used` introduces missing colors only at
cells whose old color has another occurrence. Axis repair then preserves the
realized palette exactly.

**Failure mode considered.** A naive recoloring can remove a singleton color and
make `palette_size=4` observe as 3. The count-aware repair and exact observation
test prevent this.

## D4 — Alternate canonical and expanded sizes in a period-4 schedule

**Initial repair choice.** Phase 0 used side 3; phases 1–3 used side 4/5. This
made every three-demo rotation include an expanded witness but produced only
12/60 (20%) exact canonical profiles in the pinned gate, below its 25% floor.

**Final choice.** Phases 0 and 2 use side 3; phases 1 and 3 use side 4/5. Any
four consecutive examples therefore contain two canonical-size and two
expanded-size tiles. Holding out any one query leaves at least one expanded
demonstration, so the fixed-3×3 rival is still refuted.

**Rejected alternatives.** A one-in-four anchor was empirically too sparse. A
three-in-four canonical schedule would permit a rotation whose three
demonstrations are all 3×3. Random size choice would not give a deterministic
lesson-level guarantee.

**Evidence.** Intermediate failure
`checks/after/checks/78ab57735469_after_profile_floor.log`; failing regression
`checks/task-tests-profile-red-valid.log`; final 30/60 profile report and
rotation census.

## D5 — Declare executable rivals and witnesses

**Choice.** The semantic contract names:

- `ignore_horizontal_flips`;
- `ignore_vertical_flips`;
- `fixed_3x3`.

The corresponding witnesses are horizontal asymmetry, vertical asymmetry and a
non-3×3 side. `lesson_identifiable` checks the live competitor mapping rather
than relying on prose.

**Why these rivals.** The first two reproduce the retained audit's exact failure
mode. `fixed_3x3` is the strongest plausible canonical-fitting shortcut because
all four canonical inputs are 3×3; it matches all 4 labelled canonical pairs.

**Known limit.** Passing this finite set is not proof against undeclared rules.
That limitation is stated in every report.

## D6 — Use strict structural validation

**Choice.** `self_check` rejects empty/ragged/non-square grids, sides outside
3–5, non-integer or out-of-range colors, palettes outside 3–4, and symmetry on
either axis. Boolean cells are rejected despite Python's `bool` subclassing
`int`. `strict_canonical_like` adds side=3 without narrowing the lawful training
domain.

**Rejected alternative.** A permissive validator that merely checks shape would
allow the same ambiguity to re-enter through overrides or manually supplied
examples.

## D7 — Synchronize active authority text without changing behavior

**Choice.** The selected base target's `racket_target.target_code` was copied
exactly from the canonical `program_solution`; archival `raw_code` was retained
and a status marker records the synchronization.

**Reason.** Baseline authority sync reported exact-text divergence while
execution parity passed. Synchronizing the selected text removes a maintenance
hazard without editing canonical data or changing labels.

## D8 — Add a reusable declared-rival schedule probe

**Choice.** `workspace/probe_schedule.py` loads the current generator,
iterates its actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, checks every
query position across consecutive starts, and reports source hashes and exact
counts. A source-bound smoke test was written before the tool implementation.

**Scope.** The probe's generated labels use `rule_mirror`; it is a cheap authoring
and regression tool. Racket-labelled battery/census evidence remains decisive.

## D9 — Preserve failures and bounded claims

The baseline failure, the interrupted/resumed attempt, the first after battery,
the 12/60 profile regression, and the missing-tool test are retained. The final
reports distinguish generated-label mirror checks from Racket-labelled checks,
finite rival coverage from universal identifiability, and visible-example solve
success from hidden-query correctness.

The repository-wide suite's single `defba1ab4f90` historical-identity failure is
also retained. It reproduces in an untouched extraction with identical unrelated
test and generator hashes, so I did not alter out-of-scope source merely to make
the aggregate suite green.

## D10 — Leave audit targets untouched

`bf8910eef99b` and `66b8f050cbf2` were read and exercised only. Their source
hashes match `AUDIT_ASSIGNMENT.json`; no audit repair is included in this delta.

## D11 — Prototype independent row/column flip phases without changing production

**Priority addressed.** The canonical generator already had a strong ordinary
lesson contract, but no rule-level parameter prototype for the supplied original
family. This review leaves `generator.py` and canonical data byte-identical and
adds a task-local prototype under `workspace/parametric/`.

**Choice.** Add two episode-fixed binary parameters:

- `row_flip_phase`: vertically flip even or odd 3×3 block rows;
- `column_flip_phase`: horizontally flip even or odd 3×3 block columns.

The original `(even, even)` setting returns the exact canonical Racket program
and normalized rule hash `18918c7192ef`. The other three settings preserve the
same 3×3 mosaic/composition reasoning pattern while moving only the two parity
phases. Inputs are sampled through the production generator, but the prototype
rejects tiles whose four orientation outputs collapse; in particular, a tile
with a 180-degree symmetry can make `(even, even)` and `(odd, odd)` identical.
Each retained episode fixes one setting, has three demonstrations and four
distinct query inputs, and keeps private settings/programs/answers out of the
public projection and its content ID.

**Evidence.** `tests/test_parametric_prototype.py` has 39 passing focused tests.
`workspace/parametric/verify.py` executed exact Racket for all four settings and
retained 28 intended labels, 84 rival pair checks, and 48 demonstration-only
query/rival checks in
`checks/parametric/78ab57735469-parity-phase-final2-report.json`. All intended labels
matched, every other parity setting was refuted by the demonstrations and changed
every query, the four canonical pairs matched under the exact default program,
and all four opaque public challenges were masked, sorted, and uniquely identified
from their visible bytes.

**Limit and next action.** This is a proposed task-local authoring prototype, not
a production rule change, approval, or training admission. Evidence covers one
retained episode per setting and exactly the other three parity settings as
rivals. Before promotion, a maintainer should decide whether the phase parameters
are pedagogically valuable and, if so, run a broader seed/support census with the
same four-output-distinct filter rather than weakening it.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/78ab57735469/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## D12 — Supersede the parity-only draft with a native sequential family (2026-10-25)

The earlier D11 parity-only prototype is superseded by the current
`workspace/parametric/` contract.  It preserves the four row/column phase
combinations and adds `finish=tile_only|erase_center_component`, for eight
settings total.  The exact `(even, even, tile_only)` default remains the
canonical Racket source.  The sequential finish first builds the phase-specific
3N×3N mosaic, then erases the complete 4-connected component containing seam
coordinate `(N,N)`.  Inputs are matched across settings and include a separated
copy of the target color so “erase every target color” is observably wrong.

Three demonstrations refute the seven alternate settings and three named
shortcuts.  Four fresh queries use source sides 4, 7, 8, and 10; the last is a
substantive 30×30 output.  A 128-seed sampler stress and a protected-Racket
bounded audit found no construction, teaching, label, or public-projection
failures.  The causal witness flips A’s row phase while leaving B unchanged and
replays both a 12×12 and 30×30 disagreement.  The obsolete parity-only
`verify.py` was replaced with a protected-Racket verifier for the current
three-parameter contract; a regression test executes that verifier against a
sequential setting.  Next owner action: review and integrate the exact source,
then run fresh native qualification/acceptance; training admission remains a
separate decision.
