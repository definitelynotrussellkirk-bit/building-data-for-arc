# Working notes: f4725b891d89

Review `review-ff8ab5cf2cb86363` replaced the imported `2.1.0` generator after the
baseline battery exposed a missing rule pin, dead/unlawful metadata, 14,830 override
findings, weak canonical-profile support, and no executable semantic lesson contract.

Final source SHA-256:
`4528e73c1b0e4538083d65d9981e3f212c1967a8af71217747d2cb9393eaf40c`.
The canonical/Racket authority was not changed; `RULE_HASH` pins `d0cb884b1dae`.

Key retained evidence is packet-relative under `checks/`: `before/`, the failed
`after-attempt1/` palette-cardinality iteration, final `after/`, `task-tests/`,
`lesson-census.json`, and the TDD red/green logs. Design rationale and limitations are
in packet-root `DECISIONS.md`; `workspace/reference_probe.py` is the reusable,
production-independent oracle used by task-local tests.

Imported associated notes remain in `evidence/associated_notes.jsonl` unchanged.
## Current reviewer considerations

Source SHA-256: `4528e73c1b0e4538083d65d9981e3f212c1967a8af71217747d2cb9393eaf40c`.

# Decisions for f4725b891d89

All measurements below refer to final generator SHA-256
`4528e73c1b0e4538083d65d9981e3f212c1967a8af71217747d2cb9393eaf40c`
unless explicitly labeled baseline or intermediate.

## D1 — Keep the selected Racket authority unchanged and pin it

**Choice.** Add `RULE_HASH = "d0cb884b1dae"`; retain the existing canonical row and
selected Racket rule without modification.

**Rationale.** The five canonical pairs and real-rule smoke already agreed. The defect
was in generator metadata/distribution/teaching support, not in label authority.
Pinning makes future source/rule drift explicit.

**Rejected alternative.** Rewriting the Racket rule would add authority risk without
fixing any observed failure.

**Probe.** `test_rule_pin_and_python_mirror_match_all_canonical_pairs` independently
loads all five public labeled pairs and compares both the task-local oracle and
`rule_mirror`; the final `rule_smoke` and `authority_sync` stages are green.

**Failure modes / limitation.** The Python mirror is not the authority. It could share
a conceptual mistake with the generator, so retained Racket smoke and authority-sync
evidence remain necessary.

## D2 — Replace the inaccurate nine-axis contract with four exact axes

**Choice.** Advertise only `frame_h` (8–18), `frame_w` (8–18),
`n_top_markers` (3–5), and `n_left_markers` (3–5). Reject unknown keys, booleans,
non-integers, out-of-range values, and unknown difficulties. Declare no incompatible
combinations because the full Cartesian product is constructive.

**Rationale.** The baseline declared dead `palette_kind`/helpful `texture` controls,
negative fixtures as valid textures, redundant `palette_size` and
`n_distinct_colors`, an ignored `n_markers`, and singleton `position_bias`/`density`
axes. That produced 14,830 findings in 113,760 override draws. An exact contract is
more useful than a larger fictional one.

**Rejected alternative.** Implementing every legacy axis was rejected because several
were aliases or constants rather than independent visual controls, and lawful negative
fixtures contradict the strict training manifold.

**Probe.** `test_every_exact_axis_boundary_round_trips` checks all 64 boundary
combinations in each of four difficulty settings. `observe_overrides` recovers every
control from pixels. Final override evidence reports 26,370 accepted draws, zero
findings/warnings, and correct unknown-key rejection.

**Failure modes / limitation.** The smaller axis surface intentionally gives up direct
palette selection. Palette diversity is a curriculum/profile property, not an exact
public override.

## D3 — Use 8–18 frame dimensions and preserve canonical anchors in every band

**Choice.** Every band includes an 8×8 `canonical_anchor`; medium and hard profiles
also use asymmetric and larger preferred dimensions, up to 18×18. Random drawing has
full-domain support but is strongly weighted to the profile preference.

**Rationale.** Public canonical input dimensions are 8–10. The baseline's easy 6–9 and
hard 13–17 regimes caused zero exact canonical-profile support in easy and hard.
Keeping an anchor in each band repairs that gap while retaining extrapolative scale.

**Rejected alternatives.** (1) Preserve disjoint size bands: rejected by profile-floor
evidence. (2) Generate only canonical sizes: rejected because it removes useful scale
variation and makes difficulty bands nearly cosmetic.

**Probe.** Final profile-floor evidence measured exact hits easy 15/20, medium 15/20,
hard 6/20; task tests also require at least one canonical profile and at least four
dimension pairs in each 20-draw band sample.

**Failure modes / limitation.** Weighted sampling is not a guarantee for arbitrary
short external samples; the deterministic profile schedule guarantees preferred
profiles by sample index, while the stochastic axis draw still has rare tails.

## D4 — Restrict each header to 3–5 markers and force repeated shared colors

**Choice.** Both headers contain 3–5 markers, share exactly 2–3 colors, use every
selected color, and repeat at least one color on each side.

**Rationale.** Repeats turn the rule into a visible Cartesian-product lesson. Without
them, first-match or one-to-one pairing rivals can mimic the intended equality rule.
The 8×8 minimum frame has exactly five legal slots per header, making every advertised
count constructive.

