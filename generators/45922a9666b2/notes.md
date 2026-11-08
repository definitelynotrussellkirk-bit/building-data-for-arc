# Current decisions: 45922a9666b2

## Rule and authority

Version 3.1.0. Every bottom-row red (2) cell starts a separate path. Read the original input: prefer up when that cell is not gray (5); otherwise move right when possible; stop at the top or when neither move is possible. Paint all visited cells red. Fixed background 0 and obstacle/start roles are intentional.

The canonical ledger and RULE_HASH `26a6c2419e6e` are unchanged. Both selected base target-code fields now contain that exact canonical program. The equivalent archived target used `cell-at`/`grid-from-fn`/`nth`; a manual equivalence review justified reconciliation to `at`/`cellmap`/tuple accessors on valid rectangular grids. Archival raw_code is unchanged. Derived primitive_chain was updated; family_chain is unchanged.

## Distribution and teaching

Preserve all four complete published profiles: 13×14, 12×13, 13×15, 13×13; exactly three disjoint bottom starts; linked turn counts, stopping types and terminal rows; fixed gray mass and palette {0,2,5}. Procedural draws vary start columns, turn rows and nuisance obstacles. Exact scene_profile and route_layout overrides remain observable. Difficulty weights remain 30/40/15/15 (easy), 25 each (medium/default), 15/15/35/35 (hard).

Prior default: independently choose canonical route layout at 15%, procedural at 85%. Reversal: use canonical at sample_index % 6 == 0 and procedural at the other five residues. Baseline seed4, indices46..49, medium supplied three canonical demonstrations followed by a procedural query; a shape-to-published-route lookup fitted all demonstrations but missed the query. Retained counterexample: counterexamples/canonical-mask-lesson.json. The period-six schedule retains exact support and supplies at least two procedural demonstrations after any one-pair holdout from four consecutive draws.

EXAMPLES_NEEDED=3 is literal. The executable lesson contract checks the memorized canonical route mask plus straight-up, left-turn and right-first rivals. Only the route-mask rival is claimed to fit canonical examples (8/8 labeled pairs). Procedural layouts refute that rival under the fixed role profiles; workspace/probe_route_mask.py exhausts same-mask path decompositions. Explicit canonical-only overrides and arbitrary nonconsecutive sampling are outside the schedule guarantee.

Seed must have exact Python int type; sample_index must additionally be nonnegative. Negative integer seeds and large integers remain valid; booleans/floats/strings are rejected before context construction. No shared runtime behavior was altered.

## Retained authoring tools

workspace/probe_shortcut_lesson.py evaluates the live declared rivals and emits exact inputs for public Racket apply. counterexamples/canonical-mask-final-witness.json is a final-source generated witness (seed4, index49, medium), with authoritative output and the competing mask output.

workspace/parametric/prototype.py proposes turn_direction=right|left once per episode. Right is exact canonical text; left is its horizontal-reflection conjugate. Labels are executed Racket, and demonstrations must distinguish the two declared settings. Public filenames depend solely on public contents; stale seed-named exports are rejected. Runtime bootstrap respects RUNTIME_MANIFEST and source isolation. This is a prototype, not an approved canonical change.

workspace/diagnostics/ contains a safe preparation-stage classifier, synthetic regressions, and a passive shared-tool patch. Shared code was not modified.

## Limits and status

Final canonical battery: 12/12 green. Final portable task suite: 30/30 pass, no skips. Final 100-per-band census: 300 lessons, 1,200 distinct inputs, 1,200 rotations, zero declared-rival ambiguity/errors; separate seed0 schedule enumeration: 18 lessons, 72 rotations, 14 distinct inputs. Source-bound receipts and full counts are in the returned checks/; the final handoff review records fresh-replay results.

No arbitrary-size, new-palette, altered role-count, or universal rule-identification guarantee. Larger queries and alternative role quotas remain future domain decisions. Mirrored prototype geometry can correlate with direction. Neither passing checks nor the prototype changes training admission. Audit-only targets were left untouched. The unrelated blind task's nonliteral demonstration declaration blocked preparation and remains documented; it is not a canonical repair failure.

## Current owner source and evidence limits

