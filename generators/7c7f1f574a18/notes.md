# Working notes: 7c7f1f574a18

## Current native parametric candidate — 2026-10-24

The separate `workspace/parametric/` candidate varies `min_hole_area` over 1, 2
and 3. Threshold 1 returns the exact canonical program; other thresholds retain
the solid-bbox exception and compare the largest enclosed four-connected gap
region with the threshold before docking. Equal-bbox/equal-area pocket partitions
make this intermediate necessary; bent, vertical and diagonal-leak cavities
teach topology rather than a horizontal-run shortcut. See the workspace README
for the complete grammar, commands, visibility contract and limitations.

The minimum two-demo sampler now guarantees different backgrounds and multiple
foreground colors after a source-bound seed-14 review exposed a color-only
shortcut. All four query profiles are generated independently of the private
setting and end at a substantive seven-object 30×30 scene. No production size
override or canonical-source change is claimed. Native owner acceptance remains
a separate exact-source handoff after reviewer qualification. Current evidence: 78 focused tests passed; native qualification covers all three settings at seeds 0/17; the two causal witnesses replayed in protected Racket. The minimum-two-demo self-review found no query-discriminating survivor among its finite declared rivals.

## Review outcome — 2026-10-03

The pinned baseline (`4a3b30e70bdfa808d83735af676176c37b752c2776bdb168c7c0c8fbc2904275`) reduced the rule to solid rectangles versus corner-notched rectangles. It also advertised dead or inaccurate axes, omitted `RULE_HASH`, generated no canonical background-4 profile, used a weak structural self-check, declared no executable teaching contract, and left selected `target_code` text out of sync with canonical authority.

The selected implementation was rewritten rather than incrementally patched. It now mirrors the canonical topology law independently in Python, generates both closed subtypes plus an open boundary-gap object in every ordinary scene, crosses input-side roles, exposes five observable exact controls, pins `e048ab46f343`, and synchronizes the selected base-solution `target_code` to the canonical Racket source. The archival `raw_code` remains intentionally unchanged and behaviorally equivalent.

TDD evidence retained under `checks/`:

- initial regression suite: 25 failed / 5 passed;
- first implementation: 30 passed;
- scale regression: 1 failed / 30 passed because generated maximum component size was 9 versus the canonical median near 16;
- widened motifs: 31 passed;
- reusable census tool missing/import-path failures: retained;
- final task-local suite: 32 passed.

Final official battery: 12/12 stages green on generator SHA-256 `27d4ef0b4f69c061c19b98ecb426edae19013204771b4b34c4a6e47ad9c5902f`. The source-bound census sampled 100 lessons per band (300 lessons, 1,200 unique inputs): zero invalid inputs, zero unidentifiable lessons, every declared witness fired on every input, and every declared rival disagreed with the independent oracle on every input. This is finite evidence against the declared rivals, not a proof of universal ARC induction.
## Current reviewer considerations

Source SHA-256: `27d4ef0b4f69c061c19b98ecb426edae19013204771b4b34c4a6e47ad9c5902f`.

# Decisions — `7c7f1f574a18`

Each decision records the observed baseline choice, its rationale when recoverable, the selected alternative, the probe used, and remaining limitations.

## D1 — Treat bounding-box gap connectivity as the defining law

**Baseline choice and rationale.** The baseline described closed objects as solid rectangles and open objects as rectangles missing a corner. No retained note explained why those two morphologies were treated as the full domain; the likely rationale was implementation simplicity.

**Decision.** Implement the canonical distinction directly: a component is closed if its bounding box is full or contains at least one gap region disconnected from the bounding-box boundary; otherwise it is open.

**Alternatives rejected.** “Solid versus non-solid” fails on canonical hole-bearing closed objects. “Has any bbox gap versus no gap” misclassifies broken frames. Flood-filling from the whole grid boundary was rejected because the canonical property is local to each object's bounding box.

**Probe.** All five canonical pairs are asserted in `tests/test_generator_7c7f1f574a18.py`; the independent census recomputes topology without calling `rule_true`.

