# Working notes: 7946249c9684

## Review repair, 2026-10-03

The selected 1.1.0 sampler was much narrower than the authority: 2–3 isolated, distinct-color runs of length at least 3 plus one singleton. It also lacked a `RULE_HASH` pin and declared dead/unprobeable controls. No associated prior-review notes were available.

Version 3.2.0 keeps the Racket authority unchanged and constructively samples exact dimensions, maximal-run count, and palette size. The default curriculum cycles through:

- a strict canonical anchor with run lengths 1, 2, and 3+;
- touching different-color runs plus horizontally connected foreground; and
- separated same-column runs plus repeated colors and an adjacent same-color branch.

Declared canonical-fitting rivals cover global column extremes, nonzero connected-component leaves, same-color component leaves, and global color extremes. A first contact construction did not guarantee adjacency; a later schedule revision still had a cyclic-query ambiguity. Both were fixed before the final source. `workspace/curriculum_probe.py` now rotates all four schedule members into the query position and reads rival declarations dynamically.

Final source SHA-256: `0e39b781378bcd3b94bf4bceb407dc9fc1528c0e4fada003a4a1512c0d3bdf6f`.

Final evidence: 12/12 after-battery stages green; 62 task tests passed; 16,380/16,380 override draws accepted; 300/300 Racket-backed lessons had no declared ambiguity; 1,200/1,200 cyclic rotations and 486/486 joint override cases passed. Finite rival coverage is not universal induction, and the supported domain is intentionally bounded.
## Current reviewer considerations

Source SHA-256: `0e39b781378bcd3b94bf4bceb407dc9fc1528c0e4fada003a4a1512c0d3bdf6f`.

# Decisions — 7946249c9684

Final generator version: `3.2.0`
Final SHA-256: `0e39b781378bcd3b94bf4bceb407dc9fc1528c0e4fada003a4a1512c0d3bdf6f`
Canonical rule pin: `ab25d2969132`

## D1 — Keep the selected Racket authority unchanged

**Input / observation.** The canonical examples and selected rule agreed on a simple column-local transformation: for each maximal same-color nonzero vertical run, preserve the first and last cells and erase only the interior. Length-1 and length-2 runs are unchanged.

**Decision.** Change the sampler and its review contract only. Pin `RULE_HASH = "ab25d2969132"`; do not edit the Racket source or canonical data.

**Why.** Rule smoke already showed the authority executed, and the defect was that the generator represented only a narrow subset of its lawful domain. Changing the rule would have obscured the actual teaching defect and increased acceptance risk.

**Alternative rejected.** Narrow the authority to “2–3 long isolated bars.” That would match the old sampler but contradict canonical length-1/length-2 examples and discard lawful behavior.

**Probe / outcome.** Final rule smoke: 120/120 fired, 0 crashes; authority sync passed. See R7 in `REVIEW.md`.

## D2 — Replace decorative axes with four exact observable controls

**Baseline.** Version 1.1.0 declared nine nominal controls, but generation actually drew its own bar count and colors. `position_bias` and `density` were unprobeable single-token axes; helpful textures were dead; degenerates overlapped the ordinary texture domain.

**Decision.** Advertise only:

- `grid_h` in 6..12;
- `grid_w` in 7..12;
- `n_runs` in 3..8;
- `palette_size` in 2..3.

Each override is validated for unknown keys, exact integer type, and range. `observe_overrides` measures the realized grid rather than trusting request metadata.

**Why these bounds.** Width 7 can still host the maximum eight runs by using one separated two-run column; height 6 is enough to create two separated runs or two touching color runs plus a nontrivial length-3 run. Two or three colors are enough to exercise repeated colors and color-boundary behavior without adding a color-count axis the semantic curriculum cannot reliably teach.

**Alternatives rejected.** Keeping aliases such as `palette_kind` or `texture` would preserve UI surface without observable semantics. Supporting 1 run or 1 color would weaken every three-example lesson and remove the main rival witnesses. Wider ranges were unnecessary for the repair and would expand the override matrix without new rule behavior.

**Failure modes considered.** Boolean values are Python integers but are rejected by exact type checks. Unknown axes fail rather than being swallowed. Every joint boundary/interior case is constructed, not sampled until success.

**Probe / outcome.** Shared override contract: 16,380/16,380 accepted; local joint matrix: 486/486 accepted and exactly observed.

## D3 — Use construction rather than capped rejection sampling

**Decision.** Build vertical runs as explicit `(column, start, end, color)` tuples, paint them once, and validate the resulting maximal runs.

**Why.** Exact `n_runs` and `palette_size` are combinatorial constraints. Randomly dropping bars and retrying would create hidden bias, nontermination risk, and override failures near `width=7, n_runs=8`.

**Alternative rejected.** Generate random cells then segment them. That makes accidental merges common and turns an exact-control contract into a probabilistic claim.

**Probe / outcome.** No override rejections, exceptions, or mismatches in the 16,380-draw shared audit. Task tests cover every advertised scalar value and malformed control class.

## D4 — Preserve strict canonical anchors

**Decision.** One profile in every three-example cycle uses an exact public shape from `(7×7, 8×8, 6×9, 7×9)`, three distinct colors, separated columns, and run lengths 1, 2, and at least 3.

