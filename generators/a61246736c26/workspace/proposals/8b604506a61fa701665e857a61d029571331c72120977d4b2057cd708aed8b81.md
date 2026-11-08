a61246736c26 v4.1.0 — repaired a swatch-row shortcut and malformed-grid validation; added a separate parametric prototype.  
Repair: nonzero same-row support, permuted/mixed-row teaching witnesses, three executable rivals, literal identifier checks, and observable profile provenance.  
Final generator SHA-256: `f6be3b037fc2bd515ed0a12602eaf9d6873f563b0ed26f0b84ac5a51d25f2e45`.  
Racket authority unchanged: `08238424436c`; original family `training:15660dd6`; no approval or audit-status edits.  
Final checks: strict battery 12/12 stages; portable task tests 43 passed; override contract 1,530/1,530 accepted draws, zero findings.  
Teaching policy: five demonstrations plus one query; six-position default schedule; arbitrary single-query holdouts checked against three declared rivals.  
Production census: 300/300 lessons, 1,800 pairs, 1,766 unique inputs; zero production ambiguities and zero ambiguities in 1,800 query rotations.  
Fixed-seed schedule census: all six starts in all three bands, 18 lessons and 108 rotations; zero ambiguity/error; 25 unique inputs.  
Canonical support: exact profile 29/60, envelope 43/60; semantic-manifold strict check 600/600. Finite declared-rival coverage is not universal identifiability.  
Solve: final-source visible examples 5/5; two masked queries executed, correctness unknown; earlier exposure yes, references during solve no.  
Replay: 11 changed paths verified; fresh focused tests 43/43 passed; declared runtime closure, 369 of 87,941 original files. No repair blocker remains.  
Acceptance: routine — canonical repair complete; the separate parametric extension remains a proposed prototype.

# Repair and evidence

The selected baseline was version 4.0.0, source `33e5c3a10739251440d40b658e523234ff2ef3fe823b9fbe76f74a1717a41767`. I used the retained `review-66a96f3e3fde9097:v0001` and `review-e3fe90a3dfb3e6d7:v0001` audits as leads, then reproduced their findings against those pinned bytes. Their explicit prior statuses remain unchanged.

| ID | Finding and repair | Decisive evidence | Status |
| --- | --- | --- | --- |
| R1 | Baseline same-row scenes always selected frame 0, teaching an incorrect shortcut. Added top/middle same-row profiles, joint swatch permutations, and explicit rivals/witnesses. | `checks/regression/before/`; `checks/regression/final-f6be/`; task-local `workspace/probe_joint_swatch_support.py` | Repaired; 576/576 final explicit-profile inputs valid; same-row frames 0,5,9 in every band. |
| R2 | A malformed separator could raise IndexError inside the validator. Stop after structural findings before indexing tile interiors or calling the mirror. | Baseline literal witness and separator sweep under `checks/regression/before/`; `tests/test_review_regressions.py` | Repaired; focused tests included in 43 passing portable tests. |
| R3 | The first three-demo/four-position repair taught two rivals but admitted a conditional third rival. Replaced it with five demos/six positions and mixed-row deranged palettes. | `checks/lesson-review-intermediate/finding.json`, `racket.json`; `counterexamples/conditional_swatch_shortcut.json` | Exact four-pair lesson retained; final checker flags it; final production and rotation censuses pass for the three declared rivals. |
| R4 | Literal identifier coercions triggered 33 strict defect-lint warnings. Reject bool, float, string, None identifiers and negative sample indices. | `checks/before/`; `checks/contract/red.log`; `checks/after-final/` | Repaired; unrestricted literal integer seeds retained because public gates use large seeds. |
| R5 | Four scheduled paths omitted keyed scene-profile provenance. Record a singleton choice using the public context API. | `checks/after/` failed override stage; `checks/override-diagnosis/`; final override log | Red-to-green regression; 792/792 pre-fix/current grids identical; final override matrix passes. |
| R6 | Existing selected-task tests assumed a nonportable repository path and a private module alias. Migrate that editable task-local file to public reviewer helpers. | `checks/task-tests-before/`; `checks/task-tests-f6be/` | Repaired; no frozen root fixture was edited. |

All patch files belong to `repo/generators/a61246736c26/`. Canonical catalog/data, shared runtime/tools, assignment contracts, and both audit targets remain unchanged. The original selected assignment's approval flag does not transfer approval to these changed bytes.

## What was built

The canonical generator now supplies complementary demonstrations: same-row scenes with frames 5 and 9, mixed-row scenes under both deranged palettes, and exploratory scenes that retain every public profile and the broader constructor family. Explicit `scene_profile` controls bypass the lesson schedule and remain observable; they do not carry the default lesson guarantee. Four-column tiles are limited to size 5 or 6 so input width stays at most 29.

The reusable task-local support probe discovers current rival declarations rather than copying a stale name list. It reports three unique implementations across nine namespace bindings, checks all usable canonical labels, and separates independent Python support measurements from actual Racket evidence.

