# Current decisions: 75ba893e1e36 / 59341089

## Selected repair and authority

Proposed selected generator version 2.0.0, reviewed in assignment `review-adc50ac64e6b84c4`. The
intended transformation is `mirror | input | mirror | input`: each row becomes `(reverse(row) + row)` repeated
twice. The canonical program and its five labeled pairs remain unchanged;
`RULE_HASH = 6d59d4b5186a` pins that authority. The selected base solution's active `racket_target.target_code`
is synchronized byte-for-byte with the canonical program. Its archival `raw_code`
is unchanged. This is an active-source synchronization, not a new rule or training
approval.

## Ordinary domain and control contract

Ordinary inputs are rectangular ARC grids with literal integer colors: height 1–15,
width 2–7, exactly two or three colors, and at least one unequal LR-mirrored pair.
The output is therefore at most 15 × 28. `self_check` recognizes this domain
without trusting metadata. `strict_canonical_like` additionally requires 3 × 3 and colors
drawn from 5, 7 and 8. All five canonical inputs remain accepted, including the
two-color pair; the earlier parametric draft's three-color-only assumption was
reversed.

Exact shape and palette controls are validated before sampling and checked from
pixels by `observe_overrides`. An explicit palette determines its count unless a matching
explicit count is supplied. Unbound dimensions are conditioned on the requested
palette capacity. Only an incompatible request with all relevant axes fixed, such as
height 1, width 2 and three colors, is rejected as a joint conflict. Error axes name
the caller's palette argument when its length supplied the count.

The imported version advertised unreliable `left_edge_kind` and `row_pattern`
controls; their original design rationale was not recorded. Version 2 retires both
with an explicit migration error. Fixed `lr_asymmetric=True` remains a compatibility
argument; false requests and negative texture names move to the separate
`make_degenerate` API. That API supplies symmetric, monochrome and single-column
fixtures that the ordinary validator deliberately rejects.

All nine helpful texture names remain starting priors, followed by exact color and
asymmetry constraints. `bg_density` and `noise_overlay` are causal per-cell
probabilities, applied with or without a texture override; they are not exact final
pixel fractions. A random mirrored cell pair, rather than a fixed corner, protects
the reflection witness while missing requested colors are inserted. Malformed
scalars, unknown keys and impossible requests fail explicitly.

## Lesson schedule and reversals

The imported default used only 3 × 3 inputs. A fixed 3 × 3 crop/pad rival fits all
five canonical pairs, so that default could not teach width generalization. The
first repair alternated canonical and varied-width draws (a two-step schedule). Its
finite census of 300 lessons and 1,200 rotations passed, but independent review
found seed 305 in the easy band: duplicate filtering removed the second identical 1
× 2 witness, leaving one ambiguous query rotation. Actual `Catalog.generate` and Racket
outputs are retained at `checks/code-review/public-rotation-47565626/`.

The current four-step schedule uses a canonical draw, an even-width witness, a
canonical draw and an odd-width witness. Canonical draws are 3 × 3; alternating
width witnesses use disjoint sets {2, 4, 6} and {5, 7}. Thus the two width witnesses
in a four-candidate window cannot be equal, and production duplicate filtering
cannot remove the second merely for matching the first. Each ordinary lesson with
three demonstrations and one query retains width evidence when any one pair is held
out. Explicit shape overrides supersede the default schedule; arbitrary overridden
curricula do not inherit this teaching claim.

Height and palette-count weights vary by difficulty; both counts, 2 and 3, remain
supported. Half the default raw indices retain the canonical profile, with
`MIN_STRICT_FRAC=0.40` checked empirically. Variable width teaches the intended shape
transformation; no ordinal lesson index or hidden parameter is exposed to the
learner. Four finite rivals are declared: unchanged four copies, input-first phases,
vertical instead of horizontal reflection, and a fixed 3 × 3 canvas. The schedule
addresses the exhibited width shortcut; finite checks do not prove universal rule
identifiability or distinguish every possible rival.

## Defects, tests, tools and remaining decision

Original witnesses live in `counterexamples/review-adc50ac64e6b84c4/`. `tests/test_generator_contract.py` covers exact controls,
negative fixtures, invalid inputs, causal priors, feasible partial requests and
duplicate filtering. Independent review additionally exposed a partial request
rejected after an unbound width draw; the free-dimension conditioning repairs this.
Its failing and passing runs, each tied to its source hash, are under `checks/code-review/`
and `checks/partial-overrides/` in the review return.

