# Review notes: 4bf462ff34fb

## Intended rule

Recolor a 4-connected blue (`1`) component to green (`3`) iff its exact border
signature is `T`: it touches the top edge and no other edge. Preserve blue
components touching any additional edge, interior blue components, and all
non-blue components. The selected Racket authority and `RULE_HASH
284791f05f91` were not changed.

## Reproduced defects in v3.0.0

1. The full override matrix timed out after 301 seconds at 12,000/12,960 draws.
   Placement used a 20,000-node randomized backtracking search inside up to 30
   scene restarts, and exact-border origin enumeration translated every shape
   at every canvas cell before recomputing its border signature.
2. A four-pair ordinary window (`easy`, seed `0`, sample indices `5..8`) became
   ambiguous when pair `6` was the query. The remaining three demonstrations
   all used linked canonical profiles, so both `all_top_blue` and
   `all_top_only_objects` fit every demonstration but changed the query.
3. The deterministic fallback scene did not contain all declared rival
   witnesses.
4. The task-local test hardcoded a pre-extraction repository layout and failed
   before collection in the portable packet runtime.
5. `linked_canonical_profile` was declared as a semantic witness without a
   corresponding rival disagreement, causing a strict semantic-contract warning.

The exact historical lesson counterexample and repaired replay are retained in
`counterexamples/rotation_ambiguity_seed0_easy_5_8.json`.

## Repair in v3.1.0

- Compute exact-border origins from shape bounding boxes rather than translated
  cell sets.
- Use forward checking plus dynamic minimum-remaining-values placement, with a
  512-node budget per randomized scene attempt so impossible random layouts
  restart instead of consuming the whole matrix timeout.
- Force every generalized scene to include a blue top-corner near-miss and a
  non-blue top-only object. The fallback now also includes witnesses against
  all four declared rivals.
- Restrict linked-profile eligibility to odd sample indices and double its
  conditional probability to preserve the approximately 32% overall prior.
  Therefore every four consecutive indices contain at least two generalized
  scenes; after any one query holdout, at least one anti-shortcut scene remains.
- Make task tests locate the portable repository with `reviewer_support`, and
  add regressions for the historical rotation, fallback witnesses, exact-axis
  hot spots, and witness/rival contract completeness.
- Remove the weak `linked_canonical_profile` witness declaration while retaining
  linked-profile frequency measurement through `strict_canonical_like`.
- Add `workspace/probe_curriculum.py`, which enumerates consecutive starts and
  every query rotation against the generator's declared competitors.

## Final evidence

Final generator SHA-256:
`df5d13eda0724fd99e4a80307afdc43a762406a79ba67b4a3d28a6134cf19f5b`.

- Battery: 12/12 stages green.
- Override contract: 12,960/12,960 accepted, 144 cases, 0 findings.
- Task-local tests: 10 tests plus 11 subtests passed.
- Racket-labelled lesson census: 300 lessons, 1,200 pairs, 1,200 query
  rotations, 1,200 unique inputs, 0 ambiguities or scoring/materialization
  errors.
- Task-local cyclic probe: 768 four-pair windows, 3,072 rotations, 810 unique
  inputs, 0 declared-rival ambiguities.

These are finite checks against the four declared rivals, not proof against all
possible induction shortcuts. The linked-profile prior remains intentionally
close to the public component-profile distribution, while generalized scenes
carry the distinguishing evidence.
## Current reviewer considerations

Source SHA-256: `df5d13eda0724fd99e4a80307afdc43a762406a79ba67b4a3d28a6134cf19f5b`.

# Decisions: 4bf462ff34fb

## D1 — Preserve the selected rule and authority

**Decision.** Keep the intended transformation and selected Racket authority
unchanged: recolor only blue components with exact border signature `T`.

**Why.** The defect was in sampling, lesson assembly, runtime and test
portability, not in the canonical labels. Rule smoke, authority sync and the
independent shortcut apply all matched rule hash `284791f05f91`.

**Rejected alternative.** Broadening the rule to “all blue touching top” would
make the generator easier but contradict the canonical task at top corners.

## D2 — Repair placement at its source

**Decision.** Replace per-cell translated-origin enumeration with bounding-box
arithmetic, and replace static randomized backtracking with candidate
precomputation, dynamic minimum-remaining-values selection, forward checking and
a 512-node budget per random scene attempt.

**Why.** Evidence showed nested proof attempts were the runtime source: a
20,000-node search could be repeated across 30 scene restarts, while candidate
origin generation dominated profiles by recomputing equivalent border facts.
The final override matrix completed all 12,960 draws with no findings.