**Limit.** Components are same-colour and 4-connected; the generator does not teach mixed-colour or diagonal-object variants because the selected Racket rule does not define them as one object.

## D2 — Put three answer-bearing morphologies in every ordinary scene

**Baseline choice and rationale.** The baseline sampled solid rectangles and corner notches. This supplied one positive and one negative class but no distinction between solidity and genuine closure.

**Decision.** Always include (1) an irregular hole-bearing closed object, (2) a solid closed object, and (3) an open almost-ring whose gap reaches the bbox boundary. Optional components repeat a class without removing the core witnesses.

**Alternatives rejected.** Random polyomino generation was considered but rejected because rejection sampling obscures exact controls and can produce lessons without the needed contrast. Using only ring versus broken ring was rejected because “closed means has a hole” would survive.

**Probe.** Each declared witness fires 600/600 times in the official semantic census and 1,200/1,200 times in the large task-local census. `solid_only_closed` and `holes_only_closed` each disagree 1,200/1,200 times.

**Failure mode.** Fixed motif families can create morphology recognition shortcuts. The irregular tab and palette/size variation reduce this risk but do not eliminate every shape-specific heuristic.

## D3 — Cross source side with destination side

**Baseline choice and rationale.** Positioning varied, but no retained evidence guaranteed that starting side was independent of class.

**Decision.** Force a closed object to begin on the right and an open object to begin on the left in every ordinary scene. Destination remains determined only by topology.

**Alternatives rejected.** Pure random placement can accidentally leave whole lessons consistent with “move to the nearest edge” or “preserve side.” Alternating by sample index would still create per-example regularity.

**Probe.** `crossed_starting_sides` fires on every sampled input; the `starting_side` rival disagrees on 1,200/1,200. The row-preservation regression also checks that only columns move.

**Failure mode.** Because crossed roles are guaranteed, a learner could use a more specific conjunction of motif identity and side. Additional morphology families would be needed to refute every such conjunction.

## D4 — Use separated row bands

**Baseline choice and rationale.** The baseline separated object rows, plausibly to avoid post-docking overlap.

**Decision.** Preserve that useful invariant explicitly: component row spans do not overlap. Horizontal docking therefore has an unambiguous, order-independent output.

**Alternatives rejected.** Allowing shared rows without defining collision precedence would make valid inputs whose Racket output overwrites cells depending on traversal order. Adding collision semantics would change the task rather than improve its data.

**Probe.** `self_check` rejects overlapping row spans, and generated Racket outputs show zero out-of-bounds results or mutations across 120 smoke applications.

**Limit.** The data does not train learners to reason about multiple objects sharing rows, even when their docked footprints would remain disjoint.

## D5 — Match canonical scale while retaining controlled variation

**Baseline choice and rationale.** Baseline dimensions were mostly 12–18 and objects were small. No note tied those ranges to canonical data.

**Decision.** Use heights 19–24 and widths 19–26, with every third default draw anchored at height 22 and one of the five canonical widths 19/21/22/24/26. Enlarge the primary motifs to 17 cells.

**Alternatives rejected.** Exact replay of canonical inputs would maximize profile hits but harm novelty. Broad 9–30 dimensions were rejected because the canonical task supplies no evidence for very small or maximal canvases and profile support would dilute.

**Probe.** The first rewrite failed a scale regression at max object size 9 (`checks/tdd-scale-red/result.json`). Final profile floor is 21/60 exact and every band has support; final census spans the declared ranges and has 1,200 unique inputs.

**Limit.** Maximum object size is fixed at 17 in the current motifs. Future work could vary ring width/height while preserving the same topological witnesses.

## D6 — Mix canonical, binary, and multicolour palettes

**Baseline choice and rationale.** Baseline always used background 0 despite canonical background 4, and advertised palette controls that were not realized consistently.

**Decision.** Expose one exact `palette_profile` axis: `canonical` uses background 4 / foreground 1; `binary` varies one foreground color; `multicolor` gives distinct component colors. Default anchors guarantee canonical palette support while non-anchor draws teach color invariance.

