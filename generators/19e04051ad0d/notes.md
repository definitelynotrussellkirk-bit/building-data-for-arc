# Working notes: 19e04051ad0d

## Review review-12bfd50e9b774ba3 — version 3.1.0 → 3.2.0

- Baseline generator SHA-256: `769ab701b32aa455b835a1154b7b7a528cb34fa93cf2f1328eab3072ad892a4d`; final: `cd05f83c1e193c864f8c748791945a3b09c58a6de3cb5247154cf225d188d482`.
- Reproduced 60 strict-scalar aliases plus a canonical/generated structural mismatch. `bg_color=9.75` was accepted as 9; explicit `layout=None` also changed the domain.
- Added exact request validation, strict background-color drawing, a sparse connected-mask profile, and a sparse palette-neutral canonical-morphology profile. `RULE_HASH` and Racket authority are unchanged.
- Final staged task tests: 55/55. Final battery: 12/12 green. Defect lint: FLAGGED 0. Profile floor: 26/60 exact hits with support in every band.
- Required census: 300 three-demo-plus-query lessons, 0 production ambiguity; 1,200 required rotations, 0 ambiguity; 1,197 unique exact inputs.
- Isolated proposal: `workspace/parametric/` implements immutable `next|previous` cycle direction with exact Racket programs; it is not part of production approval.
- Self-review limit: the two canonical morphologies are fixed and sparse; the finite rival census does not prove resistance to every future topology memorizer.
- Prior evidence lead: `evidence/review_index.json` and retained review `review-d26ef983b50430a9`; all current claims were rechecked on assigned bytes.

## Review review-d26ef983b50430a9: version 3.0.0 -> 3.1.0

The previous rejection of every ascending numeric color cycle accidentally
restricted all scenes to the complementary descending cycle. For three distinct
colors, the spatial-next rule then equals the numeric-predecessor rule. That
rival fits all six usable canonical pairs (three unique canonical inputs), and
matched 600/600 baseline diagnostic samples. Rejecting a rival on every single
input can therefore create an equally simple complementary shortcut.

The repair samples ascending and descending cycles by sample-index parity,
with a keyed-random choice of the three rotations within each orientation.
Seed is deliberately excluded from parity because advancing seed and index
together would otherwise collapse the schedule. Three consecutive accepted
inputs see both orientations; the empirical production census confirms that
rejection/duplicate skipping did not disturb the schedule in 300 lessons.

The reverse-numeric rival is now declared and is the only entry labeled a
canonical shortcut. The seven other old hypotheses are retained as ordinary
semantic/lesson competitors. Numeric-color witnesses are conditional on the
input, while complete lessons must supply both directions' discriminators.
`lesson_identifiable` now returns malformed-pair reasons before evaluating any
rivals, avoiding a KeyError when the first demonstration is missing its fields.

## Distribution choices retained

The task grammar remains height 8..12, width 7..9, the same fourteen layouts,
three distinct region colors, a uniquely modal background, independently keyed
hole masks, visible foreground in every region-column, and at least two holes
per region in the strict domain. Difficulty continues to affect height/layout
frequencies and hole fractions, not the legal override range. Ordinary `222`
layouts remain excluded to disprove fixed-boundary rules, but `layout="222"`
remains an exact accepted override. Broader shapes and ordinary equal-width
mixing are possible follow-ups, not changes silently included in this repair.

All 700 advertised joint axis combinations were exercised at both schedule
phases in all three difficulty bands: 4,200/4,200 distinct, strict-valid inputs,
with exact observations. Both numeric rivals fit exactly one phase for every
combination. This is exhaustive over those finite controls at one seed, not
over all seeds, masks, or palettes.

## Authority and measurements

Canonical labels and the semantic RULE_HASH are unchanged. Two selected backing
solution JSON files had whitespace-only raw_code/target_code disagreement with
the exact canonical source; those fields were synchronized. No Racket algorithm
was changed. The before battery had eleven green stages and an authority-sync
failure; all twelve after stages are green.

Final generator SHA-256:
`769ab701b32aa455b835a1154b7b7a528cb34fa93cf2f1328eab3072ad892a4d`.

Retained evidence at packet root includes:
- `checks/color-cycle-before.json`, `checks/color-cycle-final.json`: source-bound
  600-input probes at seed 600123, indexes 0..199, each of three bands. Final
  predecessor accuracy is 300/600, with zero survivors in 594 overlapping
  three-demonstration windows. All six relative orders appear in each band.
- `checks/lesson-census.json`: 100 production lessons per band, 1,200 unique
  inputs and materialized Racket labels, no errors, rejections or declared
  ambiguities. Seeds and starts are recorded for every lesson.
- `checks/cyclic-query-final.json`: all four query rotations of each lesson,
  1,200 rotations, zero rival survival/ambiguity, zero Python/Racket mismatches,
  and zero source replay mismatches. Seventeen namespaced declarations represent
  eight distinct rival hypotheses; they are not seventeen independent rivals.
- `checks/joint-axes-final.json`, `checks/after/`, `checks/task-tests/` and
  `checks/repository-tests-console.log`: input controls, twelve-gate battery,
  portable focused tests, and 273 passing repository tests.

