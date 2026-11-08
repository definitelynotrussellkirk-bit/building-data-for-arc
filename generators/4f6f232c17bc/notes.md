# Working notes: 4f6f232c17bc

## Review source and baseline

No prior return was used as a lead: the retained associated-notes file was empty.
The review used the pinned baseline generator, all five canonical pairs, the
selected Racket authority, and a completed before battery.

Baseline generator SHA-256:
`b3e9172eb5615cc86ba101ce76f6ca4b15a5bfb245c008bc0942764227cbc119`.
The before battery finished with 5 green, 1 advisory, and 6 failed stages.
Confirmed root causes were:

- no `RULE_HASH` and dead/misdeclared axes;
- a left-only validator that rejected three lawful canonical right-source inputs;
- a centered, left-source-only sampler with no clipping, distractor, or semantic
  teaching contract;
- no exact support for the canonical four-color profiles in easy/hard draws;
- ignored/invalid overrides and an accepted unknown key.

Evidence: `checks/before/checks/4f6f232c17bc_before_battery_summary.json`.

## Selected repair

Version `3.0.0` keeps the selected Racket rule unchanged and rebuilds only the
input curriculum and its executable contract.

- Pin `RULE_HASH = "549dba88300b"`.
- Expose six exact axes: `grid_h`, `grid_w`, `blue_size`, `source_side`,
  `mirror_visibility`, and `n_distractors`; reject unknown or malformed inputs.
- Construct a 4-connected blue object on either side of a unique full-height
  divider, with both full and per-cell-clipped reflections.
- Schedule all five canonical shape/palette profiles every fifth sample while
  retaining expanded profiles between anchors.
- Cycle four semantic states—left/full, right/partial, left/partial,
  right/full—so every three-of-four query rotation contains both source sides
  and a clipping witness.
- Include ignored distractors in ordinary draws, including an off-axis gray
  case, while allowing exact `n_distractors=0`.
- Add an independent Python rule mirror, structural validator, exact override
  observer, five semantic witnesses, five executable rivals, and
  `lesson_identifiable`.

## Test-first evidence

The focused regression suite was written before the production rewrite. The red
run is retained at `checks/tdd/red-before-generator.log`; the final suite contains
47 tests covering canonical ownership, authority pinning, every axis boundary in
every difficulty band, malformed inputs, deterministic generation, schedule
rotations, witness/rival truth, and the independent probe.

The independent probe is
`workspace/reference_probe.py`. It uses portable canonical helpers and does not
import production geometry. Its final 120-draw run accepted all 5 canonical
inputs, matched all 5 canonical outputs, covered both source sides and both
visibility modes in every band, and found a counterexample to every declared
rival. Evidence: `checks/after/reference-probe.json`.

## Final verification

Final generator SHA-256:
`d29fc0a8ba27c5aa30326b0837e31042590061c6ed8fa87b84d305a8644a3428`.

- full after battery: 12/12 green;
- selected task tests: 47/47 passed;
- rule smoke: 120/120 applied, 112 distinct outputs, 0 crashes, 120/120 mirror
  parity;
- profile floor: 31/60 exact canonical-profile hits and 60/60 envelope hits,
  with exact support in every band;
- override matrix: 18,180 accepted draws, 202 cases, 0 findings;
- required-rotation semantic gate: 12/12 lessons and 48/48 rotations
  identifiable against the declared rivals;
- source-bound census: 300/300 lessons, 1,200 labelled pairs, 1,200 unique
  inputs, 0 production ambiguities, and 0/1,200 ambiguous rotations.

## Limits

The distribution deliberately stays within 8–10 rows, 11–14 columns, connected
blue objects of size 3–8, and at most three distractors. The finite semantic
checks cover five named plausible rivals; they do not prove uniqueness against
all possible hypotheses. This remains a single-operation task; no artificial
composition was added.
## Current reviewer considerations

Source SHA-256: `d29fc0a8ba27c5aa30326b0837e31042590061c6ed8fa87b84d305a8644a3428`.

# Decisions for 4f6f232c17bc

## D1 — Keep the selected Racket authority unchanged

**Choice.** Pin `RULE_HASH = "549dba88300b"` and repair only input generation,
validation, tests, and curriculum metadata.

**Rationale.** All five canonical pairs and the rule-smoke stage agreed with the
existing authority. The baseline defects were sampling and ownership defects,
not evidence that the transformation itself was wrong.

**Alternatives.** Rewriting the rule to enforce one source side or whole-object
clipping would have contradicted canonical examples. Adding a composed operation
would create a different task.

**Probe, failure mode, limit.** Authority sync and 120 Python/Racket parity cases
pass. This verifies the sampled domain, not arbitrary malformed grids.

## D2 — Treat either side of the divider as lawful

**Choice.** Add exact `source_side=left|right`; require the connected blue object
to lie wholly on one side.

**Rationale.** Three canonical inputs place blue on the right, while the baseline
validator and generator assumed left only.

**Alternatives.** Keep left-only and special-case canonical inputs was rejected as
two conflicting domains. Allow blue on both sides was rejected because the
canonical curriculum does not establish that interpretation and it weakens the
single-source-object invariant.

