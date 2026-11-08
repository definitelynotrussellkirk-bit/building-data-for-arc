# Apply the Transform Script: current design

## Authority and domain

Version 3.0.0 pins the unchanged canonical `RULE_HASH = 04788c0240d6`.
Read the nonzero cells of row 0 from left to right, crop the nonzero body,
and apply each instruction to the preceding result. Code 1 rotates 90 degrees
clockwise; 2 reflects left/right; 3 rotates 180 degrees; 4 reflects up/down.
Return one final crop, preserving the motif color. Zeros are ignored, including
leading padding and internal gaps. Repeated instructions and their order matter.

The sampler's declared domain is narrower than everything the Racket program
can execute: a blank row 1, 1..6 codes from 1..4, and a nonempty, four-connected,
monochrome body of 3..12 cells. In particular, acceptance by Racket alone does
not establish membership in this generator's domain. The validator accepts
3..30 rows and 1..30 columns when the structural requirements fit; the sampler
uses 7..14 rows and 8..16 columns. All four canonical inputs pass validation.

## Controls and distribution

The five exact controls are `grid_h` (7..14), `grid_w` (8..16), `n_codes` (1..6),
`motif_color` (1..9), and `motif_size` (3..12). Every combination is constructively
supported in every difficulty band. `observe_overrides` measures these quantities
from pixels. Non-None controls must be exact integers; unknown names, booleans,
coercions, invalid seed/index types and unknown difficulty values fail explicitly.

The prior version advertised unobservable palette/density/texture/position knobs
and used band-dependent bounds that rejected otherwise advertised values.
The new version removes those knobs and applies difficulty only as sampling
weights. This is an intentional control-interface change, not a compatibility
alias. The reason is executable override evidence, rather than an inferred
intent of the original author; that intent is unknown.

Two thirds of profile choices favor canonical dimensions conditional on the
actual distinct-color count. The full size range remains possible. Five-cell
motifs are favored in that core, with broader shape and size choices outside it.
Motif colors span all 1..9 and can coincide with instruction colors; row position
identifies the role. Random body placement and script gaps avoid fixed-position
assumptions. A bounded connected-growth routine has a finite fallback that
preserves the requested size and fits the smallest canvas. Default teaching
anchors have eight distinct D4 orientations; the free slot also allows symmetry.

## Teaching contract and limits

A seed-stable period-four schedule contains one singleton, two rich composition
scripts, and one free script. Its offset and singleton code remain fixed across
period boundaries. The singleton and rich slots refute each of the three
incorrect canonical-fitting D4 code maps at least twice; both rich slots also refute the declared sequence
shortcuts. Leading blanks in both rich rows distinguish ignoring zero cells
from treating zero as an instruction terminator. Holding out any one of four
consecutive, unrejected, same-seed pairs leaves three demonstrations that refute
all twelve declared rivals.

This is a finite-rival property, not uniqueness among all possible programs.
Its schedule argument assumes ordinary generation, the same difficulty within
the lesson, and no explicit `n_codes` or `motif_size` override. Such overrides
are lawful exact controls but can remove teaching anchors or make them symmetric.
Independently seeded or nonconsecutive assembly needs its own lesson check.
The production sampler and every query rotation were checked separately.

The earlier gallery-style description was reversed because the canonical
program and all four recorded labels implement sequential composition. The
prior labels were already supplied by Racket; this repair does not allege that
those labels were wrong. The old distribution had no executable teaching
contract. Uniform scripts alone were rejected because rare individual witnesses
do not ensure adequate demonstrations in each assembled lesson.

## Reusable evidence and present status

`workspace/analyze_script_maps.py` independently enumerates all 8^4 constant D4
codebooks: four fit all four canonical labels, including three incorrect maps.
It derives the rich-script pools used to choose schedule words. See the workspace
README for commands and limits. `counterexamples/` retains three compact,
source-bound generated cases with exact recipes, Racket outputs and rival outputs;
they are reproducible witnesses, not claims of globally minimal grids.

