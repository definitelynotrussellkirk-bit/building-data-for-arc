# dc155169ea57 — current authoring notes

## Rule and authority

Original ARC family: `training:84ba50d3`. Colors are semantic literals: background 8, objects 1, barrier 2. Extract blue four-connected components above the full red row. If every occupied row of a component has at most one cell, translate its bottom to the grid floor and punch background-colored holes in the barrier at its columns. Otherwise, align its **lowest row containing more than one cell** immediately above the barrier. Narrow tails may cross the barrier. Erase source objects, draw translated objects, then apply holes last.

Canonical RULE_HASH remains `c0f1818b0fb2`; full canonical program SHA-256 remains `2def524a1836b8bbbbf304e452ba7cfadf72ac353419ed428326edfcc2b167e6`. The supported authority-sync command synchronized only the selected active target_code formatting. The canonical ledger and archival raw_code were not changed.

## Version 3.4.0 repair

The original3.2.0 sampler separated all components by column bands, admitting a projection-grouping shortcut. Version 3.3.0 introduced detached singleton/bar witnesses but did not reliably teach supporting-row and tail distinctions. Fresh review reproduced three further rivals on its retained300-lesson census: lowest-cell stopping(28ambiguous lessons), highest supporting row(22), and lowest maximally wide row(21). These sets overlap. Historical receipts and exact Racket reproductions are retained in the return; see `checks/peer-review.md`.

The final witness uses one detached singleton and one wide object with an upper row of at least3 cells, a lower row of2 cells and a1 cell tail. The singleton shares a column with the wide object but has a separating blank row; its column differs from the tail column, so the tail remains visible at the barrier. Residues0 and2 of a four-position ordinary schedule reverse vertical order. Both witness positions distinguish all four rivals. Other components remain independently sampled, and odd positions retain the original richer grammar.

Scheduled default draws reserve wide widths of at least3 before choosing feasible counts, and require height>=9 and barrier row>=5. This accommodates both vertical orders without merging components. Explicit semantic overrides bypass the schedule and retain the original legal7..30dimension range and exact controls. The7x7 canonical singleton profile remains available in ordinary positions.

Three demonstrations are declared. Four distinct pairs with two witness positions permit holding out any one pair while retaining a witness. Actual deduplicated lesson assembly, all declared starting residues at seed 0, and query rotations were checked. No universal `lesson_identifiable` predicate is asserted.

`SEMANTIC_RIVALS` and `LESSON_COMPETITORS` contain four distinct hypotheses: projection_groups, lowest_cell, highest_support and max_width. `CANONICAL_SHORTCUTS` contains the three that fit all four original pairs; lowest_cell is deliberately excluded because a canonical tail already refutes it. Multiple declaration bindings are not counted as extra rivals.

## Distribution and exact controls

The30%canonical linked-profile branch preserves all four original height/width/line/count/wide/thin combinations. Mixed profiles are chosen on witness positions; ordinary positions compensate with singleton probability 1/2 and each mixed profile probability 1/6. Across parities each canonical profile retains marginal probability 1/4 within that branch. Broad hard dimensions span15..30. Input shape variety remains narrower than arbitrary legal polyominoes; easy witness objects are deliberately more structured than ordinary easy draws.

Booleans, coercible strings/floats for integer axes, unknown keys/difficulties, and invalid proportions reject explicitly. None overrides and texture='none' normalize to omission. thin_frac is approximate because integer composition is rounded. Exact dimension/count conflicts carry incompatible_axes. Feasible width-only all-wide draws select a realizable default count before recording it. Lawful all-wide, all-thin and one-shape textures remain diagnostic degeneracies and do not claim sufficient teaching support.

## Verification

Final generator SHA-256: `b0988612ae6038bbbddb6f8f30e787984c5d9c71a1e380f88cd13ada8655e3d6`. Final battery:12/12 green. Semantic sample:600/600 lawful draws,4/4 canonical inputs accepted,288/600 projection witnesses and306/600 joint support witnesses. Racket checks validate60/60claims for each witness class, including all three support rivals. Profile floor:22/60 exact hits(easy10, medium7, hard5),45/60 envelope hits.