**Rejected alternatives.** Raising the five-minute stage timeout or the node
budget would hide the defect and retain poor scaling. Removing shape/border
variation would make generation faster by narrowing the curriculum. A greedy
placer without backtracking was rejected because it needlessly increases
fallbacks on legal dense scenes.

**Limit.** The 512-node budget is a practical restart threshold, not a proof
that every legal random specification will be found before fallback. The
fallback is valid and deliberately witness-complete.

## D3 — Guarantee lesson evidence, not only marginal witness frequency

**Decision.** Keep a roughly 32% linked canonical-profile prior, but make only
odd sample indices eligible and use a 64% conditional draw. Every four
consecutive indices therefore contain at least two generalized slots. With
three demonstrations and one query, every hold-one-out rotation retains at
least one generalized anti-shortcut demonstration.

**Why.** The historical window `easy/seed=0/indices=5..8` proved that a healthy
marginal generalized fraction did not guarantee a teachable lesson. The selected
policy gives a deterministic coverage floor while retaining stochastic profile
selection and the intended overall prior.

**Rejected alternatives.** Merely increasing the generalized probability gives
no hard per-window guarantee. Eliminating linked profiles would throw away
canonical morphology coverage. Hard-coding a four-item shape cycle would be more
restrictive than needed and easier to infer from superficial geometry.

**Limit.** Eligibility has index parity. Sample indices are generator metadata,
not grid features; nevertheless the cyclic probe explicitly checks consecutive
starts and all query positions. The reported guarantee is against declared
rivals only.

## D4 — Put decisive rivals into every generalized scene and fallback

**Decision.** Force a blue `TL` near-miss and a non-blue `T` object in generalized
scenes. Make the fallback contain a blue `TL` singleton, blue `T` vertical
domino, blue `B` vertical domino and non-blue `T` singleton.

**Why.** These are minimal direct witnesses for the two canonical-fitting rivals:
`all_top_blue` and `all_top_only_objects`, while the bottom blue and ordering also
support the other-border and first-blue distinctions. The fallback previously
could satisfy grammar without refuting all declared shortcuts.

**Rejected alternative.** Relying on random `TL`/`TR` or distractor-border draws
made evidence probabilistic and allowed complete lessons with no decisive pair.
Adding many fixed objects was rejected because the four-object fallback is enough
and preserves canvas flexibility.

## D5 — Require semantic witnesses to name an actual disagreement

**Decision.** Remove `linked_canonical_profile` from `SEMANTIC_WITNESSES` but keep
profile measurement via `strict_canonical_like` and `MIN_STRICT_FRAC`.

**Why.** A profile-presence feature is distribution coverage, not evidence
against a rival transformation. Registering it as a witness produced a warning
with no associated competitor. The new task test requires the semantic-witness
keys and witness-to-rival mapping keys to match exactly.

**Rejected alternative.** Inventing a weak “non-profile” rival solely to satisfy
the schema would not represent a plausible output rule.

## D6 — Make tests portable and regression-focused

**Decision.** Use `reviewer_support.find_root(__file__)`, `canonical_path`, and
`canonical_pairs`; add tests for the exact historical rotation, fallback witness
coverage, known override hot spots and witness/rival contract completeness.

**Why.** The packet runtime relocates task tests. Fixed `parents[...]` assumptions
failed before tests could run. Each production change now has a task-local
regression that failed under the baseline behavior and passed after repair.

**Rejected alternative.** Copying canonical JSON into the task test would avoid
path discovery but duplicate authority data and become stale.

## D7 — Add a reusable cyclic-curriculum probe

**Decision.** Add `workspace/probe_curriculum.py`, which loads the current
generator, iterates its declared competitors, enumerates consecutive starts for
requested seeds/bands, and rotates every pair into the query.

**Why.** The shared lesson census samples many Racket-labelled lessons and
rotations but does not enumerate every cyclic start. The task-local probe is
cheap enough to close that specific gap and is usable by future reviewers.

**Scope.** Final invocation used 32 starts × 8 seeds × 3 bands = 768 windows,
with 4 rotations each = 3,072. It uses the Python mirror for speed; the final
battery and shared census separately bind that mirror to the selected Racket
rule. It does not certify undeclared rivals.

## D8 — Preserve failures and perform clean delta replay

**Decision.** Keep the before timeout, the first after semantic-contract failure,
the exact lesson counterexample and the clean replay evidence. Build the return
from the packet’s source-bound packager rather than manually zipping the tree.

**Why.** The failed states explain the repair and prevent a green-only handoff
from obscuring what was actually fixed. Fresh replay under an isolated Git root
proves the generated patch applies to the issued packet rather than depending on
working-directory residue.