The final acceptance battery passed all 12 stages. Its source-bound reports in
the associated return's `checks/after-final/` show 600/600 strict samples,
67,140/67,140 valid override draws, 31/60 exact canonical-profile hits and 34/60
envelope hits. The larger census checked 300 three-demonstration lessons and
1,200 query rotations over 1,200 unique inputs with no ambiguity against the
declared rivals. Fixed-seed enumeration checked every period start in every
band. Portable tests cover contracts, the finite teaching argument, fallback
construction, the analysis tool and retained counterexamples. No unresolved
main-task blocker is known; wider hypothesis classes and override-based lesson
assembly remain outside the stated guarantee. No Racket authority changed.
## Current reviewer considerations

Source SHA-256: `0a7333474bb418b62192c1c7a9ee8a8bb92a9480b109811bceb0eac71b5d85fc`.

# Design decisions — 8096ecc43d5a

The selected baseline was version 2.0.1, SHA-256
`83283dea82be611755a90a41fc703807378d4be3d2e0c87a8b55756dec72fdd7`.
The repaired generator is version 3.0.0, SHA-256
`0a7333474bb418b62192c1c7a9ee8a8bb92a9480b109811bceb0eac71b5d85fc`.
The explanations below distinguish an observed prior choice from the original
author's rationale, which was not established. No unintegrated earlier return
was used as a measurement of this baseline.

## D1 / M1: follow the sequential authority and define a real input contract

The original prose described independently transformed copies packed as a
gallery and misstated instruction meanings. The selected Racket program and
all four canonical labels instead compose instructions into one final crop.
I corrected the generator summary, docstring and task SUMMARY.md to that rule,
pinned `RULE_HASH=04788c0240d6`, and kept every authority file unchanged.
The original generator already returned inputs for Racket labeling; this was
not evidence that its saved labels had been computed by the wrong gallery rule.

The old `self_check` accepted destructive mutations without examining their
structure. It now verifies a rectangular integer grid, legal instruction count
and colors, a blank separator, and a connected monochrome body of 3..12 cells.
It rejects bool/float cell values, missing scripts or bodies, disconnected
motifs and mixed motif colors. The validator's outer shape domain is
3..30 by 1..30; generated canvases occupy the narrower range stated below.
The task's canonical inputs all pass.

The alternative of declaring every input executable by Racket to be in-domain
was rejected: execution can also tolerate unknown codes or inputs outside the
documented puzzle structure. Execution validity, validator membership and
generated support are separate statements. Evidence: the before/after
selfcheck and rule-smoke logs in `checks/before/checks/` and
`checks/after-final/checks/`, and `tests/test_contract.py` in the source patch.

## D2 / M2: five observable exact axes, valid across difficulty bands

| Exact control | Accepted integer range | Observable quantity |
| --- | --- | --- |
| `grid_h` | 7..14 | Number of rows |
| `grid_w` | 8..16 | Number of columns |
| `n_codes` | 1..6 | Nonzero cells in row 0 |
| `motif_color` | 1..9 | Common nonzero body color |
| `motif_size` | 3..12 | Nonzero body-cell count |

The previous palette/density/texture/position controls were not honest exact
controls. Their intended purpose is unknown; keeping them as silently ignored
aliases would preserve misleading behavior. I removed them and made unknown
names explicit errors. Non-None values must be exact Python integers; the
generator also validates seed, sample_index and difficulty without coercion.
None continues to mean no explicit override. Negative integer seeds are legal;
sample indices must be nonnegative.

Every advertised combination fits the smallest canvas, so no incompatible
combination is declared. Difficulty changes preference weights, not the set
of legal exact requests. The final override report records **67,140 accepted
draws out of 67,140**, over **746 cases**, with zero findings, warnings or
explicit rejections; the separate unknown-key probe is correctly rejected.
The exact case plan, seeds and axes are retained in
`checks/after-final/checks/8096ecc43d5a_after_override_cases.json` and
`..._after_override_results.json`. This is an intentional public-control
interface change. Existing callers using removed names must update their
requests rather than receive a silently different grid.