Accepted the period-six canonical/procedural schedule, exact scalar guards and executable shape-mask rivals. The canonical ledger and rule pin are unchanged. The reviewer reports 12 green battery stages, 30 portable tests repeated in a fresh 351-file dependency closure, 300 lessons with 1,200 clean rotations, and 18 fixed-seed lessons with 72 clean rotations. Two selected target texts now equal the canonical source; derived primitive chains changed too. The owner verified the exact JSON changes and preserved archival raw_code. Tokens differ: equivalence of cell access, list selectors and cellmap is reviewer-reported for rectangular nonempty grids, with the authored proof retained. The right/left direction prototype has two complete episodes, canonical parity and opaque public filenames. The unrelated blind task remains blocked by its nonliteral demonstration declaration. Safe diagnostic and shared patch remain passive proposals. Geometry/direction correlation and the four linked profiles remain limits. No variant or training approval.
## Current reviewer considerations

Source SHA-256: `901b35aa8aaf523990096af8ecfae1e4dac10f9fdfa84b21557c7179e8b52fac`.

# Decisions and limits

## D1 — preserve the original reasoning structure

The selected family is a scene of three independent up/right walkers driven by gray obstacles. Each step depends on the current position and the original grid; painting a previous path cannot change another path's decisions. The four existing complete role profiles couple canvas shape, path turn quotas, terminal types/rows, and gray count. We retained that domain rather than treating each number as an independently combinable control. Evidence: canonical tests, unchanged rule pin, and final profile-floor receipt under checks/after-final/.

The original motivation for every profile restriction is not recorded in the placeholder notes. Canonical support establishes that the linked configurations are relevant, not that those restrictions are universally necessary. No unsupported historical rationale is invented.

## D2 — lesson-level layout schedule

The previous 15% independent canonical-layout choice admitted a real teaching defect. On baseline version 3.0.0, seed 4, start46, medium, the first three layouts were canonical and the query procedural. The shape-specific route-mask rival fitted all eight labeled canonical pairs and all three demonstrations, then failed the query. Canonical Racket application confirmed all four outputs (checks/baseline-shortcut-racket.json); the full failed lesson is retained.

New policy: three demonstrations, one query in census/contract testing, four consecutive sample indices. Use a six-index layout period: one canonical then five procedural. Production uses the first three as demonstrations and the fourth as query. Required rotations hold out every one of those four pairs and preserve the order of the other three. The exposed solve/prototype additionally use two queries; neither is counted as extra census rotations.

Every four-index window contains at most one canonical layout; any held-out pair leaves at least two procedural demonstrations. The finite structural probe enumerates every monotone route inside each canonical mask under the fixed per-role turn and stopping constraints: candidate decompositions 2/8/9/2 across the four profiles, with exactly one valid canonical decomposition each. Fixed terminal rows and turn counts fix total route cardinality. An identical output under the mask rival would require identical route unions; the unique decomposition contradicts a procedural layout. This establishes the specific mask guarantee, not universal induction. See checks/template-structure-final.json and workspace/probe_route_mask.py.

Rejected alternatives: merely increasing random procedural probability leaves a nonzero bad-lesson event; increasing demonstration count alone does not guarantee a negative example; removing canonical support sacrifices a useful supported layout; arbitrary post-label resampling obscures distribution and introduces retries. The chosen schedule controls only semantic layout, leaving profile/geometry/obstacle randomness intact. Version 3.1.0 intentionally changes the seeded sequence from 3.0.0. The later scalar-validation correction kept 3.1.0 and did not alter valid-input RNG behavior.

Exact route_layout overrides are intentionally allowed. Forcing canonical layouts can recreate the counterexample; lesson_identifiable reports it rather than pretending such overrides inherit the default schedule guarantee. Nonconsecutive example selection and undeclared rivals remain outside the claim.

## D3 — distribution and API decisions

Retain scene_profile weights: easy 30/40/15/15, medium/default25/25/25/25, hard15/15/35/35 in the declared profile order. Fixed dimensions range12–13 rows and13–15 columns. All 60 profile-floor draws were exact canonical shape/color-count hits,20/20 per band; the strict semantic sample accepted 600/600 grids. Those results establish the tested domain, not scale generalization.

We did not add height/width or palette controls: scaling only the canvas without new path roles could introduce padding shortcuts and was not necessary for the demonstrated defect or the semantic parameter. A future extension should justify changed turn/terminal quotas and show distinguishing lessons at larger sizes. No larger-query evidence is claimed.