Final300-lesson census:3 demonstrations+1 query,1,200 pairs,1,131 unique input hashes; no production ambiguity and no ambiguity in1,200holdout rotations against the four declared rivals. Fixed-seed schedule:12 lessons,48 rotations,21 unique inputs across overlapping windows. These are finite, source-bound checks rather than guarantees over all seeds, overrides or hypotheses.

`workspace/probe_teaching.py` uses public Catalog generation with independent --demos/--queries counts. Seed17, all three bands,3 demonstrations+4 queries:7distinct inputs per episode,12/12 Racket-consistent query labels, each query distinguished against all declared competitors from demonstrations alone. Task tests pass22 tests plus86 subtests, including the10prototype tests. The fresh patch replay is documented outside this task patch in REVIEW.md and RESULTS.json.

## Separate proposed extension and limits

`workspace/parametric/` proposes barrier_capacity values1,2,3. Default1 returns exact canonical Racket bytes; alternatives change one guarded threshold literal. Each setting has2 demonstrations and4 queries. The final prototype's6/7/7rival inventories include a bounding-box-capacity interpretation for2/3; it is equivalent at1 and correctly omitted from required refutation. See its README and `checks/parametric/verification-v2.json`. Public challenges exclude hidden settings and query answers. No variant or source receives training approval from passing checks.

Minimal counterexamples live in `counterexamples/`. Remaining limits are the deliberately structured witness grammar, finite rival inventory, diagnostic overrides without automatic curriculum guarantees, and unmeasured downstream learning value. No Qwen training or human-difficulty calibration was run. Audit findings for other generators are reported in AUDIT.md and remain outside this repair.


## Current proposed prototype public identifiers

The accepted canonical repair does not approve this separate prototype. Static inspection found setting-associated public path ordinals: multi-capacity export uses episode-NN-challenge.json in requested capacity order. The exact reviewer prototype remains unchanged. An external follow-up must replace setting-associated public paths with names derived solely from visible demonstrations and query inputs, preserve original evidence, and exercise the writer through Racket with a focused privacy regression. Source-bound pending work: `generators/dc155169ea57/evidence/parametric-public-identifiers-pending-bde888379ee5fdae/manifest.json`. No owner prototype execution or full battery rerun was performed.
## Current reviewer considerations

Source SHA-256: `b0988612ae6038bbbddb6f8f30e787984c5d9c71a1e380f88cd13ada8655e3d6`.

# Decisions and evidence

## D1 — Teach connectivity and supporting-row distinctions explicitly

**Prior choice:** version 3.2.0 placed every object in a separate column band. Original motivation beyond simple non-collision placement is unknown. This prevented the generator from showing the difference between connected components and horizontal projection groups. Prior unresolved audits `review-046c5b5b5e5c6d1d:v0001` and `review-1e2534b09933f73f:v0001` were leads, not accepted measurements of current source.

**Initial choice (3.3.0):** retain the existing scene sampler and inject a disconnected thin/wide overlap on every even ordinary draw. Residues0 and2 reverse vertical order. All other components retain their original positions. This creates an executable counterexample while preserving component counts, exact dimensions, mix and fixed colors. Odd slots retain the more varied original shapes. The literal minimal witness is in `repo/generators/dc155169ea57/counterexamples/projection_overlap.json`; `checks/projection-witness-racket.json` independently confirms its expected output under the selected authority. The test-first failures are retained in `checks/teaching-red.log`.

**Rejected alternatives:** arbitrary rejection sampling would make small-grid support and exact controls less predictable; replacing every object with isolated bars would unnecessarily narrow the grammar; remapping colors would violate the literal canonical palette; claiming that a positive witness frequency alone proves teachability would ignore lesson assembly and deduplication.

The projection_groups rival fits all four canonical pairs. In the first candidate it was one callable with three declarations, not three independent hypotheses.