## D3 / M3: favor canonical profiles without clipping broad support

The old default distribution produced **0/60** exact canonical-profile hits
and **0/60** canonical-envelope hits. Canonical profiles jointly measure
height, width and distinct-color count, not just legal colors or a large
canvas. The four observed profiles are (8,8,3), (8,9,4), (9,9,4), (9,10,5).

Two thirds of profile choices now select a core preference: favor the relevant
canonical dimensions conditional on the actual palette count. A finite extra
weight retains a nonzero chance of every dimension in the advertised range,
even inside that core. The other profile choice samples broadly. These weights
are a pragmatic measured repair, not an estimated natural-data frequency.
The alternative of narrowing all samples to canonical shapes was rejected
because it would remove useful lawful variation and make larger controls
artificial exceptions.

Core motifs favor five cells, matching the supplied examples; broader draws
cover 3..12. Easy and hard change the weights for size and free-script length.
Motif colors cover all 1..9, including the canonical colors outside 8/9 and
overlap with instruction colors. Position, motif shape and top-row gaps vary.
Fixed color-role separation and fixed placement were rejected because position
already identifies the script/body roles and color should be preserved.

Connected frontier growth is bounded at 128 attempts. Its finite fallback
preserves exact cell count and fits within 4x4, preventing a retry limit from
silently shortening or dropping a requested motif. Forced-fallback tests cover
every asymmetric size 4..12. The free slot can emit symmetric motifs; forcing
all outputs to have eight orientations would introduce an unnecessary support
restriction.

The final 20-draw-per-band profile check measured exact/envelope hits of
**11/20 and 12/20 easy**, **12/20 and 13/20 medium**, and **8/20 and 9/20 hard**:
**31/60 exact**, **34/60 envelope**, no crashes. Those observations exceed the
packet's stated floors without claiming a probability guarantee for arbitrary
finite samples. Exact receipts are the before and after-final profile JSONs.

## D4 / M4: put distinguishing examples inside each intended lesson

The intended production lesson is **three demonstrations followed by one
query**, assembled from consecutive accepted draws with a shared seed and
difficulty. The repair also supports holding out each of those four pairs as
the query, subject to the finite-rival scope below.

`workspace/analyze_script_maps.py` examines all 8^4 constant D4 codebooks.
Four fit all four canonical labels: the intended map and three incorrect maps.
Five additional sequence shortcuts also fit the canonical labels: sorting,
deduplicating, collapsing adjacent duplicates, halting at the first zero,
and applying only the first three codes. The semantic contract adds first-only,
last-only, reversed order and no-script rivals, giving twelve distinct rivals.
The tool's source-bound report is `checks/script-map-analysis-final.json`;
its labels come from recorded canonical data, not a new Racket application.

The period-four schedule contains a singleton S, two rich words A/B, and one
free word F. Its seed-dependent offset and singleton code stay fixed across
all period boundaries. The three anchor slots use asymmetric motifs. Relative
to the three incorrect codebooks, S/A/B carry the three pairwise refutation
masks 011, 101 and 110; therefore every incorrect codebook is contradicted by
two slots. Both rich words also contradict each sequence shortcut and begin
after at least one zero cell. Whichever pair is held out, a refuting anchor
remains among the three demonstrations. The ten retained rich words were
chosen from 320 words independently derived by the tool, rather than selected
by hardcoded output grids.

Uniform independent scripts were rejected because a witness that is common
over the dataset need not appear in a particular lesson. An ordered-only
schedule was also unnecessary: the finite refutation structure supports all
four query positions. A fixed singleton code across every seed was rejected;
the singleton identity and schedule offset vary by seed.