The generic `selfcheck-minimal-impostor` warning remains a shared-tool decision. Some singleton,
short-line and 2 × 2 block patterns are ordinary lawful asymmetric inputs for this
whole-grid rule. `workspace/mutation_probe.py` separates input validation, actual canonical
execution and disagreement with a four-copy rival. The final linter-input probe
supplies all accepted named shapes. We preserve the warning and do not ban lawful
inputs just to obtain a green aggregate.

The pre-existing open audit `review-1fe8e6e6e8fd3ff4:v0001` was used as a lead for the
matching-edge/asymmetry and palette metadata failures on original SHA
`9c4571d481c526b53617e6cd3fb37a1f9df91154abece8bc2277c85054197db0`. Its stored `evidence/review_index.json` remains unchanged. This repair proposal
does not resolve that disposition or any unrelated audit automatically.

`workspace/parametric/` is a separate proposed episode API: first tile {mirror, input} and
tile-pair count {1, 2, 3}, fixed once per episode. Six bounded settings were
materialized with actual Racket labels and distinguished by their three
demonstrations. It is not selected by ordinary generation and has no training
admission. See its README and `checks/parametric/bounded-six-v2/`. The source-bound completion probe in
`workspace/partial_override_probe.py` is a reusable authoring diagnostic; a found completion falsifies a
claimed conflict, while an unsuccessful bounded search remains inconclusive.

The final override matrix also retains one nonblocking noise-prior diagnostic:
20 of 90 same-seed extreme comparisons are identical; 70 differ. A random
recolor may choose the current color, and exact constraints can overwrite its
changes, especially on a two-cell grid. The documented control is a stochastic
prior, so equality on an individual draw is allowed. It is applied causally on
all routes; this disposition does not weaken exact shape or palette promises.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-1fe8e6e6e8fd3ff4:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `9c4571d481c526b53617e6cd3fb37a1f9df91154abece8bc2277c85054197db0`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit repair-bound closure against accepted source05dacbfebeb9c1a1e82ffc3114926d6b36ef6bae6575099271d05ef1ee2ac311. Former matching-edge/asymmetry conflict is removed via explicit retired-control migration errors; a protected random mirror pair guarantees distinct colors and LR asymmetry in ordinary draws. Palette controls now advertise ordinary2/3 colors and enforce exact realized counts; unsupported monochrome/symmetric cases use separate negative fixtures rather than a false advertised endpoint. tests/test_generator_contract.py, original-controls.json, checks/control-analysis/ and final source 45900-call override receipt plus30 tests/1640 subtests support this focused reviewer-reported closure. Remaining stock small-shape warning and stochastic noise diagnostic are distinct and not waived.

### Assessment or prior finding

## 75ba893e1e36

**Findings-only adversarial audit; target unchanged.** Reproduced two control-contract defects on generator SHA-256 `9c4571d481c526b53617e6cd3fb37a1f9df91154abece8bc2277c85054197db0`, with canonical Racket rule hash `6d59d4b5186a`. Evidence: `checks/audit/75ba893e1e36/report.json`; portable replay: `checks/audit/75ba893e1e36/reproducer.py`.

**A75-1 — reproduced helpful-override defect: requested LR asymmetry can remain symmetric.** Exact call: `generate(1, 0, difficulty=None, left_edge_kind="matching", lr_asymmetric=True)`. Input: 3 rows × 3 columns. Actual Racket output: 3 rows × 12 columns. Returned input is `[[7,5,7],[7,5,7],[5,5,5]]`. This is LR-symmetric despite `lr_asymmetric=True`; the target's own `self_check` rejects it with “input is LR-symmetric, so mirror|input phases are visually identical”. `_shape_left_edge(...,"matching",...)` makes the rows symmetric; the following asymmetry repair writes `palette[1]` into `g[0][0]`, which is already that color for this draw, so it changes nothing. Ensure the chosen replacement differs from the opposite edge, or reject mutually incompatible controls explicitly. Bounded scope: exact seeds 0 and 1, sample index 0, those same overrides; seed 0 passes and seed 1 fails (1/2 inspected calls, not a population-frequency estimate).

The supported `Catalog.apply(..., check_generator_domain=True)` executed the canonical Racket rule on the exact witness: mirror|input|mirror|input equals the rival “four unchanged horizontal copies” on this input. The unchanged-copy rival fits **0/5 labeled canonical pairs**, so this is a local ambiguity caused by the symmetric generated witness; it is not claimed as a canonical shortcut. The retained authority receipt independently marks the witness's generator domain **invalid**. No successful production export, false authoritative label, or full-lesson identifiability failure is claimed. This is a reproduced generator/control and validator inconsistency.

