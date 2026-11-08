# Current account: 6c93e8516229

## Intended rule and authority

The selected canonical authority remains pinned by `RULE_HASH = "6b0505b049ac"`.
For each 4-connected color-3 component:

1. any degree-3 cell makes the component red (`2`);
2. otherwise, exactly two perpendicular degree-2 turns make it magenta (`6`);
3. every other component becomes blue (`1`).

Thus a degree-4 plus is blue, not red, and a three-turn stair is blue, not
magenta. This review did not change the Racket program or its selected authority.
The final authority-set SHA-256 is
`bc68c00e1c215b3628b568e2f9ce97fa538954421745cd663b3b4f13cae79ada`,
the same as the baseline.

## Current generator domain

Version `3.0.2` constructs 10–19 by 11–21 grids with 3–8 separated green tree
components. Every ordinary board contains at least one blue, magenta, and red
class. The observable exact controls are `grid_h`, `grid_w`, and
`component_count`; unknown, mistyped, or out-of-range controls fail loudly.
Canonical `(height, width, component count)` profiles `(10,11,3)`, `(19,21,8)`,
`(14,12,5)`, and `(14,16,6)` are weighted anchors, while all legal joint exact
overrides remain constructive.

The production lesson uses three demonstrations and one query. Even sample
indices contain a blue degree-4 plus and odd indices contain a blue three-turn
path. Every board still includes all three output classes. This alternating
schedule refutes both declared canonical-fitting rivals in every production
three-demo lesson and in every one-pair-held-out rotation tested by the census.

## Repair in this review

Baseline source
`dd25d9df5cc4790a4fe1ff2b853e247525f311edb7967484b621578d3b3e889b`
passed 11 of 12 battery stages but accepted malformed top-level call arguments.
The defect lint reported 39 strict-scalar warnings spanning boolean, float, and
string seeds; boolean or negative sample indices; and invalid difficulty values.

The repair adds `_validate_call_arguments` before context construction. `seed`
and `sample_index` must now be exact integers, `sample_index` must be
non-negative, and `difficulty` must be `None`, `easy`, `medium`, or `hard`.
This rejects invalid API calls without narrowing any lawful generated grid or
changing sampling for valid inputs. The final source SHA-256 is
`b0ebe6d546dab4c0d4fe8c8163bfa4325f75e6652f586a69735644c8d01a4271`.

The prior accepted return `review-dddf2b1ea21ed018:v0001` was used only as a
lead for the existing topology, distribution, and teaching design. All claims
in this review were remeasured against the pinned source in this packet.

## Semantic teaching evidence

The declared rivals are:

- `any_junction_red`: incorrectly treats a degree-4 plus as red;
- `at_least_two_corners_magenta`: incorrectly treats three or more turns as
  magenta.

A 300-lesson final-source census (100 per difficulty, three demonstrations plus
one query) materialized 1,200 pairs and 1,200 one-pair-held-out query rotations,
covering 1,199 exact unique inputs. It found zero production ambiguities, zero
rotation ambiguities, zero hook warnings, and zero scoring errors. This is
finite evidence against the declared and searched rivals, not a proof of unique
induction against every possible hypothesis.

## Proposed parametric extension

`workspace/parametric/prototype.py` implements the smallest meaningful rule
parameter found for the original family: choose once per episode whether a
junction of degree `3` (canonical default) or degree `4` is red. With the chosen
degree removed, exactly-two-turn components remain magenta and all others blue.
The prototype is Racket-backed and separate from production. Retained seed-0
and seed-1 episodes exercise both settings; in each, all three demonstrations
refute the other setting and the query also differs. The variant is proposed,
not approved, and two retained episodes are not exhaustive validation.

## Known limits and open findings

The production generator remains a finite sampler of tree prototypes and D4
transforms, not the full mathematical domain of connected components. Every
board deliberately contains all three classes, which strengthens teaching but
is a curriculum bias. Canonical profile frequencies are engineering weights,
not an estimate of a real distribution. The repaired API contract introduces
no new grid shortcut or lawful-input restriction; the remaining uncertainty is
undeclared rival rules outside the finite census.

Key evidence: `checks/after/checks/6c93e8516229_after_battery_summary.json`,
`checks/task-tests/checks/task_tests.xml`, `checks/lesson-census.summary.json`,
`checks/lesson-census-compression.json`, and
`checks/parametric/junction-degree/manifest.json`.
## Current reviewer considerations

Source SHA-256: `b0ebe6d546dab4c0d4fe8c8163bfa4325f75e6652f586a69735644c8d01a4271`.

# Decisions: 6c93e8516229

The prior accepted return `review-dddf2b1ea21ed018:v0001` was consulted as a
lead. Its claims were not carried forward as measurements; this review reran the
battery, focused tests, Racket checks, and lesson census against the assignment's
pinned baseline and the final source.

## D1 / R1 — Validate top-level calls before constructing generation context