The direct task suite has 15 unique tests. The portable runtime additionally
maps the pre-existing task test file to a root fixture path, so its 22 passes
include seven duplicate executions, not 22 independent tests.

## Self-review and remaining limits

Balancing the two cycle orientations removes a numeric-order restriction but
introduces a visible period-two lesson composition; a learner given generation
metadata could exploit that schedule, so metadata must not enter puzzle inputs.
The 300 production lessons and every cyclic query placement defeat the eight
declared rivals, but neither these finite checks nor the intentionally narrow
shape/layout grammar establishes identifiability against all possible rules.

Imported `evidence/associated_notes.jsonl` was used only as a lead, notably
GNOTE004169/GNOTE004172 from local-random-95d5c03ca568 (gpt-5.6-sol). No prior
return ZIP or its measurements was reused. The inherited anti-fixed-width and
anti-ascending-color rationales were re-examined against the pinned baseline.
## Current reviewer considerations

Source SHA-256: `cd05f83c1e193c864f8c748791945a3b09c58a6de3cb5247154cf225d188d482`.

# Decisions for review-12bfd50e9b774ba3

## Scope and prior evidence

The selected approved generator was task `19e04051ad0d`, baseline version 3.1.0 and SHA-256 `769ab701b32aa455b835a1154b7b7a528cb34fa93cf2f1328eab3072ad892a4d`. I used the existing `evidence/review_index.json`, prior notes, canonical pairs, and retained probes to understand the current design, but reproduced current defects on the assigned bytes before changing source. The canonical Racket rule was treated as authority throughout.

The packet had no Git metadata. I therefore used exact baseline/current hashes, test-first receipts, generated patch inventory, and fresh-return replay as the reproducibility boundary.

## D1 — reject scalar aliases at the public request boundary

**Decision.** Validate `seed`, `sample_index`, `difficulty`, and declared overrides before constructing `GenCtx`; require exact Python scalar types and preserve `None` as no override. Use `draw_color_strict` as defense in depth.

**Why.** The baseline accepted booleans, floats, strings, a negative index, and unsupported difficulty values. `bg_color=9.75` silently became 9. These aliases can create duplicate or mislabeled training examples and hide distribution changes.

**Rejected alternatives.** I did not patch only `bg_color`, because the detector showed the same boundary defect across call arguments. I did not rely only on downstream draw helpers, because they cannot restore the omitted-versus-explicit-`None` sampling contract.

## D2 — repair measured canonical support, not the detector

**Decision.** Add two sparse ordinary-generation profiles while preserving the existing random-mask majority:

- a keyed-random 4-connected mask at `sample_index % 6 == 0`;
- a palette-neutral canonical morphology at `sample_index % 8 == 7` when height and layout are not explicitly overridden.

**Why.** The first measured mismatch was canonical persistent-marker support `{0, 10, 18}` versus disjoint generated support. After fixing it, the detector exposed canonical object-count support `{18, 21}` as a second disjoint feature. A connected profile addresses the first mechanism; a sparse canonical morphology addresses the second and the profile-floor envelope directly.

**Rejected alternatives.** I rejected suppressing the structural detector, changing a version string without changing support, making all masks connected, and making equal-width canonical geometry the dominant distribution. Those choices would respectively hide evidence, create dishonest cache invalidation, erase useful variation, or introduce a stronger positional shortcut.

**Cost/limit.** Two fixed canonical topologies are now present sparsely. They are palette-neutral and surrounded by random/asymmetric lessons, and all declared rivals were refuted in 300 lessons and 1,200 rotations, but that finite census does not rule out every future topology-memorization strategy.

## D3 — keep the parametric extension isolated

**Decision.** Implement `cycle_direction = next | previous` under `workspace/parametric/`, with one immutable setting per episode and exact Racket programs as label authority. Do not import it from production code.

**Why.** It preserves the same object discovery and region-cycling reasoning while yielding a clean two-setting hidden parameter. Every selected input distinguishes the settings, and public challenges can conceal the setting and query answer.

**Rejected alternatives.** I did not parameterize layout, palette, or hole density because those are nuisance axes already varied by the generator, not rule variants. I did not approve the reverse rule as part of the canonical family; the evidence only establishes a runnable sibling proposal.

The packet's generic `wrap_rule` path imports a legacy helper absent from the protected authoring runtime. Because the canonical source is already a complete lambda, the prototype executes its exact callable via `strip_rule_wrapper`. If a future rule stops being lambda-form, this adapter should fail explicitly and be revised.

## D4 — audits are findings-only

The two drawn audit generators were source-hash checked and not edited. For `907bb29fbac5`, I bounded the search to 32 seeds × four consecutive hard samples and retained the first lesson-level shortcut witness. For `6c88f7697696`, I reran a source-bound probe over 252 ordinary calls, 60 exact-axis calls, nine invalid controls, 51 Racket applications, canonical pairs, and declared rivals.

## D5 — stopping decision

Stop after the selected repair, isolated prototype, visible solve, required lesson census, both audits, reports, packaging validation, patch replay, and fresh focused tests. No selected-task blocker remains. Additional work would be broader hypothesis search or shared-tool maintenance rather than a necessary repair to this assignment.
