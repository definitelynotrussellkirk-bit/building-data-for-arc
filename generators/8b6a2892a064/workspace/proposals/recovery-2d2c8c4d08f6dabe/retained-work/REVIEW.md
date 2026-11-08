# Review: 8b6a2892a064

Task 8b6a2892a064; version 4.1.0; original parent training:f0f8a26d.
Final generator SHA-256: 17a221e4e5ccc47d3cfa15f0cb54b55f4b09ad3b31f7401a7e80a20bc89553e4.
Repairs: reject 33 reproduced invalid scalar cases, enforce 30x30 bounds, preserve prior valid sampling streams.
Racket authority: formatting-only synchronization of two active target_code fields; canonical rule/raw history unchanged.
Checks: all 12 after stages pass; retained focused run passes 74 tests and 19 subtests. Recovery: 79 tests + 38 subtests pass; four Racket tests were explicitly deselected and retain their earlier passing evidence.
Lessons: 3 demonstrations; 300 raw windows/1,200 pairs/1,049 unique inputs; 2 ambiguous windows and 3 ambiguous rotations remain.
Four-query probe: 3 demonstrations + 4 distinct queries, Racket-labeled; existing production checks and the new local gate pass each query.
Prototype: all 6 settings executed, each with 3 demonstrations and 4 queries; variants remain proposed.
Solves: blind and exposed records each match 3/3 visible examples; masked query correctness is unknown.
Audits: 26cfe7595a4a and 735ba14c7162, findings only.
Acceptance: needs attention.
Packaging: blocked by exhausted storage/memory; the private runtime was then OOM-killed. A verified checkpoint preserves the reviewed source and decisive evidence.

## Findings and built changes

| ID | Finding / output | Evidence | Status |
|---|---|---|---|
| M1 | Boolean/coercible scalar controls accepted | checks/scalar-red.log; checks/semantic-green.log; checks/focused-final-tests.log | Repaired; strict exact integers |
| M2 | 31-row grid admitted | checks/semantic-red.log; task tests/test_semantic_contract.py | Repaired |
| M3 | Active authority text differed though semantics agreed | checks/authority-proposal.json; checks/authority-apply.log; checks/after | Official formatting-only repair |
| M4 | Version bump altered valid deterministic draws | checks/sampling-compatibility-red.log; checks/focused-final-tests.log | Fixed by preserved sampling version |
| L1 | Three demos can leave skip_short_lines plausible | checks/ambiguous-canonical-lesson.json; checks/lesson-census-brief.json | Open sampler/census limitation; local gate rejects witness |
| P1 | Six small rule variants with executed Racket and separate counts | generators/8b6a2892a064/workspace/parametric; checks/parametric/six-settings | Proposed executable prototype |
| T1 | Large packet extraction/recovery cost | workspace/packet_tools and its 15 synthetic tests | Optional reusable tool |
| T2 | Replayable finite-rival gate over upstream labels | workspace/lesson_gate; checks/four-query-gate.json; checks/ambiguous-episode-gate.json | Optional reusable tool; nine focused tests |

## What the passing checks establish

Before repair, defect_lint and authority_sync failed, and semantic_gate was advisory NO_CONTRACT. The complete after battery passes all twelve stages. The retained focused suite passes 74 tests and 19 subtests, including the four Racket integration tests. A later portable task_tests run was observed to pass 83 tests and 44 subtests, but its log was lost when the private runtime was OOM-killed; that observation is not presented as durable proof. The fresh recovery run passes 79 tests and 38 subtests, with the four Racket tests explicitly deselected. The 74-test earlier run and 79-test recovery run together cover the same 83 distinct task test cases; the counts are not additive. Evidence: checks/recovery-tests/stdout.log, junit.xml and command-receipt.json. The battery itself does not include task-local tests. Both task-local test loaders compile exact source bytes after independent review identified timestamp-cache provenance risks.

The six retained prototype episodes execute 42 labeled pairs, including 24 query-label records. They share the same seven input layouts across settings as a controlled comparison; within each episode all inputs are distinct. Each setting's five alternatives are filtered using demonstration labels before queries run. The default emitted rule matches all four unique public canonical pairs in Racket. No hidden parameters, rules, or query answers appear in public payloads or public names.

## Limits that remain visible

The larger census matters more than the 12-lesson smoke check: two raw materialized windows remain ambiguous, with three ambiguous query rotations. The repaired declarations let automatic production reject unsupported episodes; the existing explicit-count route can return diagnostic findings, and an absent declaration previously permitted no-contract behavior. The proposed admission improvement is mandatory nonvacuous contracts across routes, using existing worker checks. No arbitrary-rotation, all-seed, or all-hypothesis guarantee is claimed.

The source approval pin was not refreshed. The production probe used the explicit research opt-in --allow-unapproved. The prototype and local gate do not approve training admission or establish a Qwen3.5-9B gain. First-census infrastructure failures and all decisive red tests remain retained, with gzip restoration metadata where needed.

Self-review: pinning SAMPLING_VERSION preserves existing valid geometry rather than narrowing it to pass tests. The prototype deliberately narrows scenes to make six nearby rules distinguishable, and that restriction is documented rather than presented as full canonical coverage.

## Reproduction and handoff

Use each tool's task-local README and the exact argument arrays/cwd/evidence paths in RESULTS.json. The retained pre-recovery focused-test log is checks/focused-final-tests.log; main after summary is checks/after/checks/8b6a2892a064_after_battery_summary.json. The local gate was freshly rerun after recovery: four-query pass (exit 0), retained ambiguous episode rejected (exit 1). The finisher has 13 passing synthetic guard tests, but has not completed a full real-archive extraction/build/replay here. Both solve directories retain their actual single attempted revision and frozen final notes. AUDIT.md and FEEDBACK_TO_CODEX.md contain the two findings-only audits and the seeded allocation analysis.

The original ZIP remains unchanged. This environment has insufficient space to restore every unchanged history file required by the stock return builder; the source hash inventory and work are preserved. This is a packaging/replay blocker, not a claimed valid official return. A recovery utility can reconstruct the original workspace, overlay the reviewed files, and invoke the untouched stock builder on a machine with adequate resources.

## Recovery provenance

The original main assignment and final generator/prototype bytes survived in the checkpoint. The completed solves also survived, and their exact generator snapshots are included under solve/source and solve-blind/source. The blind assignment is reconstructed through the original deterministic contract function. The audit target IDs and source hashes are retained, but the random audit seed was lost; its reconstructed contract declares that limitation rather than inventing a seed. The selected targets remain unchanged.

The checkpoint's compression map still described an earlier prototype batch while the six episode files were from the final source-bound batch. Recovery verified their embedded source bindings, preserved the actual retained episode bytes, recompressed them, and corrected the map. Both old and corrected map entries are recorded in checks/infrastructure/recovered-compression-map.json.


The separate convenience source patch was checked and actually applied to a minimal directory containing exact original bytes for all 15 changed paths. Every resulting hash matches the delivered overlay. Evidence: checks/infrastructure/source-patch-replay.json. This verifies the source patch only; it does not close the full stock return/replay blocker.
