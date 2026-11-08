# Working notes: ada3abda1b1d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `304c75512a5bc7d350ac380481caca58ae2f62eb6a15ad3e767cc38658f0424a`.

# Decisions for `ada3abda1b1d` v3.2.0

## D1 — Treat the upper count boundary as the root cause

**Decision.** Repair the missing count-five support rather than changing the exact-two transformation.

**Evidence.** The baseline official battery was fully green, but `checks/count-boundary-before.json` found zero count-five inputs, maximum multiplicity four in all 888 sampled inputs, and 864/864 three-demo windows compatible with `count == 2 or count >= 5`. The exact witness in `checks/question/witness.json` agrees between `rule_mirror` and canonical Racket, so the authority itself was not defective.

**Rejected alternatives.** Changing the Racket rule, changing the canonical outputs, or merely adding prose about exactness would not teach the missing boundary. Adding only a unit test for a handwritten count-five grid would validate the mirror but would not make generated lessons contain that evidence.

## D2 — Preserve exact canonical anchors

**Decision.** Keep sample slots 0, 4, and 8 on their historical canonical count signatures and alter ordinary non-anchor draws only.

**Rationale.** The anchors provide stable public-scale examples and strict-canonical coverage. The regression `test_exact_canonical_anchor_slots_are_preserved` checks signatures `(1,1,2,2,2)`, `(2,2,2,3)`, and `(2,2,3,3,4)` at all difficulty settings.

**Rejected alternative.** Adding count-five distractors to the anchors would solve the rival more uniformly but silently redefine the generator’s canonical-like family and weaken comparability to the public examples.

## D3 — Put a `{1,4,5}` boundary bundle in every ordinary non-anchor

**Decision.** Ordinary default samples jointly contain a singleton, a count-four distractor, and a count-five distractor. The profile label still controls whether additional distractors emphasize singleton, triple, or canonical-mixed behavior.

**Why this stronger schedule.** The first repair placed count-five support often enough for ordered three-example lessons, and all task tests and the official battery passed. The rotate-query census nevertheless found 423/1,200 ambiguous rotations and 600 warnings when the one discriminating sample became the query (`checks/lesson-census-v31-failure-summary.json`). Requiring the boundary bundle in each ordinary sample makes any three of four consecutive pairs sufficient while retaining exact anchors.

**Rejected alternatives.** One count-five example per three-slot period was too query-position dependent. Randomly sampling count five at a high rate would improve averages but offer no deterministic sliding-window guarantee. Raising the upper witness to six or more adds grid pressure without distinguishing the observed rival better than five.

## D4 — Judge lessons by rival rejection, not profile-label equality

**Decision.** `lesson_identifiable()` validates pair correctness and tests every declared competitor directly. A separate regression still requires every three consecutive default samples to cover the three declared profile labels.

**Rationale.** Profile names are generator metadata; identifiability is about whether a competing rule fits the demonstrations. The previous `profiles_seen == COUNT_PROFILES` requirement produced warnings even when concrete demonstrations already refuted the rivals and made query rotation depend on which labels remained.

**Failure mode guarded.** Removing the profile-label condition without direct competitor checks would be too weak. The final implementation keeps direct named-rival rejection, semantic witness claims, profile-floor checks, and explicit profile-coverage tests.

## D5 — Preserve constrained override compatibility

**Decision.** Add the boundary bundle when the requested color count and canvas can support it; for tiny explicit override combinations that cannot, fall back to the historical profile and retain the existing loud capacity assertion.

**Rationale.** Default production settings always have enough distractor colors. Rejecting previously valid exact override combinations would be an unrelated API break. The full override stage remains green in the final 12-stage battery.

**Limit.** An explicitly constrained fallback sample may omit count five. The production/default lesson schedule—not every conceivable override—is the identifiability guarantee.

## D6 — Add independent reusable probes

**Decision.** Keep two task-local tools in `workspace/`:

- `probe_count_boundaries.py` loads either the selected generator or an arbitrary `--generator` path, enumerates cyclic starts across four difficulty settings, and tests the undeclared upper-bound rival independently of semantic hooks.
- `probe_lesson_rotations.py` materializes four consecutive pairs for every requested start, holds out each pair once, and checks all declared lesson competitors plus `lesson_identifiable()`.

**Rationale.** The official gate can only enforce hypotheses that are declared. An independent probe caught the original omission even though the baseline battery was 12/12 green. The rotation probe exhausts the short deterministic schedule instead of trusting a random lesson sample.

## D7 — Do not change Racket authority

**Decision.** Leave rule hash `761b29fec54a`, canonical data, and the base solution untouched.

**Evidence.** Canonical execution, authority sync, Racket lint, and rule smoke all pass. The explicit count-five witness has `rule_mirror_matches_racket: true` (`checks/question/witness.json`). The defect was the generator’s teaching distribution, not the transformation.

## D8 — Report named-rival guarantees narrowly

**Decision.** Claim rejection of the declared rival set and the measured schedules, not universal identifiability.

**Measured scope.** Final evidence covers 864 independent three-demo windows, 3,456 exhaustive four-pair rotations, 12 required-rotation gate lessons, and a 300-lesson/1,200-rotation Racket-scored census. It does not enumerate all computable shortcuts, all random seeds, or every override combination.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/ada3abda1b1d/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