**Final correction (3.4.0):** independent review found lowest-cell, highest-support and maximal-width interpretations surviving some demonstrations: respectively 28/300, 22/300 and 21/300 production lessons, and 108/1,200, 70/1,200 and 69/1,200 rotations. Exact Racket reproductions are in checks/peer-review.md. The final wide witness uses upper width>=3, lower width 2, and a one-cell tail, plus a detached singleton. Both scheduled positions distinguish all four interpretations. Default witness slots reserve height>=9, line>=5 and wide width>=3 before selecting feasible counts; explicit overrides bypass this restriction. The tail and passer use different columns. Highest-support and max-width join projection_groups as canonical shortcuts; lowest-cell is a lesson competitor only. The new independent support regression failed 43 subtests with one huge-integer error before correction, then all seven teaching tests passed. The final finite inventory contains four unique rivals. `EXAMPLES_NEEDED=3` and `LESSON_SCHEDULE_PERIOD=4` expose the intended lesson policy. The baseline lacked executable teaching declarations. The final source does not use a tautological universal lesson-identifiable claim.

## D2 — Preserve canonical profiles while adding larger inputs

A30% linked-profile branch preserves canonical combinations `(9,9,5,3,1,2)`, `(7,7,3,1,0,1)`, `(11,11,6,3,1,2)`, `(18,18,8,5,3,2)` where entries are height,width,line,count,wide,thin. A singleton cannot also be an overlap witness. Mixed forms therefore occur uniformly on witness positions, while ordinary positions weight the singleton form by1/2 and each mixed form by1/6. Across both parities each form has marginal probability 1/4 within the linked branch.

Hard broad draws expand to15..30 on each dimension; ordinary easy/medium distributions remain. A shape count that will not fit width 7 is avoided at default-count selection time rather than silently dropping a component. Exact user controls still reject true conflicts. Final profile-floor observations are22/60 exact hits (10/20 easy,7/20 medium,5/20 hard),45/60 in-envelope hits. Linked-profile regression draws are2,400; this is a structural support check, not a claim of semantic diversity for every draw.

## D3 — Make control contracts truthful

Integer axes no longer coerce booleans, floats or strings. Unknown keys/difficulty names and invalid proportions reject explicitly. Thin composition is rounded to a component count, so thin_frac is marked approximate. None overrides and the no-op texture normalize to omission. Exact incompatible requests provide incompatible_axes metadata. Lawful all-thin/all-wide/one-shape textures remain available as diagnostics and are explicitly classified as degenerate rather than invalid. The prior strict scalar/override warnings are retained in `checks/before/`.

These explicit overrides do not inherit ordinary-production teaching guarantees. Each assembled lesson still needs its own rival check. Confusing per-input lawfulness with sufficient demonstrations would recreate the main defect.

## D4 — Keep canonical authority fixed

The before authority gate failed because the selected target_code copy differed in formatting from the canonical ledger, although execution parity passed. The supported `authority-sync --selected-only` proposal was inspected and applied. The allowed selected JSON path is `repo/shared/data/base/solutions/training/84ba50d3__dc155169ea57.json`; only `/racket_target/target_code` was synchronized. Canonical source, catalog rule hash c0f1818b0fb2 and archival raw_code retain their meanings; the archival formatting difference is still reported. Evidence: `checks/authority-sync-proposal.json`, `checks/authority-sync-apply.log`, final authority receipt. This is not a new reference transformation.

## D5 — Check complete, actually materialized lessons

The broad census uses production sampling,100 lessons per band with the seed recipe and accepted indices in `checks/lesson-census-v2.json`. Every lesson has3 demonstrations+1 query; every materialized pair is held out once, preserving the other pairs' order. Results:300/300 materialized,0 production ambiguity,1,200/1,200 rotations without ambiguity/errors,1,131 unique grid hashes among1,200 pairs. This does not mean1,200 independent scenes or exhaustive random support.

The separate schedule census fixes seed 0, enumerates all4declared start residues in3bands, and checks all4 query positions:12 lessons,48 rotations,21 unique inputs across overlapping windows. Its exact receipt is passed to the final battery with required rotations. The first after battery warned because this receipt had not yet been supplied; retain that intermediate run in `checks/after/`. The generic census residue-reporting modulus6 is separate from the declared schedule period4.

Four-query production is separately exercised by `workspace/probe_teaching.py` with seed 17,--demos3,--queries4, one episode per band. All7 inputs per episode are distinct,all12 query labels match Racket, and demonstration-only fit rejects all four declared rivals before each query is assessed. This is separate from one-query rotation evidence. Exact argv and paths are in RESULTS.json.

