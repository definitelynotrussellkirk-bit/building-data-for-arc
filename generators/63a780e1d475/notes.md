# Working notes: 63a780e1d475

## Current rule

For every consecutive pair of blue (`1`) cells aligned in a row or column, if the pair is separated by at least one cell and every interior cell is background (`0`) in the **original input**, paint the complete inclusive segment red (`2`). Horizontal and vertical candidates are both determined from the original input; a horizontal paint may therefore cross a vertical paint without blocking it.

Canonical authority remains rule hash `b3ad5e9b6be9`. The Racket behavior was not changed in this review. The duplicated selected source fields in `shared/data/base/solutions/banks/e57147319d67/E31__63a780e1d475.json` were synchronized byte-for-byte to remove comment-only authority drift.

## Reversed prior decisions

The imported `2.0.1` generator emitted only horizontal endpoint pairs, painted only the interior red, left endpoints blue, accepted inert/fictional controls, and did not pin `RULE_HASH`. Those choices contradicted canonical rows and columns and the canonical inclusive recoloring. Version `3.0.0` replaces that sampler rather than preserving its restricted grammar.

## Distribution and curriculum

- Dimensions: `grid_h=8..14`, `grid_w=9..14`; the default five-shape cycle includes every canonical shape.
- Pair count: `n_pairs=2..4`. Difficulty changes the default count schedule: easy `(3,2,3,2)`, medium `(3,3,4,2)`, hard `(4,4,4,3)`.
- Orientations: exact modes are `horizontal_only`, `vertical_only`, `mixed_clear`, and `mixed_crossing`.
- The production mode cycle is crossing, horizontal-only, crossing, vertical-only. Combined with the five-shape cycle, the declared schedule period is 20.
- Four demonstrations are required. Two crossing slots per four-mode cycle ensure that every five-pair lesson, under every query rotation, retains a crossing witness in its demonstrations.
- Endpoint incidences are disjoint. This prevents accidental extra alignments and makes `n_pairs` and `orientation_mode` directly observable.

`mixed_clear` is retained as an exact override for domain coverage, but is not in the default teaching cycle: adding it to a four-slot default would weaken the guaranteed crossing witness unless the lesson length or schedule were enlarged.

## Validation and semantic contract

`self_check` rejects malformed/ragged grids, non-integer colors, out-of-range shapes, no-span inputs, lone or multiply-used endpoints, ambiguous extra alignments, and inputs outside the 2–4 pair grammar. Unknown, mistyped, out-of-range, or retired overrides fail loudly. `observe_overrides` recovers all four advertised controls from pixels.

The declared rivals are: sequential row-then-column clearance, horizontal-only, vertical-only, interior-only, first span per orientation, and identity. The strongest canonical-fitting rival is sequential row-then-column clearance: all canonical spans are noncrossing, so it fits all five canonical pairs. The retained crossing counterexample is `counterexamples/sequential_block_crossings.json`.

## Final evidence

Final generator SHA-256: `1c6135766e9d7927f66c2632705fcb9b70101964c83d075c8fa09938767c3aa1`.

- Full after battery: 12/12 stages green (`checks/after/checks/63a780e1d475_after_battery_summary.json`).
- Task-local contract: 69/69 tests passed; the schedule test enumerates all 20 cyclic starts, all five query rotations, all three bands, and eight seeds (`checks/task-tests-final2/result.json`).
- Lesson census: 300/300 lessons, 1,500 labelled pairs, 1,500 query rotations, zero ambiguity or scoring errors against declared rivals, 1,496 unique inputs (`checks/lesson-census.json`).
- Post-repair visible-only solve: one revision, all four visible examples passed, earlier rule exposure declared yes, no reference consulted during the solve (`solve/summary.json`).

## Known limits

The generated domain fixes the canonical color roles (background 0, endpoint 1, output 2), uses only disjoint endpoint incidences, and does not sample blocked interiors or chains where one blue cell belongs to multiple candidate pairs. These restrictions make the lesson grammar unambiguous but do not cover every input the canonical Racket function could accept. The finite rival census is evidence against the declared hypotheses, not a proof of unique induction against every possible rule.
## Current reviewer considerations

Source SHA-256: `1c6135766e9d7927f66c2632705fcb9b70101964c83d075c8fa09938767c3aa1`.

# Decisions: 63a780e1d475

## D1 — Replace, rather than extend, the imported horizontal-only sampler

**Prior choice:** emit horizontal blue endpoint pairs, paint only interior cells red, and leave endpoints blue.

**Decision:** implement the canonical row-or-column inclusive-span rule from a clean construction.

**Reason:** all five canonical outputs recolor endpoints; four canonical training pairs contain one horizontal and one vertical span, and the canonical test contains two horizontal plus one vertical span. Patching the old sampler incrementally would preserve its wrong grammar and misleading controls.

**Probe/evidence:** canonical ownership and independent mirror assertions in `generators/63a780e1d475/tests/test_generator_contract.py`; final rule smoke in `checks/after/`.