**Why.** The old sampler omitted canonical short runs. A canonical anchor keeps the generated curriculum connected to the public examples and makes identity behavior on short runs explicit.

**Alternative rejected.** Make every sample adversarial. That would improve rival rejection but drift away from public morphology and fail the strict profile floor.

**Probe / outcome.** All 4 canonical inputs pass `self_check`; strict canonical-like rate is 193/600 = 32.17%, above the 25% floor, with hits in every band.

## D5 — Teach four canonical-fitting rival distinctions

The four declared rivals are read by both shared and local tools:

1. `column_extremes`: keep only the globally first/last nonzero cell in each column, ignoring run/color boundaries.
2. `nonzero_component_leaves`: treat all orthogonally connected foreground as one component and keep only vertical leaves.
3. `same_color_component_leaves`: merge orthogonally connected cells of the same color before selecting leaves.
4. `global_color_extremes`: for each color, keep its globally topmost and bottommost rows, ignoring separate runs.

**Decision.** Declare the same callable map as `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, plus one executable witness for each distinction.

**Why.** All four fit all four canonical pairs, so canonical compatibility alone cannot distinguish them. They cover independent failure modes: same-column separation, touching color boundaries, connected objects, and color reuse.

**Alternative rejected.** Declare only the obvious column-extremes rival. During self-review, component-based rules also fit the public examples and exposed gaps in the first curriculum design.

**Probe / outcome.** The semantic gate confirms all four fit canonical pairs and every witness claim holds on 60/60 checked fired examples. The 300-lesson Racket-backed census refutes each rival in every lesson.

## D6 — Use a three-profile cyclic curriculum

**Decision.** `SCHEDULE_PROFILES = (canonical, boundary_contact, separated_stacks)` and `EXAMPLES_NEEDED = 3`.

**Rationale.** Three demonstrations are enough to include one public anchor and two complementary adversarial constructions. The schedule is deterministic by `sample_index`, so lesson assembly and cyclic starts are inspectable.

**`boundary_contact`.** Two differently colored runs meet vertically in one column. An adjacent bridge is chosen constructively, not randomly, so the foreground and same-color component shortcuts are exercised. Extra runs realize the third color and requested count.

**`separated_stacks`.** At least two same-column runs are separated by background, while an adjacent same-color run and repeated colors create independent endpoints. It was strengthened so it can refute every declared rival even if `boundary_contact` becomes the held-out query.

**Rejected intermediate design.** The first contact implementation chose columns independently, so horizontal adjacency was possible but not guaranteed. A later first schedule revision passed nonrotated lessons but left a rival alive when the boundary profile itself was the query. Both were treated as defects and repaired before the final source.

**Probe / outcome.** `workspace/curriculum_probe.py` rotates all four consecutive instances through the query position. Across 1,200 rotations, all rivals are refuted and `lesson_identifiable` returns no failures.

## D7 — Keep exact overrides lawful even when they cannot realize every semantic witness

**Decision.** Honor every legal axis combination exactly. For `n_runs=3, palette_size=3`, use all three colors even though this prevents repeated-color evidence in that one grid. Do not falsely declare the combination incompatible.

**Why.** The requested measurements are internally consistent: an exact 3-run, 3-color grid exists and obeys the authority. Semantic witnesses are lesson-level requirements, not a promise that every individual override grid contains every contrast.

**Alternative rejected.** Reject `3×3` as incompatible solely to simplify the repeated-color witness. That would make the control contract less honest.

**Probe / outcome.** The exact edge is included in both shared and local override matrices. Ordinary default profiles use at least four/five runs where repeated-color evidence is required.

## D8 — Pair fast task-local probes with Racket-bound evidence

**Decision.** Add `workspace/curriculum_probe.py` and 62 portable tests. The probe dynamically reads rival declarations, verifies canonical fit, rotates query positions, and checks a 486-case joint override matrix. It uses `_intended_output` only as a task-local mirror.

**Why.** The shared lesson census is authoritative but deliberately does not rotate every pair. The local probe makes the small deterministic schedule exhaustively inspectable without invoking Racket thousands of extra times.

**Limitation.** A Python mirror can share an implementation misconception with the generator. Therefore its conclusions are accepted only alongside Racket rule smoke, authority sync, exact Racket witnesses, and the 300-lesson Racket-backed census.

## D9 — Make `self_check` validate the lawfully advertised domain

**Decision.** Validate rectangular dimensions, color domain, exact run count/palette count, at least one length-3+ run, and profile-specific semantic contracts when profile metadata is available. Keep canonical length-1 and length-2 runs lawful.

**Alternative rejected.** Retain the old check “2–3 bars of length ≥3, distinct columns/colors.” It encoded the sampler shortcut as if it were the task law and rejected canonical examples.

**Probe / outcome.** Self-check battery green; all canonical pairs accepted; malformed/task-local cases covered in tests.

## Domain limits and stopping rule

The final sampler is intentionally not universal. It excludes blank grids, purely horizontal grids, one-color and one-run cases, grids above 12×12, and more than eight runs. Those may be lawful under the authority, but adding them would enlarge the scope without improving the four identified distinctions. I stopped after the complete after battery, task tests, 300-lesson Racket census, cyclic rotation probe, exact Racket witness, fresh solve, and two required audits all completed with no repair blocker.
