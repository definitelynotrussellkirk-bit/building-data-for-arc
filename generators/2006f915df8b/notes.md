# Current review — generator 3.0.0

Rule `24791e9d8fc8` is unchanged: shortest four-neighbor non-wall path from 2 to 3, coloring only original-zero interior cells 8. All five canonical inputs remain valid, including the three-way shortest-path ties in train 0 and test 0. Generated labels remain Racket-owned. Production selects unique shortest paths; its selection helper is not an alternative label authority.

Replace narrow left-to-right L routes with alternating stretched two-loop witnesses and random lattice mazes with trees, branches, and up to two extra links. Only dimensions are public override axes: every integer height 7–12 and width 8–14 works in every band. Unknown/retired controls are rejected, and explicit None exactly follows omitted defaults. Default size 11×12 is anchored every fourth index; remaining defaults cover the whole range with difficulty weights. Fixed input roles 0/2/3/5 are not palette controls.

Three demonstrations plus one query are evaluated against 24 fixed DFS orders, flood-open, fewest-turns, and goal-greedy. Goal-greedy fits all five canonical pairs and is explicitly declared as a canonical shortcut. The two-loop witness defeats every declared competitor. The period-4 lesson schedule supports every query position under the public within-lesson rejection policy: witness endpoint parity differs from lattice mazes, and the first two witnesses have opposite vertical endpoint order after transposition, so neither can be rejected as a duplicate.

An earlier repair failed this guarantee at seed 6484, easy, exact 7×8 dimensions: witness indices 2 and 4 duplicated, production accepted [1,2,3,5], and holding out index 2 left a fewest-turns ambiguity. Preserve `counterexamples/duplicate-6484/` and the failing regression; the endpoint-parity/reflection construction fixes that concrete rejection case. Preserve canonical ties rather than weakening the validator to the sampler's unique-path subset.

Limits: witness topology and lattice endpoint structure are recognizable; the 27 rivals are a finite contract, not all possible shortcuts. Unique-path sampling does not cover tied routes. Final source hashes, public check counts, Racket receipts, accepted-lesson census, schedule enumeration, audits, and exposed solve are recorded in the returned REVIEW/RESULTS and checks. `workspace/checkpoint-tool/` provides verified, streaming recovery without redrawing assignments.

## Current owner acceptance

Accepted v3.0.0 maze diversity and duplicate-safe accepted-lesson assembly. Reviewer reports 57 portable tests, 12/12 stages, 300 lessons and 1,200 rotations. Seed 6484 intermediate-code counterexample and lost before-stage observations are retained with their original scope. Canonical rule unchanged; active target comment synchronization only. Semantic checks were not rerun. Generator approval binds these exact sources and does not admit model trajectories to training.
## Current reviewer considerations

Source SHA-256: `f574a02ff6155f62ad28562f6af217ddbc0bb8e4d41522c73e27b569eb7c7472`.

# Decisions — 2006f915df8b, version 3.0.0

## Rule and authority

The intended operation is shortest four-neighbor routing through cells other than wall color 5, from the single red 2 endpoint to the single green 3 endpoint. The existing Racket rule paints only original-zero interior path cells with 8. It preserves the endpoints, walls, off-path zeros, and input shape. Racket remains the source of production labels; the Python searches in the generator select inputs and implement named rival hypotheses.

The canonical ledger and canonical program are unchanged. The selected solution bank's `racket_target.target_code` contained four extra comment lines, while `raw_code` already exactly matched the canonical program. Aligning `target_code` with the canonical bytes removes that text-only authority disagreement. It does not change executable behavior, neighbor order, or tie handling. The unchanged rule hash is `24791e9d8fc8`.

All five canonical inputs remain validator-valid. Independent graph analysis finds three shortest routes in train 0 and the labelled test, so rejecting ties in `self_check` would incorrectly redefine the task. Production deliberately selects unique shortest routes to avoid using an arbitrary tie convention as a training signal. That sampling restriction is separate from the wider valid rule domain.

## Distribution and explicit controls

The old sampler produced narrow left-to-right L routes despite broader maze claims. It silently accepted several ineffective palette, placement, and texture controls; some advertised dimension combinations were rejected only because of difficulty. Version 3 keeps only two observable axes: integer `grid_h` in 7–12 and integer `grid_w` in 8–14. Every exact in-range pair is supported in every difficulty band. Unknown and retired controls, noninteger values, and out-of-range values raise actionable `ValueError`s. Explicit `None` follows the shared no-override convention and replays the omitted default exactly.

Every fourth raw index receives an 11×12 default-size anchor; the other indices draw across the full dimension domain with small-size preference for easy and large-size preference for hard. Explicit dimensions override this default policy. The anchor supplies canonical-scale examples in each band without narrowing the public dimension contract. The input colors are fixed semantic roles 0, 2, 3, and 5; cosmetic color permutation would change this task's meaning. The output may additionally contain 8.