Measured final evidence: the semantic gate checked 600/600 strict inputs,
12/12 production lessons and 48/48 query rotations. Fixed-seed enumeration
checked all four starts in each of three bands: 12 lessons and 48 rotations.
The larger production census checked **100 lessons per band**, **300 total**,
with **1,200 unique inputs** and **1,200 query rotations**. It found zero
ambiguities, scoring errors or materialization errors against the declared
rivals. These are distinct populations, not counts to be added as independent
coverage. Full instances, exact seeds and accepted indices are in the retained
reports. The fixed-seed schedule receipt hash is
`7405263c8f95c3a5431c7ff4d0f45ab818bbf6877003f4d47972b4526cc4f163`.

The proof argument applies to consecutive, unrejected, same-seed windows with
no explicit `n_codes` or `motif_size` override. Those exact overrides are lawful
but may remove an anchor or force symmetry. Independently seeded assembly,
nonconsecutive selection and different hypothesis classes need their own
evidence. The passing census does not establish uniqueness among all programs,
all-seed coverage, or training admission.

## D5: final exposed solve and self-review

The final solve was prepared from the same generator hash and used three
visible demonstrations and two masked queries, a different format from the
four-pair lesson census. One actual revision passed **3/3 visible examples**.
A separate visible-only search found eight codebooks fitting those three
labels, all agreeing on both query predictions. This supports a finite-family
query-consensus claim, not uniquely recovered meanings for every instruction.
The episode declares prior rule exposure and no reference consultation during
solving. Masked-query correctness remains unknown.

Self-review: the schedule intentionally restricts three quarters of default
script slots to teaching anchors, so free scripts, symmetric motifs, all colors
and exact controls remain to keep the declared broader support real. I checked
all declared rivals at cyclic boundaries and query rotations, retained concrete
sorting/deduplication/codebook witnesses, and leave untested rival families and
override-based lesson assembly outside the acceptance claim.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/8096ecc43d5a/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Native parametric family — review-789b5940d1ff7764 (2026-10-25)

Built a new native `script_order={left_to_right,right_to_left}` family under
`workspace/parametric/` without changing the selected production generator or
canonical authority. The default program is byte-exact canonical source
(`04788c0240d6550baf1344b31b28de075108d0b89dcfe18faf5f1615115fd17c`).
The alternative reads the same visible instruction cells in reverse order. Step
A produces an ordered code sequence; Step B crops the motif and folds every
transform over the current result in that order.

The sampler is deterministic, setting-blind, and independently prefix-stable for
2–6 demonstrations and 1–4 queries. The first two demonstrations reject the
other declared setting plus sorting, deduplication, adjacent-collapse,
first-only, last-only, and no-script shortcuts. The fourth query is a 30×30
input with a connected asymmetric 28×30 body, more than 500 colored cells, and
left/right/bottom boundary contact. Public turns retain demonstrations and one
masked query input only.

Current evidence:

- Focused native tests: 6 passed.
- Full staged task suite: 74 tests passed.
- Self-audit: 170 episodes over seeds 0..15 and 17, both settings, every demo
  count 2..6, four queries, 2,040 protected-Racket evaluations, zero findings.
- Native qualification: 4 jobs, seeds 0 and 17, two demos/four queries,
  32 protected-Racket evaluations; status `qualified`.
- Causal witness: forcing left-to-right order in a qualified right-to-left
  episode changes the final protected-Racket output; builder replay and
  independent replay both passed.
- Qualified public projection: 4 episodes / 16 sequential one-query views;
  saved projection verification passed.

Source inventory: `workspace/parametric/evidence/manifest.json`.
Qualification: `checks/8096ecc43d5a/qualification/qualification.json`.
Witness: `checks/8096ecc43d5a/causal/witness.json`.

Limits: the named sequence rivals and finite seeds are not a universal
identifiability proof. Exact-source owner integration, fresh owner qualification,
acceptance, and any training-admission decision remain pending.
