# Current notes — 563e1df172df v3.2.0

## Intended rule and domain

On black 0, one red 2 and one green 3 occupy different rows and columns. Paint 8 from red horizontally along its row to green's column, then vertically toward green; keep endpoints. Fixed colors carry semantic roles. The selected Racket authority and `RULE_HASH = "a29452f21143"` are unchanged. The generator retains the twelve exact scene profiles, canonical shapes 10×16 / 12×14 / 15×15, quadrants, and near/medium/far distance bands. The declared input support is deliberately finite, not all reference-lawful grids.

## 2026-10-20 repair decisions

Literal integer seed and nonnegative literal integer sample_index are required before generation; bool, float and string coercions are rejected. Negative integer seeds remain supported.

The previous v3.1.0 four-slot gap cycle fixed global arm-only query rotations but synchronized with the twelve-profile cycle: northwest always had unit row gap and northeast unit column gap. This permits conditional arm-only shortcuts. Replace it with a five-slot cycle `(both_nontrivial, unit_row_gap, unit_column_gap, both_nontrivial, both_nontrivial)` and declare combined lesson period 60. Preserve the existing both-nontrivial fallback when a requested unit orientation is geometrically impossible; it keeps exact profile semantics and strengthens arm evidence.

The default changes from four to eleven demonstrations. Twelve consecutive pairs give each quadrant three distinct gap phases; each arm is nontrivial at least twice in that quadrant before a single query holdout. Every remaining eleven-demo lesson therefore retains both-arm evidence in every quadrant. Shorter lessons of at least four demos may pass actual-rival checks, but have no unconditional arbitrary-rotation guarantee. The cost is longer default episodes; arbitrary subsets and multiple holdouts are not covered.

The original three direct wrong rules fit 0/8 stored canonical pairs, so they remain semantic/lesson competitors rather than canonical shortcuts. Actual canonical-fitting shortcuts are horizontal-first only for far distance, and vertical-first only when red is southeast of green. Both fit 8/8 canonical labeled records (four unique input grids), have generated Racket-checked counterexamples, and are registered with truthful semantic witnesses. Northwest-conditional horizontal-only and northeast-conditional vertical-only rivals protect the repaired joint support. Seven unique rivals are checked. Distance predicates remain branch witnesses, not false per-firing rival claims.

## Evidence and current limits

Final generator SHA-256: `893e2a8667332831c99aa8e39cd51684a64e4a94adffe09abc151d10e1e0c7b3`. Final battery 12/12 green; direct task-local tests 75 passed; strict support 600/600; exact profile support 60/60. Final eleven-demo production census: 300 lessons / 3,600 rotations / 3,202 unique inputs, no declared-rival ambiguity. Fixed seed 0, all 60 starts × three bands: 180 lessons / 2,160 rotations / 211 unique inputs, no ambiguity. These are finite declared-rival checks, not universal induction or all-seed proof. Deterministic schedule correlations and the finite shape/profile grammar remain intentional limits.

The required portable aggregate task-test stage is blocked by the unchanged frozen root fixture's fixed-depth canonical path. The packet's DUTIES forbids reviewer edits to that fixture. A separate optional maintainer migration patch accompanies the return; passing task-local tests do not clear this gate. No source/rule approval or training-admission state is changed.

Minimal current generated witnesses: `counterexamples/review-061120dc37b1cf76-shortcuts.json`. Regressions: `tests/test_contracts.py`, `tests/test_curriculum.py`, `tests/test_parametric.py`. Exact before/intermediate/final receipts, audits, censuses, commands and solve provenance are in the return for `review-061120dc37b1cf76`; its root REVIEW/DECISIONS/RESULTS provide the index. Historical review-index decisions are leads, not measurements of current source.

## Proposed parameter and tools

`workspace/parametric/prototype.py` materializes horizontal-first (canonical default) and vertical-first turn order once per episode. It retains roles, fixed colors and two-leg routing, labels with the public real Racket bridge, and separates public four-demo/one-query challenges from private parameter/source/answer records. Default parity is 8/8; both settings disagree on the same inputs and each demo distinguishes them. This is a proposed two-setting extension, not a new approved production rule and not the eleven-demo production contract.

`workspace/tools/compressed_evidence.py` provides lossless supported evidence compression/restoration for later reviewers. It verifies paths, sizes and hashes and preserves backups; it has no generator/runtime dependency. Imported historical material remains in `evidence/associated_notes.jsonl` and the retained review index.
## Current reviewer considerations