The separate `workspace/parametric/prototype.py` implements `stroke_symbol ∈ {2,8}`, selected once per episode. Setting 2 returns the exact canonical program; setting 8 recolors interior 8s instead of 2s. The frame, solid-tile lookup, duplicated pattern, and lattice composition retain their original roles. Exact programs, clean public challenges, private labels, actual execution records, parameter rivals, and a README command are included.

Parametric final evidence: see `checks/parametric/commands.json` and `checks/parametric/final-f6be-evidence/report.json` and `checks/parametric/final-f6be-integrity.json`. The completed final-source check covers six episodes, both settings across three bands, 24 labeled pairs, 16 distinct inputs, and 54 actual Racket applications. It found no ambiguity in 12 production rival checks or 24 holdouts/48 holdout-rival checks. Integrity verification checked 9 source bindings, 19 artifact hashes/sizes, and 6 clean public challenges. Each prototype episode has three demonstrations and one query; this two-setting claim is separate from the canonical five-demo policy.

## Verification and limits

The exact final commands and exit codes are indexed in `RESULTS.json`. The final large census and schedule census are retained losslessly, with small readable summaries beside them. `checks/evidence-compression.json` and `checks/restore_evidence.py` describe and verify restoration of compressed reports.

Final profile support is 9/20 exact and 13/20 envelope in easy, 12/20 and 20/20 in medium, and 8/20 and 10/20 in hard. The 600/600 strict semantic-manifold rate means all sampled inputs satisfied the declared lattice/swatch manifold; it is a different measurement from exact canonical shape-and-palette support.

The 300-lesson census uses the public production assembler and its source-bound seed recipes. Each lesson has five demonstrations and one query; every one of its six pairs is also held out once. The fixed-seed census exhausts all six start residues at seed 0 in each band. These populations overlap, so their unique-input counts must not be added. They do not establish every seed, every palette-conditioned rival, or universal induction.

Self-review found that same-row swatch witnesses alone permitted the branch rule “read the strip only for same-row scenes.” The retained counterexample motivated the mixed-row witnesses and longer schedule; the final finite checks cover that third rival, while untested branch-conditioned hypotheses remain outside the claim.

Both findings-only audits are in `AUDIT.md`: `3ae696dbdba9` has an asymmetric shape witness against a repeated-row shortcut; `cc90240d0045` has a missing-corner ring witness, override inconsistencies, and validator type failures. They are recommendations for those targets, not repairs or automatic audit closures.

## Honest history

The return retains the original failing battery and regression tests, the intermediate conditional teaching failure, the failed provenance battery, and the prototype's real aliasing failure with its source snapshot. The earlier 55a post-repair solve remains under `checks/prior-solve/55a/`; the current `solve/` was freshly prepared from final f6be bytes. Both ordinary solve attempts used intent `solve`; no failed solve was manufactured.

The separate blind task `4f1ec6a61342` was completed before task-source inspection: 3/3 visible demonstrations, two masked queries executed, no earlier exposure or reference consultation. It is not a correctness claim about masked answers. All solve notes are assistant-authored work logs, not token-level model traces.

Infrastructure failures—including initial inode-limited extraction, a missing schedule receipt in an early invocation, and any prototype temporary-space retry—are retained with their actual outcomes. They are distinguished from generator or assertion failures. A final packaging attempt also caught a WORK-relative directory in the task-local command index; `checks/packaging/` retains the rejection and pre-fix index, and the index now records packet-relative directories while preserving the actual absolute locations.

## Fresh delta replay

The official public `review replay-return` applied the candidate return's exact source patch to a new extraction of the original packet, confirmed the Git root was the fresh `WORK/`, and checked all 11 changed paths against the reviewed working tree. The supported `--runtime-closure` mode extracted 369 of 87,941 original files. This was a declared dependency closure, not a full second extraction. The official replay receipt retains its truthful `patch_replay_passed_tests_pending` status because that command does not execute returned code; the separate fresh test receipt completes that obligation.

The fresh checkout's own Python environment ran all selected-task tests: **43 passed, zero failures, errors, or skips** (51.40 seconds reported by pytest). Repository, runtime, and selected-generator imports resolved within the fresh checkout. To fit the constrained temporary filesystem, 301 unchanged dependency files were reused through content-verified hardlinks after the official extraction. Every selected-task file remained independently copied. Existing third-party Python packages and the Racket executable were reused, with paths and versions recorded. Post-test verification confirmed that all changed files still matched, all selected-task copies remained independent, and the reused dependency contents were unchanged.

Evidence is in `checks/final-replay/`: `replay.json`, `focused-tests.log`, `focused-tests.xml`, `POST_TEST_INTEGRITY.json`, environment/source-provenance receipts, exact command records, and reusable setup/verification scripts. `checks/final-source-binding.json` binds the tested delta SHA-256 `8b604506a61fa701665e857a61d029571331c72120977d4b2057cd708aed8b81` to the final generator and every changed file. The delivered package carries the same source patch; final packaging updates only reports and evidence. The canonical rule, approval flags, and both audit-target sources remain unchanged.