**A75-2 — reproduced declared-range defect: `palette_size=1` cannot execute.** AXES declares `palette_size` valid `1..3`, but `generate(0,0,palette_size=1)` raises `ValueError("draw_int('palette_size'): override 1 outside [2, 3]")`. The same error occurs with the explicitly documented degenerate texture `monochrome`. Both exact calls are retained (2/2 inspected endpoint calls). Reconcile the advertised bound with the actual sampler and the intended degenerate-domain policy; neither call currently reaches its texture branch.

**Actual replay:** from `WORK/`, run `python3 run_with_racket.py ../.venv/bin/python ../checks/audit/75ba893e1e36/reproducer.py` (exit **0**; payload cwd `repo`). This exit means both defect assertions and the Racket witness check reproduced successfully, not that the target passed an audit battery. `report.json` retains seed, sample index, overrides, exact source/rule hashes, both input grids, authoritative output, rival output, domain errors and the command record. The audit read the selected generator, notes, empty associated notes and selected canonical record; there was no `evidence/review_index.json`. No source changes or full battery were performed, and production-distribution and lesson-wide behavior remain untested.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-1fe8e6e6e8fd3ff4-v0001/audit_assets.json), manifest SHA-256 `96d9addd81e81b856c1e1523b65502dcd225e5d18903f2cf5ff84f1280bdf720`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current maintainer acceptance

Accepted source `05dacbfebeb9c1a1e82ffc3114926d6b36ef6bae6575099271d05ef1ee2ac311` under the owner lightweight policy. Stock battery remains **11/12** because the generic minimal-shape warning fails strict defect lint. The exact linter-input mutation probe reports36 Racket cases,15 accepted unique whole-grid asymmetric inputs, all refuting four unchanged copies. This supports accepting this task repair; no shared lint waiver or all-green claim is made. The separate noise warning remains20/90 identical paired sweeps. The two prior control findings are explicitly closed by exact postconditions/truthful v2 migration; see retained stock-gate-limits and authority-sync manifests. All repair/prototype executions remain reviewer-reported. Canonical authority is unchanged; the active base copy now equals it.
## Current reviewer considerations

Source SHA-256: `05dacbfebeb9c1a1e82ffc3114926d6b36ef6bae6575099271d05ef1ee2ac311`.

# Decisions and limits — 75ba893e1e36

Assignment `review-adc50ac64e6b84c4`; proposed version 2.0.0. Final generator SHA-256:
`05dacbfebeb9c1a1e82ffc3114926d6b36ef6bae6575099271d05ef1ee2ac311`. The selected task's concise current account is `repo/generators/75ba893e1e36/notes.md`. This
document records alternatives, reversals and limits; exact command receipts are in
`RESULTS.json` and the referenced evidence directories.

## Rule and authority

The canonical function appends four horizontal phases: LR-mirror, input, LR-mirror,
input. Height is preserved and output width is four times input width. The four
training pairs and one labeled test pair all have 3 × 3 inputs and use colors 5, 7
and 8; one pair uses only two of them. The original generator's canonical scale and
palette were therefore understandable anchors, but its imported notes contained no
recorded rationale for the other control choices.

No canonical pair or canonical program was edited. `RULE_HASH=6d59d4b5186a` now binds the
generator to the canonical program. The selected base solution's active
`racket_target.target_code` was made byte-identical to that program; archival `raw_code` was
retained. Before repair, behavioral parity passed but active-text authority
synchronization failed. This correction removes competing active representations
without changing the intended mathematical transform. The canonical ledger remains
byte-identical to the packet baseline.

## R1–R5: Exact input controls and truthful validation

The baseline matching-edge repair could assign a cell its existing value, leaving an
LR-symmetric input despite `lr_asymmetric=True`. Seed 1 at sample index 0 with matching
edges is a retained witness. The old `palette_size=3` request produced only two colors
for 3/100 seeds in 0–99 at sample index 0; seed 3 is the smallest retained witness.
A 1 × 1 request could return fewer colors than requested, width 1 always hid
reflection, and palette size 1 was advertised but rejected. Coercions from Boolean,
float and string values and unknown controls were accepted in other paths. See
`checks/control-analysis/baseline-control-observations.json` and `counterexamples/review-adc50ac64e6b84c4/original-controls.json` in the task patch.

The repair chooses a random row and mirrored column pair, assigns two distinct
requested colors there, and preserves that pair while inserting a missing third
color. This gives observable asymmetry and exact palette cardinality after all
texture operations. A fixed corner witness was rejected as an alternative: it would
add an unnecessary positional signature. Unbounded retry loops were also unnecessary
for these small exact constraints.