The strict-scalar checker exposed accepted booleans/floats/strings and negative indices. Added exact-int validation before gen_ctx, with nonnegative sample_index. Integer seeds, including negative/large integers, retain the base API's domain. Actual red/green regression:2failed+1passed, then3passed; evidence checks/strict-scalar-*.xml.

## D4 — canonical authority reconciliation

The canonical ledger and RULE_HASH remain unchanged. The selected training and augmented base JSON target programs used a semantically equivalent legacy expression. Public authority-sync refused automatic synchronization because tokens differed. We reviewed equivalence manually: nested list indexing is unchanged; four-element states make nth0..3 equal first/second/third/fourth; cellmap expands to the same row-major construction over the original grid. Eager cell reads differ only for malformed/effectful inputs outside valid rectangular ARC grids.

Only racket_target.target_code and derived primitive_metadata.primitive_chain changed in the two selected files. Both archival raw_code values retain SHA a77991e0359e6569981b9f0b544a2c35136128bde226541e18e9b0bdf6fefcac. Family chain is unchanged. The exact canonical source SHA is cb5498c6b165919ba60e3efff8286d9b5b580c1d8c384fc578014cf7912d7763; its executed callable SHA is 8e87d0aca9631812390f9ba54f4a8ba1bc23c3deffc5fccb241ef9f01fed5d4b. The final authority-sync, rule-smoke and Racket-lint stages pass. See checks/authority-reconciliation.json. This is an explicit selected-execution-text reconciliation, not an unreported reference edit.

## D5 — one semantic parameter, proposed only

turn_direction chooses right (canonical default) or left once per episode. Right returns byte-exact canonical program text; left reflects input, applies that program, then reflects output. This preserves upward priority, independent original-grid reads, color roles, turns and stopping structure. Left inputs reflect supported right scenes, reversing horizontal role order; they are not claimed as canonical production-profile inputs.

Each episode has three demonstrations and two queries. Sampling is deterministic and bounded; the first demonstration must distinguish directions and only the chosen direction may remain consistent with all demonstrations. All labels and rival evaluations execute Racket. Final evidence checks eight canonical pairs, eight profile/layout combinations, two complete episodes/ten pairs, and one same-input direction witness. Both opposite directions are refuted by all three demonstrations. See checks/parametric/final-export/receipt.json, verification.json, and the task's parametric README.

Code review found public filenames initially leaked seed parity and hence direction. Content-derived public filenames now hash only public JSON bytes, and a reused directory with legacy filenames is rejected before writes. A staged CLI test exposed a second issue: mirrored shared/runtime dependencies are not the selected execution dependencies in portable layouts. The bootstrap now follows RUNTIME_MANIFEST and retains the official source-tree guard. Real failed checks and prior exports are preserved; current exports are only under final-export/.

Limits: two parameter rivals, two episode seeds, four fixed profiles, no larger-grid evidence, and possible orientation/direction correlation. Share only public challenge files with solvers; authoring receipts intentionally retain private labels. This prototype does not obtain variant or training approval.

## D6 — evidence, solve lanes and acceptance

Initial blind target6e175c009c2a was blocked before materialization by a nonliteral EXAMPLES_NEEDED declaration. No visible puzzle existed, so no answer or failure hypothesis was fabricated. Its source/guards were not changed. The finished blocked lane remains authoritative. A safe diagnostic/shared reporting proposal is separate from canonical repairs.

The required postrepair solve is explicitly exposed, with no reference consulted during its visible-only phase; query correctness remains withheld. Earlier source-bound solves and any stale/mixed-source restart artifacts are retained under checks/. Only the clean final source-bound lane is used for current solve metadata. These are concise reviewer work logs and program revisions, not captured token-level model transcripts.

The final handoff checks apply the exact generated delta to a fresh extraction's declared runtime closure and rerun focused tests in that checkout's own environment. REVIEW.md and RESULTS.json record the actual final outcome and extraction scope. Immutable assignment/audit draws, frozen baselines, shared runtime and unrelated generators remain unchanged.

## Two-sentence self-review

The period-six layout schedule still correlates dimensions with the original fixed role profiles, and explicit layout overrides can remove a needed counterexample; the default/consecutive-only guarantee and unresolved role-quota/size hypotheses are therefore explicit. The direction prototype supplies executed demonstrations that separate its two settings, but mirrored input geometry may reveal direction, so its finite evidence is proposed authoring support rather than a claim of shortcut-free generalization.
