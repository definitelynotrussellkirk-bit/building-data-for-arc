# Working notes: bfef8519fe18

## Current rule and authority

The selected canonical rule is unchanged: color `1` is an immutable wall; every 4-connected non-wall room contains exactly one non-wall seed; every zero in that room is replaced by the seed color. `RULE_HASH = "77ee2c0d890d"`. Final generator version is `2.1.0`, SHA-256 `14855678289a7c71b1095e9d58b7ba75147335038db9c5be69615af451cdc12c`.

## Replaced design

Version `1.1.1` generated only rigid rectangular room matrices `(2x2, 2x3, 3x2)`, declared many controls that were ignored or aliases, did not pin `RULE_HASH`, and validated only that some wall and seed cells existed. Its declared `grid_h/grid_w` values were unprobeable (`valid: auto`), and its singleton position/density axes were not real controls. This made canonical-layout and rectangular-room shortcuts viable and allowed malformed rooms through `self_check`.

The replacement exposes only three honest controls: `grid_h` in `7..14`, `grid_w` in `8..16`, and one of 11 exact `layout` values. All exact controls are observable through `observe_overrides` and reject unknown, mistyped, or out-of-range inputs.

## Distribution and teaching policy

An eight-slot schedule preserves the canonical 7x8 and 8x9 three-room T profiles while alternating regular and irregular partitions. Scheduled layouts include rotated T rooms, a regular cross, dogleg two-room partitions, and dogleg-cross four-room partitions. Plain vertical/horizontal two-room layouts remain exact override controls but are intentionally not default schedule slots. Every cyclic four-pair lesson contains exactly two irregular examples; with any one pair held out, at least one irregular demonstration remains.

Declared semantic rivals are `identity`, `canonical_t_top_only`, and `rectangular_rooms_only`. The latter two fit all three canonical pairs but are refuted by retained irregular-room witnesses. `EXAMPLES_NEEDED=3`, `MIN_STRICT_FRAC=1.0`, and `LESSON_SCHEDULE_PERIOD=8`. The retained witness is `counterexamples/irregular_room_shortcuts.json`; its focused test verifies both canonical shortcuts disagree with the selected rule.

## Validation and performance

`self_check` reconstructs connected rooms, seed counts, border/wall geometry, and supported layout geometry. `rule_mirror` is independently checked against all canonical labels and sampled Racket outputs. The first direct implementation classified a grid by enumerating the complete dogleg-cross wall corpus; this made a fresh maximum-size validation take up to about 2.6 seconds and stalled official lint cohorts. That design was replaced with direct geometry recognition and bounded parameter sampling. The regression test `test_generation_and_analysis_do_not_enumerate_the_full_wall_corpus` forbids the exhaustive helper on the generation/analysis hot path; measured qualification generation is mean 1.91 ms, p95 4.82 ms, max 40.57 ms across 96 draws.

## Decisions and reversals

- **Reversed:** rigid rectangular matrices -> source-bound regular plus dogleg partitions. Reason: canonical-only and rectangle-only rivals fit every canonical pair.
- **Reversed:** broad fictional/alias AXES -> three exact observable controls. Reason: the baseline lint found missing/unprobeable axes, and overrides should be a truthful contract.
- **Reversed:** weak presence-only validation -> complete task-domain reconstruction. Reason: invalid multi-seed, malformed wall, ragged, illegal-color, and unknown-control cases must fail locally.
- **Reversed during implementation:** exhaustive candidate enumeration for classification -> direct geometry recognition. Reason: retained performance failure `checks/counterexample-red.log` and the official lint stall exposed an asymptotic hot path.

## Known limits

The finite rivals do not prove universal rule identifiability. The schedule deliberately omits the plain vertical/horizontal two-room layouts from default production because they add little teaching value; they remain fully supported exact controls. The selected Racket authority was not edited. The post-repair solve was correctly marked as previously exposed to the rule.
## Current reviewer considerations

Source SHA-256: `14855678289a7c71b1095e9d58b7ba75147335038db9c5be69615af451cdc12c`.

# Decisions

## D1 — Preserve the selected authority; repair only the generator

**Choice.** Pin canonical rule hash `77ee2c0d890d`, leave the selected Racket rule and canonical labels unchanged, and make the Python generator/mirror conform to them.

**Why.** All three canonical pairs are internally consistent with connected-component room filling. The defect was in coverage, contracts, and validation—not in the authority.

**Probe.** All canonical inputs pass `self_check` and `strict_canonical_like`; the independent Python oracle and `rule_mirror` reproduce all labels. The task-local qualification tool also matched 24 sampled generated labels against Racket. Evidence: `checks/bfef8519fe18_qualification_racket.json`.