The ordinary domain is now explicit: literal integer colors 0–9, rectangular grids
with height 1–15 and width 2–7, exactly two or three colors, and LR asymmetry. This
keeps outputs within 15 × 28. `self_check` evaluates that domain without metadata;
it no longer generates 4 × 5 inputs or inputs with custom palettes and then rejects
them merely for being outside the default profile. `strict_canonical_like` is the narrower
predicate for 3 × 3 grids using the canonical palette. Negative monochrome,
LR-symmetric and single-column fixtures have a separate API and are never ordinary
draws.

`left_edge_kind` and `row_pattern` were removed from the advertised axes and now
raise explicit migration errors. Trying to preserve undocumented competing edge and
row contracts would add restrictions unrelated to the whole-grid rule. Silently
accepting them was rejected. This is an intentional API change covered by the
version 2 bump. `lr_asymmetric=True` remains only as a fixed compatibility argument, not a
varying Boolean axis. Its false value points callers to the negative-fixture API.

## Causal priors and distribution

All nine helpful texture names remain available. They are initial priors, not
promises that the final constrained image is an exact geometric template. The
original noise/density paths could be bypassed unless a texture was also supplied.
Paired runs at seeds 0–31 and sample index 0 produced identical baseline and
override grids in 32/32 cases for density 0.95 and noise 0.3. The repair applies
both controls on every relevant path and validates their finite bounds. These are
per-cell replacement probabilities before exact constraints; a requested density is
not an exact final fraction on a tiny grid.

Default palette colors stay within the set {5, 7, 8} for canonical support, with two
or three colors selected and permuted independently of the transform. Legal custom
palettes expose the same color-agnostic rule and are checked explicitly. Easy leans
toward two colors and smaller witness heights; medium/hard increase the three-color
and larger-height weights. Both counts and the full declared shape bounds remain
supported. This is a curriculum proposal, not evidence that the nominal bands order
human or model difficulty correctly.

## R6: Feasible partial requests must adapt free dimensions

Independent review found a defect in the first repaired source `b2924152…` that
its own override stage missed: `generate(4,1,difficulty="medium",grid_h=1,
palette_size=3)` chose a width of 2 on the unspecified
axis and raised. The request is feasible with width 4. That slice failed for 43/200
seeds in 0–199; fixing width 2 and leaving height free failed for 4/200. The
standard override stage had nevertheless accepted seven such message-based
rejections in 45,900 attempts with zero findings. This is direct evidence that
error-message wording is insufficient to certify incompatibility.

Free height choices are now conditioned on available width and requested color
capacity; free width choices are then conditioned on chosen height. Fully fixed
impossible requests still fail, and diagnostic axes name the actual supplied palette
when its length inferred the count. The regression exercises both schedule parities,
all three bands, 33 seeds and five request families. Its first run produced 66
failing subcases; the corrected source passes them. The reusable `workspace/partial_override_probe.py`
additionally finds concrete completions on the frozen defective source and
distinguishes an inconclusive search from proof of impossibility. This repair
changes only requests requiring capacity adaptation.

## R7: Teach width after production duplicate filtering

The fixed 3 × 3 crop/pad rival agrees with all five canonical pairs. Retaining only
3 × 3 default inputs cannot expose it. The first repair alternated 3 × 3 anchors and
varied-width examples. Both a 300-lesson census and a fixed-seed schedule census
passed, but the finite result did not prove the schedule claim.

Independent review found seed 305 in the easy band: raw odd indices 1 and 3 were
both `[[8,5]]`. The production sampler rejected the latter as a duplicate pair.
Its materialized four-pair bundle then contained only one varied-width example.
Holding that example out left three demonstrations that fit the fixed 3 × 3 rival,
whose query was 3 × 12 instead of the reference 1 × 8. Actual public generation,
Racket labels, rejection logs and the full ambiguous rotation are retained in
`checks/code-review/public-rotation-47565626/` and a minimal task counterexample. An earlier natural solve failure
was not invented to illustrate this defect.

The final four-step schedule uses canonical 3 × 3 draws at positions 0 and 2, widths
{2, 4, 6} at position 1, and widths {5, 7} at position 3. The witness classes have
disjoint shapes, so the two width witnesses cannot duplicate one another. A
four-pair lesson therefore keeps at least one width witness in its three
demonstrations when any single pair is held out. Canonical duplicates may advance
the producer's cursor; the checks use the actual accepted pairs. Explicit shape
overrides supersede this default teaching schedule and require their own lesson
assessment.