**Prior choice:** `generate` validated overrides but allowed Python coercions in
`seed`, `sample_index`, and `difficulty`. The original rationale is unknown.

**New choice:** require exact integer `seed`; exact non-negative integer
`sample_index`; and `difficulty` in `{None, "easy", "medium", "hard"}`.
Validation runs before `gen_ctx`.

**Reason and probe:** the baseline defect lint reproduced 39 accepted-invalid
scalar cases. A focused test covering eight representative malformed calls was
written and observed failing before implementation, then passed after the
minimal validator was added.

**Rejected alternatives:** normalize strings/floats to integers, rely on
`gen_ctx`, or validate only overrides. All preserve ambiguous cache keys or let
booleans masquerade as integers.

**Failure modes and limits:** a future public argument added outside this
validator needs its own contract. This change intentionally does not constrain
large valid integer seeds or any lawful generated grid.

Evidence: `checks/before/checks/6c93e8516229_before_defect_lint.log`,
`checks/task-tests/checks/task_tests.xml`, and
`checks/after/checks/6c93e8516229_after_battery_summary.json`.

## D2 / R2 — Use one episode-level rule parameter: `junction_degree`

**Choice:** propose `junction_degree ∈ {3,4}`, selected once per episode, with
canonical default `3`. A component containing the selected degree becomes red;
otherwise exactly two turns becomes magenta; otherwise blue.

**Why this parameter:** it changes a real topological predicate while preserving
the original task's object roles, recoloring relation, output palette, and
component grammar. Degree 4 is already a meaningful canonical counterexample,
so both settings can be taught with lawful inputs rather than synthetic
metadata.

**Input constraints and invariants:** the ordinary tree-component grammar is
retained; demonstrations include both degree-3 and degree-4 junctions; three
demonstrations plus one query are generated per episode; output remains
componentwise recoloring with colors 2, 6, and 1.

**Rejected alternatives:** parameterize output colors (cosmetic and likely to
change fixed semantic roles); parameterize “exactly two” to “at least two”
(which weakens the distinctive canonical relation and risks poorly separated
lessons); or add multiple parameters at once (unnecessary combinatorial burden).

**Probe and failure mode:** retained seeds 0 and 1 exercise both settings through
actual Racket execution. In each episode every demonstration and the query
disagree with the other setting. Two episodes establish runnable separation,
not exhaustive coverage; future adoption would need larger seed, override, and
lesson-rotation checks.

Evidence: `generators/6c93e8516229/workspace/parametric/README.md` and
`checks/parametric/junction-degree/manifest.json`.

## D3 / R2 — Keep the parameter out of the canonical execution path

**Choice:** the prototype lives under `workspace/parametric/`; production
`generator.py`, `RULE_HASH`, and selected Racket authority continue to implement
degree 3 only.

**Reason:** the assignment asks for assessment/prototyping, not unilateral rule
replacement. A passing repair cannot confer approval on a new task family.

**Rejected alternative:** add a production override that silently changes the
answer rule. That would make one generator ID map to multiple authorities and
invalidate the source/rule binding.

## D4 / R3 — Retain the existing production distribution and witness schedule

**Choice:** do not refactor the already-passing sampler. Keep 10–19 by 11–21
grids, 3–8 separated tree components, all three classes per board, weighted
canonical profiles, and the even/odd counterexample schedule.

**Reason:** before repair, every distribution, override, semantic, grammar,
authority, and profile stage was already green. The only reproduced canonical
repair defect was the public call contract. Unrelated sampler changes would add
risk without addressing evidence.

**Alternatives checked:** reducing to canonical tuples would overfit profiles;
removing the alternating witness would re-open `any_junction_red` or
`at_least_two_corners_magenta`; free placement would weaken constructive dense
overrides.

**Measured result:** final profile support was 49/60 exact and 60/60 envelope;
the 300-lesson, 1,200-rotation census found zero declared-rival ambiguity.

## D5 — Preserve full census evidence with a lossless compact mapping

The full census report exceeded 15 MB, so it was gzip-compressed rather than
truncated. `checks/lesson-census-compression.json` records the original path,
byte size, SHA-256, compressed path/SHA-256, and restoration command. The compact
summary remains directly readable.

**Rejected alternative:** include only aggregate counts. That would discard the
only retained full source-bound lesson evidence. Compression preserves it while
staying within the return budget.

## D6 — Final self-review and limitations

No new shortcut was introduced by the repair: for every lawful call, generation
starts after the new guard with the same values and same version-keyed source
logic except the intentional version bump. The exact degree-4 witness in
`checks/question/generator-shortcuts/` confirms the strongest known canonical
shortcut still disagrees on emitted inputs.

The generator remains narrower than the entire mathematical domain because it
samples finite tree prototypes. The census tests finite declared and generic
rivals; it does not prove universal identifiability. These limitations are
reported rather than hidden by a broader acceptance claim.