**Rejected alternative:** retain the old generator and merely add vertical examples. This would still teach interior-only recoloring and retain dead controls.

## D2 — Use disjoint endpoint incidences and constructive placement

**Decision:** every generated blue cell belongs to exactly one horizontal or vertical span; accidental additional alignments are forbidden.

**Reason:** `n_pairs` must be pixel-observable, and the semantic witnesses should arise from intended relations rather than accidental triples or shared endpoints. Constructive placement gives deterministic success on the smallest supported shapes without rejection-heavy sampling.

**Failure mode avoided:** three blue cells in one row/column can create multiple consecutive candidate spans, while a shared endpoint can make orientation/count metadata ambiguous.

**Known limitation:** the canonical Racket function may act on broader arrangements. Shared endpoint chains and blocked interiors are outside this generator’s teaching grammar.

## D3 — Keep four orientation modes but teach with a crossing/single-axis cycle

**Decision:** support exact overrides for `horizontal_only`, `vertical_only`, `mixed_clear`, and `mixed_crossing`. Use the default four-slot mode cycle:

1. `mixed_crossing`
2. `horizontal_only`
3. `mixed_crossing`
4. `vertical_only`

**Reason:** crossings refute the strongest canonical-fitting sequential-clearance rival. Pure horizontal and pure vertical slots prevent a reverse shortcut that the rule only applies in mixed or crossing scenes.

**Rejected alternative:** put `mixed_clear` into the four-slot default. With four demonstrations and one query, that can remove the guaranteed crossing witness under some query rotations unless the cycle or lesson length grows. `mixed_clear` remains exactly reachable for domain checks.

**Probe/evidence:** `counterexamples/sequential_block_crossings.json`; exhaustive schedule/query test; `checks/lesson-census.json`.

## D4 — Require four demonstrations and declare a 20-slot period

**Decision:** `EXAMPLES_NEEDED=4`, with one query, and `LESSON_SCHEDULE_PERIOD=20`.

**Reason:** four demonstrations in any five-consecutive-pair window preserve witnesses for all six named competitors after any one pair is held out. The shape cycle has length five and the semantic mode/count cycle length four; their combined period is 20.

**Verification:** the final task test checks all 20 starts × 5 query positions × 3 bands × 8 seeds. The broader census checks 300 production windows and 1,500 rotations.

**Limitation:** finite declared-rival checks cannot establish unique induction against arbitrary programs.

## D5 — Make difficulty affect pair count, not rule semantics

**Decision:** easy `(3,2,3,2)`, medium `(3,3,4,2)`, hard `(4,4,4,3)`.

**Reason:** shape and orientation are needed in every band for profile coverage and semantic witnesses. Pair count is the safest monotone complexity knob: harder examples contain denser relation sets without changing the rule or removing exact control support.

**Failed iteration retained:** the first repair used the same count schedule for every band. A newly added regression test failed, exposing `difficulty` as a dead knob; the band schedules fixed it.

## D6 — Anchor canonical shapes while allowing a bounded rectangle domain

**Decision:** defaults cycle through `(8,9)`, `(9,9)`, `(8,10)`, `(10,10)`, and `(9,10)`, while overrides allow heights 8–14 and widths 9–14.

**Reason:** every band must hit canonical-size profiles, but exact controls should also cover nearby rectangles. These minima can construct all four modes with four disjoint pairs.

**Rejected alternative:** unrestricted random dimensions. It weakens deterministic profile coverage and makes the smallest mixed-crossing cases harder to guarantee.

## D7 — Pin strict controls and reject legacy knobs

**Decision:** only `grid_h`, `grid_w`, `n_pairs`, and `orientation_mode` are accepted. Unknown keys, booleans masquerading as integers, strings, floats, out-of-range values, and old `texture`/`palette_kind` controls fail loudly.

**Reason:** the baseline override battery showed thousands of mismatches and generation errors because metadata advertised controls the implementation did not honor. Silent coercion would make those defects harder to detect.

**Evidence:** final override stage exercised 15,120 draws with no findings or warnings; `unknown_key_verdict=rejected`.

## D8 — Preserve the canonical Racket behavior

**Decision:** do not alter the executable rule. Synchronize the selected nested `target_code` field to its corresponding `raw_code` solely to remove comment-only exact-source drift.

**Reason:** canonical outputs and rule hash `b3ad5e9b6be9` were already correct; the defect was in the generator and duplicate authority representation.

**Evidence:** final rule smoke and authority sync pass; execution parity remains `PASS`.

## D9 — Retain explicit rivals and witnesses as reusable authoring tools

**Decision:** expose a pure Python `rule_mirror`, six semantic rivals, five witness predicates, override observation, and a `lesson_identifiable` hook.

**Reason:** future edits should fail at the semantic contract rather than merely preserve valid-looking pixels. Named rivals cover original-input crossings, one-axis-only rules, interior-only painting, first-per-orientation painting, and identity.

**Limit:** this set is deliberately small and plausible; it is not an enumerator of all ARC hypotheses.