Source SHA-256: `893e2a8667332831c99aa8e39cd51684a64e4a94adffe09abc151d10e1e0c7b3`.

# Decisions — 563e1df172df, review-061120dc37b1cf76

## D1 / R1: strict scalar inputs, with the existing integer seed domain

The baseline silently accepted booleans, numeric strings and floating-point inputs through coercion. That contradicts the literal-integer API contract and can collapse distinct caller requests into one draw. Require `type(seed) is int` and `type(sample_index) is int`, with sample index nonnegative, before any generation. Preserve negative integer seeds, zero, and large integers; the contract does not require nonnegative seeds. Thirty-three invalid scalar cases and four valid integer cases are covered in `tests/test_contracts.py`. The original reason for permissive coercion is unknown. Continuing coercion or rejecting all negative seeds would conceal caller bugs or narrow an otherwise valid domain.

## D2: preserve canonical object roles, palette and authority

Inputs have one red 2 and one green 3 on black 0, on different rows and columns. The canonical path travels along red's row to green's column, then vertically to green, painting 8 while preserving endpoints. Fixed numeric colors carry rule semantics here, so palette permutations are not a lawful nuisance transformation. Preserve the selected Racket authority and Python mirror; no labeling defect was found. The canonical ledger has eight usable labeled records and four unique input grids. Baseline/final authority checks and prototype default parity are execution evidence; agreement does not prove that learners infer the intended rule.

## D3 / R3: keep exact scene profiles, change their joint gap support

The twelve exact `scene_profile` values couple three canonical shapes (10×16, 12×14, 15×15), four endpoint quadrants, and near/medium/far distance regimes. Prior notes explain why this observable joint override replaced misleading partial controls. Keep the shape/palette/profile support and advertised override semantics. Difficulty remains a draw-control setting rather than a new rule.

The prior four-gap cycle was justified by unconditioned arm-only holdout failures. It accidentally synchronized with the profile/quadrant cycle: every northwest case had unit row gap, and every northeast case unit column gap. The source grammar implies the coupling; a 540-draw old-source probe and canonical Racket counterexample make it concrete. Replace it with `(both_nontrivial, unit_row_gap, unit_column_gap, both_nontrivial, both_nontrivial)`. Since 5 and 12 are coprime, each profile visits each gap phase over 60 indices. Declare `LESSON_SCHEDULE_PERIOD = 60` and verify every requested start at fixed seed 0, all three bands, every query position.

Making all gaps nontrivial would discard valid unit-arm edge cases. Randomizing gap modes without whole-lesson rejection would leave support to chance. Adding a public gap override would expose a teaching mechanism without fixing lesson assembly. The chosen deterministic schedule is reproducible and bounded, but retains positional correlations; it is not a complete cross-product of all geometries, placements or sizes.

## D4 / R4: eleven default demonstrations, preserve evidence after a holdout

Increase `EXAMPLES_NEEDED` from 4 to 11. Twelve consecutive pairs contain three occurrences of each quadrant. Those occurrences are separated by four indices, hence visit three distinct residues modulo the five-slot gap cycle. There is only one unit-row slot and one unit-column slot per cycle, so each quadrant has at least two nontrivial row arms and two nontrivial column arms. Removing any one pair still leaves both arm types in that quadrant. The fallback below only strengthens this property.

This repairs conditional arm shortcuts rather than only global arm shortcuts. It costs seven additional default demonstrations and longer episodes. Retain `MIN_IDENTIFYING_DEMONSTRATIONS = 4` and evaluate actual rivals in the lesson hook: some four-demo lessons are sufficient, but callers choosing fewer than eleven must rely on that check and receive no unconditional rotation guarantee. The existing valid four-demo frozen case is preserved. Arbitrary subset selection, multiple simultaneous holdouts, and shuffled resampling are outside the 12-pair argument.

The southeast-conditional rival is canonical-consistent and exposed a concrete old five-pair query-rotation failure. The retained input/output lesson and rival are in `checks/curriculum-before/`. Regression checks exhaust all 60 starts across bands; the two final real-Racket censuses separately measure production and every single-pair holdout. Neither census proves uniqueness against undeclared hypotheses.

## D5: preserve infeasible-unit fallback and distance branch semantics