**Rejected alternatives.** (1) Allow two-marker headers: with two colors, repetition
cannot be guaranteed. (2) Keep the legacy upper bound of eight: it is impossible in an
8×8 frame and therefore requires incompatibility metadata or silent clipping.

**Probe.** `self_check` enforces marker counts, shared color sets, color count, and
repetition. Structural-mutation tests break each property and require rejection.

**Failure modes / limitation.** This excludes lawful sparse edge cases with no repeat;
they may be useful diagnostic examples, but they are poor default training lessons for
this rule and are intentionally outside the selected strict manifold.

## D5 — Cycle four teaching profiles over every four sample indices

**Choice.** `canonical_anchor`, `top_heavy`, `left_heavy`, and `balanced_crossed`
cycle by `sample_index % 4`. Four demonstrations are required; a fifth generated pair
serves as query. Profiles vary dimensions, marker-count asymmetry, ordering, and
palette cardinality.

**Rationale.** A deterministic cycle gives a cheap, inspectable lesson assembly
contract. Every standard four-demo window covers all profiles, and every individual
grid already contains the witnesses needed to refute the declared rivals.

**Rejected alternative.** Pure independent random sampling was rejected because a
correct marginal distribution can still yield semantically weak short lesson windows.

**Probe.** Task tests exhaust starts 0–7 in easy/medium/hard and assert all four profiles
appear in each demo window. The production census checked 300 lessons; query rotation
held out each of the five pairs once, yielding 1,500 unambiguous rotations.

**Failure modes / limitation.** The production census is sampled, and the task-local
exhaustion covers the schedule period plus one repetition, not every seed. New rivals
must be added explicitly to extend the contract.

## D6 — Preserve both canonical palette cardinalities

**Choice.** One profile uses two marker colors (four total colors including background
0 and frame 5); the other profiles normally use three marker colors (five total).
Exact marker-count overrides of three safely reduce a three-color palette to two so
all colors still appear and a repeat remains possible.

**Rationale.** The first repaired draft generated only four-color grids. The after
`dist_gate` correctly rejected that drift because canonical profiles include both four
and five total colors.

**Rejected alternative.** Treat the distribution failure as harmless and waive it.
That would leave a measurable canonical support hole and weaken color-cardinality
robustness.

**Probe.** `test_profile_floor_support_and_palette_breadth_in_every_band` was extended
first, observed failing, then the generator was changed. The red and green logs are
`checks/tdd-red-palette.log` and `checks/tdd-green-palette.log`.

**Failure modes / limitation.** Palettes are profile-owned rather than freely sampled
from all color subsets. This avoids accidental frame/background collisions but does
not cover every color permutation.

## D7 — Make `self_check` the complete strict grammar

**Choice.** `self_check` verifies rectangular shape, 8–18 bounds, ARC integer cells,
full color-5 border, zero non-header interior, legal marker counts/colors, identical
2–3-color sets, and repeated colors on both sides. `strict_canonical_like` delegates
to this same grammar; `MIN_STRICT_FRAC = 1.0`.

**Rationale.** The baseline validator admitted dimensions and structures outside the
intended canonical-like training manifold and mixed explicitly invalid textures into
the ordinary axis domain.

**Rejected alternative.** Maintain a permissive `self_check` and a narrower hidden
strict hook. A single explicit grammar is easier to audit and prevents disagreement
between generation, validation, and semantic checks.

**Probe.** All five canonical inputs pass; 600/600 final semantic draws pass; malformed
border, interior, header-count, color-set, and ragged mutations are rejected.

**Failure modes / limitation.** The strict grammar intentionally rejects some inputs on
which the Racket transformation could still be defined. This is a training-distribution
choice, not a claim about the mathematical domain of the rule.

## D8 — Declare executable rivals, witnesses, and lesson identifiability

**Choice.** Add four wrong-rule rivals: fill every crossing, first top match only,
first left match only, and same-rank only. Add matching witnesses and expose the same
rivals through `LESSON_COMPETITORS`. `lesson_identifiable` rejects a lesson when a
competitor fits all demos but changes the query.

**Rationale.** Correct per-grid labels do not ensure the demonstration set teaches the
intended rule. The audit assignments independently reproduced exactly this class of
failure in other generators.

**Rejected alternative.** Rely only on comments describing rivals. Non-executable
claims cannot be checked across generated lessons or query rotations.

**Probe.** Each generated grid refutes every declared rival; canonical pairs collectively
refute each rival; final semantic gate and 300-lesson census report no ambiguity.

**Failure modes / limitation.** This is a finite rival family. It does not establish
identifiability against arbitrary programs, and duplicate declarations yield eight
reported entries representing four unique behaviors.

## D9 — Keep a portable independent probe for future reviewers

**Choice.** Add `workspace/reference_probe.py` and use
`reviewer_support.find_root`, `canonical_pairs`, and task-relative loading rather than
fixed parent-depth guesses.

**Rationale.** It gives future agents a small reusable oracle and observable-feature
extractors without coupling tests to production helpers or the current checkout depth.

**Rejected alternative.** Import `rule_mirror` in every test. That would make a shared
bug in implementation and test invisible.

**Probe.** The explicit task-test stage snapshots and runs the helper in an isolated
portable runtime; all 19 tests pass there.

**Failure modes / limitation.** The helper exposes canonical labels and therefore must
never be used during visible-only solve episodes. Its module docstring states that
boundary.
