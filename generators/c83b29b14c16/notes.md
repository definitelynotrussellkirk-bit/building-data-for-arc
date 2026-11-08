# Working notes: c83b29b14c16

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `93ea98ee035b25567b69bd106b925288a8bffb2cecb07144b23dcfbc026600a4`.

# Decisions for c83b29b14c16

## D1 — Preserve the selected Racket authority

**Choice.** Keep the canonical program unchanged and pin `RULE_HASH = "d264380c5850"`.

**Why.** The authority already implements the intended conditional exactly: only colors occurring exactly twice are considered, and only row- or column-aligned pairs are filled. All five canonical outputs are consistent, and the baseline rule smoke / authority stages were already green.

**Rejected alternative.** Changing the authority to require a minimum endpoint distance or to exclude distractors would encode baseline sampler assumptions rather than the canonical rule. The failing one-gap examples proved that the sampler/self-check was wrong, not the Racket program.

**Probe.** Canonical mirror tests plus 1,800 generated Python–Racket comparisons.

**Limitation.** A rule hash is source identity, not a formal proof of semantic equivalence.

## D2 — Replace decorative axes with seven observable controls

**Choice.** Remove `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`; expose only dimensions and exact object-category counts recoverable from pixels.

**Original rationale.** Unknown. The retained notes were empty. In v1.1.1 most axes were not consumed, and degenerate texture names shared the advertised valid domain.

**Why.** Training metadata must describe the returned grid. Exact counts let the override gate and task tests falsify every advertised control.

**Rejected alternatives.** Keeping legacy names as aliases would preserve misleading controls and create multiple keys for the same pixel property. Marking them “diagnostic” would still not improve curriculum design.

**Failure modes checked.** Unknown keys, booleans/strings masquerading as integers, out-of-range values, single-axis and multi-axis boundaries, and every difficulty band.

## D3 — Anchor ordinary sizes to canonical profiles

**Choice.** Default to `(7,7)`, `(8,8)`, `(9,9)`, `(8,9)`, or `(9,10)` in every band; permit exact 7..10 overrides independently.

**Why.** The baseline had zero hard-band profile support. Canonical-scale support should not disappear when difficulty changes.

**Rejected alternative.** Making hard mode 10..12 teaches a scale absent from the examples and caused the measured starvation. Fully uniform 7..10 dimensions would reduce exact canonical-profile frequency for no task-specific benefit.

**Probe.** Final profile floor: 11/60 exact and 31/60 in envelope, with no zero-support band.

**Limitation.** Ordinary `grid_h=10` is not sampled because no canonical profile has height 10; it remains available as an exact override.

## D4 — Use pair count, not canvas scale, as the simple difficulty axis

**Choice.** Easy emits two active pairs, hard emits three, and medium alternates two/three.

**Why.** This changes simultaneous bookkeeping while preserving the task's visual scale and semantic branches.

**Rejected alternative.** Larger hard canvases add empty space rather than rule complexity. More than three active colors would exceed the canonical range and crowd the compact construction.

**Probe.** The 120-lesson census observed 600/600 easy pairs at count 2, 300/300 medium split, and 600/600 hard at count 3.

## D5 — Include the one-gap branch in every ordinary sample

**Choice.** Set default `n_short_pairs=1`, where endpoint distance is two and exactly one cell is filled.

**Why.** Two canonical pairs use this branch, yet v1.1.1 rejected it. It is also the cheapest counterexample to the wrong “only long connectors count” rule.

**Rejected alternative.** Merely lowering the old self-check threshold while keeping long-only sampling would accept canonical data but still fail to teach the branch.

**Probe.** Witness `one-gap_pair` fired 600/600 in the standard semantic census and 1,800/1,800 pair observations in the deep probe.

## D6 — Schedule negative controls over four consecutive samples

**Choice.** `sample_index % 4` selects canonical-only, diagonal-pair, aligned-triple, or singleton control. Four demos therefore cover all modes regardless of cyclic starting residue.

**Why.** The canonical pairs do not falsify two plausible wrong rules: filling an exact pair's bounding box and connecting aligned extrema regardless of multiplicity. Generated controls must do so inside complete lessons, not just somewhere in a marginal census.

**Rejected alternatives.** Random rare controls make lesson quality probabilistic. Three demos cannot guarantee coverage of the canonical scene plus all three control categories for every start.

**Probe.** All four start residues were tested 30 times per band. Both canonical-fitting shortcuts were refuted by the demos in 120/120 lessons per band.

**Limitation.** The deterministic period is learnable; the visual samples still vary independently, but a future scheduler could permute the same guaranteed cover.

## D7 — Use a universal constructive tile instead of rejection sampling