A 10×16 far profile with unit column gap would require a row gap of at least 10, exceeding the 9 available. Keep the existing fallback to both nontrivial gaps, preserving exact profile dimensions, quadrant and distance. Do not change grid size or silently weaken the distance band. The fallback changes marginal unit-gap frequency, a documented limitation, and is directly covered by the curriculum regression.

Near/medium/far predicates are positive branch witnesses, not claims that every firing defeats every rival. Preserve `BRANCH_WITNESSES` accordingly. The new nonfar witness truthfully refutes the far-only elbow shortcut; the southeast witness truthfully refutes both the universal vertical-first and southeast-conditional rivals. The intermediate failed semantic gate is retained as evidence of why these mappings were required.

## D6 / R2: distinguish ordinary competitors from canonical-fitting shortcuts

The old universal vertical-first, horizontal-only and vertical-only competitors fit 0/8 canonical labeled records each. Keep them as semantic/lesson competitors, remove their incorrect canonical-shortcut classification. Add two actual canonical-fitting rivals: intended horizontal-first only for far Manhattan distances, and vertical-first only when red is southeast of green. Each fits 8/8 stored canonical pairs. Register them in semantic and lesson checks and give truthful generated witnesses, executed through supported `arcpuzzles apply`.

Also retain northwest-conditional horizontal-only and northeast-conditional vertical-only rivals to guard the repaired support confounds. These do not fit every canonical pair and are not called canonical shortcuts. The resulting seven distinct rivals have namespace aliases in census reports; those aliases are not additional independent hypotheses. The reusable retained probe iterates the actual generator declarations instead of maintaining a separate copied rival-name list.

## D7 / P1: one episode-level turn-order parameter

The original family priority asks for a small extension preserving the reasoning structure. Choose `turn_order ∈ {horizontal_first, vertical_first}`. This changes which endpoint coordinate is resolved first while retaining two endpoints, axis-aligned routing, fixed colors, one elbow, and shape. Default materialized rule text is byte-identical to the selected canonical target code. Reject palette variation, extra endpoints, obstacle avoidance, diagonal movement, and multi-bend routing for this prototype because they change additional assumptions or the core reasoning problem.

Resolve the parameter once per episode, explicitly or from a deterministic hash of the episode seed. Generate five common input grids, execute both settings through the real public Racket bridge, expose four labeled demonstrations and one query input. Keep parameter choice, instantiated source and query answers in separate private records. For these two settings every valid nonaligned input distinguishes the elbow, so all four demos supply direct evidence. This finite two-setting discrimination is separate from production's seven-rival/eleven-demo guarantees. Prototype status is proposed; no registry, approval, training-admission or canonical-authority changes were made.

Final seed-173 evidence and 13 parametric test cases establish exact default parity, episode consistency, public/private schema boundaries, and executable alternative outputs. Earlier prototype runs are retained as baseline/intermediate evidence, not relabeled final.

## D8 / R5: keep the frozen fixture unchanged and provide a separate proposal

DUTIES explicitly forbids rewriting `test_generator_563e1df172df.py` and requires blocked completion when its portable preflight fails. The final runtime reports its `parents[3]` path resolving outside the runtime to `/tmp/data/canonical/puzzles.jsonl`. All test dependencies were present. Retain the failure and return `completion_state: blocked`; direct new-test success is a distinct claim.

A small optional patch under `checks/optional-fixture-portability/` migrates this fixture to existing public helpers. It is syntax/application checked separately and is not part of the allowed source delta or an aggregate pass. The maintainer owns applying and executing that migration in a future packet.

## D9: evidence, solve provenance and reusable tools

Retain real red tests, the 10/12 baseline, 11/12 intermediate battery, both blocked task-test records, intermediate censuses, prototype attempts, and all genuine solve attempts. Do not invent a failed solve. The final exposed solve's repeated check and stale-public-state recovery are explicitly recorded; final consultation is conservatively yes because historical rule notes were read during metadata recovery after the first final-source solution/check. The pre-inspection blind solve remains separate, with no exposure declared and unknown hidden correctness.

Keep a minimal current counterexample in task `counterexamples/` and reusable contract tests/prototype in the task patch. Add a small standard-library evidence compressor/restorer for future reviewers. It uses the supported lossless archive schema and verifies hashes before replacing raw retained reports, with backups outside the return. This makes the bounded delta reviewable without deleting failures or shipping installed environments.