## D6 — Propose a nearby meaningful rule parameter

`barrier_capacity` changes the executed row-count threshold to1,2or3 while retaining object roles, connectivity, fall direction, supporting-row alignment, tails and final-hole order. Capacity1 returns canonical Racket bytes exactly. Capacities2/3 substitute one asserted literal site; bounded values prevent unrelated program mutations. A width 3upper/width 2lower support object distinguishes all3settings.

The prototype is separate from selected generation and exposes independent demonstration/query counts. It uses a narrower teaching grammar and explicitly materializes Racket labels. Each setting has2 demonstrations+4 queries; public challenges contain only training pairs and input-only queries. Reusing the same scenes across settings is intentional controlled comparison; uniqueness is checked within each episode. Private settings and reference programs are retained solely as authoring evidence. The fresh review found an additional bounding-box-capacity shortcut not in the original six-rival inventory; its reproducer, repair and final evidence are retained under checks/parametric and checks/peer-review.md. The final inventories have6/7/7 rivals for capacities1/2/3, respectively; the bounding-box rival is equivalent at1. All three corrected episodes retain2 demos+4 queries and65 Racket grid executions in total. Ten focused prototype tests pass. Original sources, examples and reports remain byte-for-byte under checks/parametric/prior/v1 with a retention manifest. No variant is approved for production by this review.

## D7 — Portable tests and honest solve evidence

Task-local legacy tests used a private per_puzzle import/path assumption. They now use public reviewer_support helpers and recorded_draws. The frozen root fixture is unchanged. The initial official task_tests attempt failed in prerequisite preflight (pytest unavailable); no tests ran. An isolated Python environment resolved that infrastructure issue. The first official staged run passed20 tests plus29 subtests. The final amended suite passes22 tests plus86 subtests (108 reported cases); the final fresh replay is recorded separately.

The blind solve completed before assigned-generator inspection:3/3visible examples,2 queries execute,private correctnessunknown. A two-color interior conflict remains underdetermined by its visible demonstrations; the chosen leave-conflict-unchanged policy is disclosed. An initial broad ZIP README inventory had exposed unrelated historical examples, not the assigned blind task; the blind notes disclose that context.

A fresh final-source post-repair solve, after retaining the earlier episode under checks/prior-solve, used only its prepared visible examples during the solve, with earlier rule exposure=yes. First revision:3/3visible,2 queries execute,private correctnessunknown. Notes are authored work logs, not captured token-level model traces. No accidental failed revision was invented.

## D8 — Keep audits and tooling separate

Both adversarial audit targets stay unchanged. AUD-D9-001 proves exact count underproduction despite a feasible layout; AUD-D9-002 proves canonical width 3 frames are rejected/omitted; A2 independently confirms already unresolved ignored exact corner-key controls. See AUDIT.md and exact authority-backed counterexamples.

The packet contains103,286 files and requires many more filesystem entries than its compressed size suggests. Ordinary extraction exhausted local inodes; a full isolated temporary-memory extraction and official verification succeeded. A streaming stdlib ZIP verification helper is included for future agents. Fresh return replay uses the supported runtime closure and reports its partial extraction scope, followed by actual tests in that fresh copy. No installed environment or duplicate repository tree is returned.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/dc155169ea57/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Parametric public-identifier follow-up — 2026-10-24

The pending ordinal-path finding is resolved in the separate, still-unapproved
barrier-capacity prototype. The exporter now writes exact
`reviewer_support.public_challenge_bytes` to
`public/challenge-<public_challenge_id>.json`, sorts multi-setting batches by
that ID, rejects duplicate visible payloads, and keeps settings, seeds, programs
and query answers under `private/`. A focused regression mutates private seed,
capacity metadata and query labels without changing the public ID, while a
visible-grid mutation changes it.

The production generator and canonical rule remain byte-for-byte unchanged.
The corrected writer was executed through Racket for capacities 1, 2 and 3:
three public files, two demonstrations plus four distinct queries each, 65
Racket grid executions, and a clean saved-file projection check. Prototype
source SHA-256 is
`43a3fe646021328f2db2738485eac44539bf1c4d047504975f289956c8b4d354`.
This closes the path-leak defect only; it does not approve the parameter variant
or establish universal identifiability.