Even indices generate a stretched two-loop witness. Odd indices generate a random spanning tree on a rectangular lattice, with zero to two extra connections and freely selected marked lattice endpoints. Random mazes retain only endpoint pairs with a unique shortest path of at least four nodes. If added loops leave no qualifying pair, the original spanning tree is used. The fallback stays a lattice maze rather than silently changing the scheduled profile. Witnesses receive transpose, reflection, translation, stretching, and optional branches or isolated zeros. A newly opened noise cell has at most one previously open neighbor and therefore cannot create a new competing route.

## Three demonstrations and query rotation

The intended lesson has three demonstrations and one query. `LESSON_SCHEDULE_PERIOD = 4`; even indices are witnesses and odd indices are mazes. The two-loop witness defeats all 24 fixed cardinal-order DFS hypotheses, flood-all-zeros, fewest-turns routing, and greedy movement toward the goal. These are the 27 actual `LESSON_COMPETITORS` and `SEMANTIC_RIVALS` declarations. `goal_greedy` is also declared as a `CANONICAL_SHORTCUTS` hypothesis because it fits every one of the five usable canonical pairs. Tests iterate the actual declarations instead of maintaining a second list of rival names.

The lesson claim concerns the accepted pairs after production validation and duplicate rejection. It is conditional identifiability against those declared rivals: a rival that fits every demonstration must agree on the held-out query. It is not a claim that every rival must be eliminated when its query prediction is already correct, nor a proof against every possible learner or hypothesis.

An earlier version of this repair failed that claim. At seed 6484, easy, exact 7×8 dimensions, raw indices 2 and 4 were identical witnesses. Starting at index 1 accepted indices [1, 2, 3, 5]. Holding out index 2 left three maze demonstrations on which the fewest-turns rival agreed, then failed on the query. The frozen intermediate generator, five inputs, independent graph results, and regression are retained under `counterexamples/duplicate-6484/` and `checks/`. This is an actual discovered failure, not an invented failed solve.

The final construction addresses rejection explicitly. One endpoint displacement of every witness is odd, including after transposition and reflection, while lattice-maze endpoint displacements are both even. Thus a witness cannot duplicate a maze. After transposition, successive even slots receive opposite start/goal vertical order determined by index modulo 4, so the first two witnesses cannot duplicate each other either. The first four attempted pairs therefore contain two distinct accepted witnesses. Duplicate mazes can reduce the accepted maze count but cannot remove those witnesses. Holding out any one of the first four accepted pairs leaves a witness in the demonstrations. This argument assumes the public lesson materializer's within-lesson duplicate policy; it does not establish a guarantee for a different exporter that removes examples globally or otherwise changes assembly.

The final reports give the public battery, a 100-lessons-per-band census, and exhaustive start-residue enumeration at seed 0. Random census counts and overlapping schedule windows are reported separately. These runs measure declared competitors and their actual Racket-labelled materialized instances; they do not prove coverage of all seeds or undeclared rivals.

## Rejected alternatives and remaining restrictions

Retaining ignored cosmetic controls would preserve a misleading interface, so the repair rejects them. Difficulty-specific hard limits would contradict explicit dimensions; difficulty now changes default weights instead. A one-loop rectangle cannot defeat every fixed DFS ordering; the second loop creates two decisions that require incompatible global direction preferences. Random mazes alone are varied but cannot guarantee informative demonstrations. Witness-only output would make the teaching topology too repetitive. Removing every loop would collapse shortest routing into a unique-route search problem. Changing the Racket tie convention would invalidate an existing authority merely to make a Python oracle convenient.

The final sampler still represents a designed subset of all valid mazes. Its even-slot geometry and odd-lattice endpoints are recognizable, and unique-path sampling leaves tied shortest-path behavior to the canonical fixtures. A learner could exploit profile recognition or a hypothesis absent from the declared 27 rivals; the retained source-bound probes establish the stated finite competitor contract rather than universal learnability. More unrestricted maze topology and explicit tied-path sampling would be separate distribution decisions, not unmeasured claims of this repair.

## Recovery tooling

The review encountered exhausted overlay inodes and memory pressure. The selected-task workspace includes a standard-library checkpoint utility that preserves source hashes, immutable assignment contracts, frozen baselines, changed files, and explicit exclusion/deletion receipts. It validates the original ZIP and destination before restoring and never redraws assignments or silently applies deletions. Its small fixture tests cover the dangerous boundaries. The work log distinguishes original observations, restored receipts, and reruns; it does not reconstruct vanished logs as if they had survived.