**Alternatives rejected.** Always canonical palette encourages a literal 1→2/3 heuristic. Fully random palette without anchors failed the profile requirement and weakens source similarity.

**Probe.** All exact controls are observed in task tests and 16,740 official override draws. Large-census palette size spans 2–4 and foreground colors span 1–3.

**Failure mode.** Output colors are necessarily fixed at 2 and 3 by the task; those colors may also appear as input foreground colors in noncanonical profiles, which is legal but can be visually confusing.

## D7 — Replace nine weak controls with five exact controls

**Baseline choice and rationale.** The baseline exposed grid size, object count, palette aliases, colors, bias, asymmetry, and texture/degenerate flags. Many were dead, constrained inconsistently, or not observable.

**Decision.** Keep only controls with stable semantic meaning and a deterministic observer: `grid_h`, `grid_w`, `n_closed`, `n_open`, and `palette_profile`. Reject unknown keys and invalid values before drawing.

**Alternatives rejected.** Keeping compatibility aliases would perpetuate silent fallbacks. Declaring many structured incompatibilities was rejected because the simpler domain makes every Cartesian cross feasible.

**Probe.** Before override evidence records 15,095 findings; after evidence records 16,740/16,740 accepted draws and no findings.

**Limit.** There is no direct “motif family” axis because only one fully tested family per semantic witness is currently implemented.

## D8 — Make validation semantic, not merely structural

**Baseline choice and rationale.** Baseline `self_check` mostly counted nonzero cells and shapes; it accepted all-closed/full-grid impostors and supplied no independent rule mirror.

**Decision.** Validate ARC shape/value constraints, unique modal background, class presence/counts, row separation, legal dimensions, output noncollision, and exact controls. Add `strict_canonical_like`, independent `rule_true`, four witnesses, five executable rivals, and `lesson_identifiable` with three demonstrations.

**Alternatives rejected.** Comparing generated outputs only to the Racket rule would test execution but not teaching quality. Static witness names without callables were rejected because they cannot be measured.

**Probe.** Official semantic gate: strict 208/600, witnesses 600/600, 12/12 lessons identifiable. Task-local census: 300/300 lessons identifiable.

**Limit.** Validation cannot prove universal identifiability; it only establishes the declared contract over sampled lessons.

## D9 — Synchronize selected authority but preserve archival source

**Baseline choice and rationale.** The selected base record contained canonical-equivalent Racket in `raw_code` and a textually different selected `target_code`. The historical reason for divergence is unknown.

**Decision.** Copy canonical `program_solution` exactly into `racket_target.target_code`, because that field is active selected authority. Leave canonical source and archival `raw_code` unchanged.

**Alternatives rejected.** Rewriting canonical authority was unnecessary and riskier. Deleting archival code would destroy provenance.

**Probe.** Authority sync reports selected exact-group count 1 and execution parity across both distinct retained sources, each solving 3/3 train and 2/2 test pairs.

**Limit.** The report remains `selected_synchronized_archival_divergent` by design because archival `raw_code` is preserved; this is nonblocking and explicitly classified.

## D10 — Add a reusable large lesson census

**Baseline choice and rationale.** No task-local tool existed. The official gate intentionally samples only 12 lessons as a smoke test.

**Decision.** Add `workspace/semantic_census.py`, using an independent oracle and the generator's actual competitor/witness declarations. Pin formulas, hashes, counts, and domain limits in JSON.

**Alternatives rejected.** Calling `generator.rule_true` would make the probe circular. Hard-coding rival names in the tool would silently drift from declarations. Running Racket for all 1,200 inputs was unnecessary because Racket parity is already checked by the official battery.

**Probe.** The tool has a portable subprocess regression and produced `checks/semantic-census/report.json`: 300 lessons, 1,200 unique inputs, zero invalid or unidentifiable.

**Failure mode.** The fixed deterministic seed schedule can miss rare branches. A future shared gate should rotate a recorded seed window while retaining a stable minimum corpus for regression.