**Choice.** Place the maximum legal combination in disjoint regions of a 7x7 tile, select the requested subset, then apply a keyed D4 transform, offset, and color permutation.

**Why.** It proves every advertised override combination is feasible, terminates deterministically, and prevents connector-span collisions or count loss.

**Rejected alternative.** Random capped placement can silently under-produce requested objects—the exact defect reproduced in audit target `44d20451ce17`—or make rare override combinations flaky.

**Probe.** 14,130 override draws, including all boundary combinations and all bands, passed with exact observed counts.

**Limitation.** Relative role geometry is narrower than a general backtracking placer. This is the main remaining shortcut risk and is stated in `REVIEW.md`.

## D8 — Validate a task manifold broader than canonical positive examples

**Choice.** `self_check` accepts aligned exact-two pairs plus at most one singleton, diagonal pair, and aligned gapped triple, while requiring two/three active pairs, both orientations, blank interiors, and nonintersecting connector spans.

**Why.** Lawful rule inputs include non-firing categories. Treating them as invalid would make it impossible to teach the conditionals.

**Rejected alternative.** Restricting every color to exactly two aligned cells reproduces the baseline's positive-only ambiguity.

**Failure modes checked.** Ragged grids, invalid colors, blank scenes, adjacent endpoints, excessive category counts, non-collinear triples, occupied interiors, intersecting spans, and mismatched requested metadata.

## D9 — Declare executable rivals and witnesses

**Choice.** Add identity, short-pair-skipping, count-blind extrema, diagonal-bounding-box, horizontal-only, and vertical-only rivals; bind each witness to the rule it refutes.

**Why.** Named rivals convert “looks varied” into falsifiable teaching claims. The count-blind and bbox rivals were first verified to fit all five canonical pairs, making their generated counterexamples necessary rather than decorative.

**Rejected alternative.** Witness-frequency-only declarations can fire while the alleged rival still agrees, which the shared gate explicitly warns against.

**Probe.** Standard gate verified five of five rival claims; deep probe reported zero competitor errors and zero lesson-level survivors.

## D10 — Add focused tests before implementation and retain RED evidence

**Choice.** Add 15 task-local tests under the permitted task test directory, then implement to make them pass.

**Why.** The battery does not automatically discover task tests, and the baseline had no regression contract for exact controls or lesson semantics.

**RED result.** 14 failed, one passed: missing rule hash/hooks, rejected boundary overrides, accepted unknown override, and ragged-grid crash.

**GREEN result.** 15/15 passed in the portable task-test runtime.

## D11 — Build a reusable, source-bound 120-lesson probe

**Choice.** Retain `workspace/lesson_probe.py` and its JSON result/execution receipt. It dynamically consumes the generator's declared competitors and shortcuts, uses canonical Racket labels, records uniqueness/domain coverage, and tests every cyclic start.

**Why.** The standard semantic gate's 12 lessons are a smoke check. The assignment explicitly required at least 100 lessons per band when canonical-compatible rivals exist.

**Failed attempt retained.** Running the probe directly omitted the packet's protected Racket environment and failed before producing accepted data. The rerun through `run_with_racket.py` passed.

**Limitation.** 120 lessons per band provide a finite deterministic census, not a claim about every seed or unlisted shortcut.

## D12 — Episode-fixed exact-count prototype and teaching repair (2026-10-24)

**Decision.** Add a separate proposed parametric family with `required_count` in
`{2,3}`. The default count-2 Racket source is byte-for-byte canonical; count 3
preserves the same color grouping, horizontal/vertical alignment, and extrema
fill. Matched inputs contain firing groups for both counts and non-collinear
controls, so demonstrations identify the episode setting from labels alone.

**Canonical repair.** The four-sample construction previously used only even
aligned spans and 45-degree diagonal controls. A shortcut could therefore cap
attention to even spans and treat every oblique exact pair as a diagonal box.
The retained cycle now includes an odd span and a skew non-collinear pair; the
new named competitor is executable and refuted.

**Boundary/export evidence.** The adapter supports 2–6 demonstrations and 1–8
queries independently; the first four queries include a substantive 30×30 scene
with occupied opposite boundaries. Protected Racket executed 28 labels across
both settings and seeds 0/17. Four saved public challenges passed the strict
public-only checker, and mutating private settings/program/query answers did not
change their IDs. The bounded adversarial pass also exercised minimum/maximum
counts and malformed settings.

**Disposition and limit.** Proposed and manifested, not accepted. Native
qualification stops at `Production generator must be approved on its current
source/rule` because this review changed the canonical generator. Owner
reapproval is the next action; the finite two-setting evidence is not a claim of
unrestricted program uniqueness or training admission.