Final evidence uses three demonstrations and one query, production ordering from the
public sampler, plus every single held-out-pair rotation. The 300-lesson census has
100 lessons in each of the easy, medium and hard bands: 1,200 pairs, 1,167 unique
inputs, zero ambiguous production lessons and zero ambiguous rotations out of 1,200.
`checks/lesson-census-period4-final.summary.json` points to the lossless full report. At fixed seed 0, the checks cover
all four starting positions in the schedule across all three bands: 12 lessons and
48 rotations, all without declared-rival ambiguity. Source-bound seed 305 public
generation also passes its four rotations after repair.

There are four unique declared rivals, not nine: compatibility namespaces alias the
same functions. They cover unchanged copies, input-first phases, vertical reflection
and fixed 3 × 3 canvas. Finite passes do not establish universal identifiability.
Raw candidate counts, overlapping census windows and unique inputs are reported
separately; no universal all-seed claim is inferred from a single-seed exhaustive
schedule receipt.

## R8: Preserve lawful minimal shapes and the shared warning

The generic defect heuristic assumes accepted singleton, short-line or solid 2 × 2
mutations are suspicious. For this whole-grid rule, a small pattern that is
LR-asymmetric with two colors still carries the required reflection signal. Banning
it by geometry would narrow the legitimate domain merely to silence a heuristic, so
that alternative was rejected.

The final-source probe takes the exact six eligible default easy inputs used by the
heuristic (seed and sample index both set to each value from 1 to 6), enumerates all
five mutations plus originals, and executes actual canonical Racket on all 36 cases.
It observes 33 unique inputs, 15 accepted unique inputs and 21 rejected cases. All
15 accepted inputs differ from the four-copy rival; accepted mutation kinds are
singleton 2/6, solid 2 × 2 6/6 and short-line 1/6, alongside the six originals.
Reference execution alone is not domain evidence: even the 21 rejected cases have
valid reference outputs. See `checks/mutation-lawfulness/linter-final-source/report.json`.

The strict shared warning remains recorded as a blocker; the task patch changes no
detector or approval. A maintainer may assess the bound semantic evidence, then
change or scope the heuristic in its authorized shared-tool workflow. The companion
rectangle audit demonstrates why a blanket tiny-shape exemption or trust in
`self_check` alone would be unsound.

## Proposed parametric extension

`workspace/parametric/` introduces two episode-fixed parameters: first tile {mirror, input},
and tile-pair count {1, 2, 3}. Each episode has three demonstrations and one query
under one instantiated Racket program. The six combinations cover both ordering and
repeat count with bounded output width 18; default mirror/two pairs is
byte-identical to the canonical program and agrees on all five canonical pairs. It
is separate from the selected ordinary generator.

The bounded six-setting probe retained 18 demonstration and 6 query labels, 154
actual Racket grid executions, 30 directed parameter-rival checks, six identified
episodes and zero ambiguous parameter rivals. Six settings yield six distinct
outputs on one common witness. Public episode files contain only demonstration pairs
and query inputs; private parameters, programs and labels are separate. Five focused
tests pass. The initial overly strict palette assumption failed and was repaired;
that failed report and source snapshots remain retained.

This establishes a runnable finite proposal, not a production distribution over all
possible transformations. Parameter seeds, program hashes, private label traces and
distinct-output checks are in `checks/parametric/bounded-six-v2/` and `checks/parametric/final-receipt.json`. The separate
canonical repair neither selects nor approves these variants.

## Audits, solves and handoff policy

Both randomly assigned audits are findings-only and remain separate in
`AUDIT.md`. The baseline open main-task audit was used as a lead; no stored
audit disposition was edited. Blind and post-repair solves have separate
source/exposure records; masked query correctness stays unknown until independent
maintainer scoring.

All meaningful failing attempts are retained. The 50,789,328-byte original baseline
override report is stored losslessly as a 784,340-byte gzip with original path,
raw/compressed hashes and restoration helper; no failed rows were dropped. The final
source patch must be applied to a fresh original extraction and every changed/new
file checked against its expected bytes before delivery. Strict acceptance and
training admission remain distinct from this useful repair work.

## Nonblocking stochastic-control warning

The final override stage reports `PASS_WITH_WARNINGS`: all 45,900 matrix draws
were accepted with zero findings and no explicit rejections. Its one axis-effect
warning reports identical noise-overlay extremes on 20/90 same-seed sweeps
(easy 7/30, medium 7/30, hard 6/30), hence different outputs on 70/90. Random
recoloring can select the current value, and the exact palette/asymmetry repair
can erase edits; on a two-cell input the protected pair fixes the entire grid.
This is consistent with the documented stochastic prior and is distinct from
the original bypass, which produced equality on all 32/32 tested pairs. We retain
the warning and its counts. The strict aggregate blocker is the separate
`defect_lint` warning, not this nonblocking axis-effect diagnostic.