**Probe, failure mode, limit.** Every band and every query rotation contains both
sides. Two-sided blue is deliberately rejected by `self_check`.

## D3 — Model clipping per cell

**Choice.** Add `mirror_visibility=full|partial` and guarantee at least one visible
reflected cell. Partial cases include both visible and clipped source cells.

**Rationale.** Canonical examples show that out-of-bounds targets are omitted
individually. The baseline never generated this distinction.

**Alternatives.** Whole-object rejection and all-or-nothing copying were rejected;
the `all_or_nothing_clipping` rival makes the difference executable.

**Probe, failure mode, limit.** The four-state schedule leaves a clipping witness
under every query rotation. Fully invisible objects remain outside the selected
curriculum because they would produce an empty answer and teach less.

## D4 — Use a unique full-height divider, but vary its position

**Choice.** Keep exactly one full-height gray column; generate both centered and
mostly off-center axes, and permit isolated off-axis gray distractors.

**Rationale.** The selected rule searches for the full-height divider, not the
grid center or every gray cell. Canonical inputs include off-center axes and an
off-axis gray cell.

**Alternatives.** Always center was the baseline shortcut. Multiple full-height
dividers were rejected because the rule selects the first and the intended role
would become ambiguous.

**Probe, failure mode, limit.** `grid_center_axis` and
`mirror_all_nonbackground` are declared rivals. The validator rejects zero or
multiple full-height dividers.

## D5 — Preserve canonical profiles without replaying canonical grids

**Choice.** Every fifth sample cycles the five distinct canonical
`(height, width, palette-size)` profiles; other indices use expanded profiles.

**Rationale.** The baseline profile-floor check had zero exact support in easy
and hard. Anchoring profiles restores ownership while leaving geometry and
objects freshly generated.

**Alternatives.** Uniform random dimensions did not guarantee a finite profile
floor. Fixing all draws to canonical shapes would shrink diversity.

**Probe, failure mode, limit.** Final profile floor records 31/60 exact hits and
60/60 envelope hits with support in each band. The cadence is deterministic, but
profile membership does not reveal the transformed cells.

## D6 — Expose only observable, exact controls

**Choice.** Advertise `grid_h 8..10`, `grid_w 11..14`, `blue_size 3..8`,
`source_side`, `mirror_visibility`, and `n_distractors 0..3`; reject unknown keys
and wrong types.

**Rationale.** The baseline advertised aliases and degenerates that were ignored,
invalid, or contradicted its validator.

**Alternatives.** Keeping diagnostic texture aliases was rejected because callers
could not observe a stable exact contract. Wider dimensions and larger objects
were deferred until constructive support and profile evidence exist.

**Probe, failure mode, limit.** The override matrix covers all 202 cases with 30
seeds per band (18,180 draws). The declared bounds are a curriculum restriction,
not the full mathematical rule domain.

## D7 — Guarantee lesson-level witnesses, not only marginal frequencies

**Choice.** Cycle four semantic states:
`left/full`, `right/partial`, `left/partial`, `right/full`; set
`EXAMPLES_NEEDED = 3` and test all four hold-one-out rotations.

**Rationale.** Correct labels do not prevent a plausible rival from fitting all
demonstrations. Marginal side/clipping coverage does not imply each assembled
lesson is teachable.

**Alternatives.** Independent random draws and weighted resampling were rejected
because they can miss the only distinguishing witness in a lesson. A stateful
lesson assembler was unnecessary for this four-state contract.

**Probe, failure mode, limit.** Required semantic gate: 0/48 ambiguous rotations.
Large census: 0/1,200. Only five declared rivals are covered; universal induction
is not claimed.

## D8 — Add ignored distractors to ordinary production

**Choice.** Ordinary draws contain 1–3 distractors; exact override permits 0.
Colors 4, 6, 7, and 9 are used, plus an isolated gray-5 case where it cannot form
a second full-height divider.

**Rationale.** Canonical examples teach that non-blue colors are erased, but the
baseline had no distractor evidence.

**Alternatives.** A fixed single distractor color would permit a color-specific
shortcut. Dense noise was rejected because it adds visual burden without a new
semantic distinction.

**Probe, failure mode, limit.** `mirror_all_nonbackground` is refuted in every
ordinary teaching window. The selected curriculum caps distractors at three.

## D9 — Use an independent reference probe and portable tests

**Choice.** Add `workspace/reference_probe.py` and 47 task-local tests using
`reviewer_support.find_root`/`canonical_pairs`.

**Rationale.** Reusing production geometry would make tests tautological, and
fixed parent-depth paths fail inside portable task-test runtimes.

**Alternatives.** Relying only on the full battery was rejected because it does
not automatically discover selected task tests. Calling Racket for every focused
assertion was unnecessary after source-bound authority/parity checks.

**Probe, failure mode, limit.** The direct and portable task-test runs pass. The
probe independently transcribes the rule but is still a human-authored oracle;
authority sync and Racket parity guard drift.