**Rejected alternative.** Changing the rule to match the old rectangular-matrix generator would narrow the task and invalidate lawful canonical/general connected-room behavior.

## D2 — Replace fictional controls with three exact observable axes

**Choice.** Declare only `grid_h=7..14`, `grid_w=8..16`, and 11 named `layout` values. Validate types before generation and expose `observe_overrides` for exact post-generation checks.

**Why.** The baseline declared unprobeable `grid_h/grid_w`, alias palette/texture controls, and singleton position/density controls. A training-control surface should describe behavior callers can actually request and observe.

**Probe.** The focused suite checks every layout at both boundary shapes under all four difficulty values, malformed and unknown overrides, deterministic generation, and global-RNG isolation. The official override matrix accepted 25,920/25,920 draws across 288 cases and three bands with zero findings. Evidence: `checks/after-override-bg/` and `checks/task-tests-final-v2/`.

**Rejected alternative.** Keeping room-height/room-width and palette aliases would expose implementation details without guaranteeing a unique resulting room topology.

## D3 — Use an eight-slot regular/irregular curriculum

**Choice.** Preserve canonical 7x8 and 8x9 T-layout anchors, add rotated T and cross layouts, and alternate them with dogleg two-room and dogleg-cross four-room layouts.

**Why.** The two most plausible shortcuts—“only canonical top-T scenes are valid” and “every room is rectangular”—fit all canonical examples. Irregular walls refute both while preserving the selected law. Alternation ensures every cyclic four-pair lesson has exactly two irregular examples and every held-out query rotation retains at least one irregular demonstration.

**Probe.** `qualify.py` enumerates all eight cyclic starts and every query position. The shared census materialized 300 lessons (100 per band), 1,200 pairs, and 1,200 query rotations: zero production or rotation ambiguity against declared rivals. Evidence: `checks/bfef8519fe18_qualification_racket.json` and `checks/lesson-census-final.json`.

**Rejected alternatives.** Random independent layout draws can accidentally create all-regular lessons. A canonical-only schedule is label-correct but fails to teach the general law. Plain vertical/horizontal two-room layouts are retained as overrides but omitted from production because they do not add a new semantic distinction.

## D4 — Make the semantic contract executable

**Choice.** Declare three rivals, two canonical shortcuts, witnesses for fillable/noncanonical/irregular scenes, and `lesson_identifiable` over demonstrations plus query.

**Why.** Correct individual labels do not establish that a lesson teaches the intended transformation. Named rivals turn the known canonical ambiguity into a replayable gate rather than prose.

**Probe.** Both shortcuts match all three canonical pairs, then disagree with the selected rule on `counterexamples/irregular_room_shortcuts.json`. The retained test binds that witness to final source.

**Limit.** This is finite adversarial coverage, not a proof against all possible hypotheses.

## D5 — Validate the actual domain, not merely color presence

**Choice.** Reconstruct border, walls, connected rooms, seed counts, zero availability, seed distinctness, and exact supported geometry. Reject ragged grids, booleans, illegal colors, broken borders, extra seeds, unsupported layouts, and malformed calls.

**Why.** The old `self_check` passed any rectangular grid containing at least one color-1 cell and one seed, including inputs on which the documented law is undefined.

**Probe.** Focused damage tests plus the official selfcheck, grammar, defect-lint, profile-floor, authority-sync, and rule-smoke stages.

## D6 — Keep exhaustive topology enumeration off the hot path

**Choice.** Retain `_wall_candidates` only as a diagnostic helper; generation samples bounded legal parameters and classification recognizes wall geometry directly.

**Why.** The first repair version rebuilt every possible dogleg-cross wall merely to classify one grid, producing roughly 2.6-second fresh validations at maximum size and stalling an official cohort.

**Probe.** A test monkeypatches `_wall_candidates` to raise and then generates/validates a 14x16 dogleg-cross scene. Qualification measured mean 1.91 ms, p95 4.82 ms, max 40.57 ms over 96 production draws.

**Rejected alternative.** Caching the exhaustive corpus would hide first-call latency and retain avoidable memory/complexity.

## D7 — Build a reusable source-bound qualification probe

**Choice.** Add `workspace/qualify.py`, deriving layouts, rivals, shortcuts, and schedule period from final generator declarations instead of copied lists.

**Why.** Future changes should fail when declarations and tests drift. The probe records generator hash, canonical acceptance, distribution support, cyclic starts, query rotations, retained shortcut counterexamples, timing, and optional Racket parity.

**Known correction.** Its first run incorrectly treated two intentional override-only layouts as missing default support. The final tool separates `scheduled_layouts` from `override_only_layouts`, while the focused tests still exercise all 11 controls.
