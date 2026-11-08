Task: 832404dc8a5c (ARC training:d2acf2cb), candidate 4.0.0; assignment review-bf76c6f3e46f8419.
Defect: a grid-wide palette-direction shortcut fit every measured baseline input; controls also silently coerced or ignored invalid values.
Repair: alternate canonical profiles with mixed-direction, crossing, and endpoint-distractor diagnostics; add strict controls and executable semantic contracts.
Final generator SHA-256: 450d238a82ab2de4b6c808f5f70f966a1667cbdcbf952cf322a826d5dcc51e1d.
Checks: 48/48 task tests pass; full strict battery 11 green / 1 failed; semantic gate PASS with 6/6 witness claims and 4/4 canonical pairs accepted.
Lessons: three demonstrations plus one query; 300/300 production lessons identifiable and 0/1,200 ambiguous query rotations against 12 distinct declared rivals.
Schedule: all 8 starts at seed 0 across 3 bands; 24/24 production lessons and 0/96 ambiguous rotations; 96 pair occurrences, 21 unique inputs.
Remaining blocker: defect_lint exact finite-set object_count mismatch; preserved without waiver, sampler seed tuning, or shared-gate changes.
Authority: canonical rule unchanged (bce3d4596195); selected target_code aligned to canonical whitespace, archival raw_code preserved; execution parity PASS.
Extension: runnable endpoint_threshold prototype proposed; default parity 4/4, two settings distinguished, 8/8 parameter query rotations; no variant/training approval.
Acceptance: needs attention — maintainer must decide whether the coarse structural statistic is an intended blocking distribution requirement.

# Review and return contents

The ZIP contains the allowed source patch, runnable authoring tools, exact counterexamples, all required reports, two completed audits, both solve records, and source-bound verification evidence. It is a delta for the original packet. No shared approval or training admission is granted. `RESULTS.json` records exact commands and actual exits; the packager generates `INTAKE.json` automatically.

## Findings and patch status

| ID | Affected source | Observation and evidence | Patch / result |
|---|---|---|---|
| R1 | Main generator sampling | Grid-wide direction rival fits 4 canonical pairs and all 384 measured baseline inputs; exact final 10×10 witness differs at 18 cells. `QUESTION_ANSWER.md`, `checks/curriculum-probe-final.json`. | Repaired with diagnostic schedule; final production and rotation censuses have no declared-rival ambiguity. |
| R2 | Main override and input contracts | Coercion, ignored keys, untyped cells, undeclared texture behavior. `checks/regression-red.log`, baseline defect/override reports. | Strict controls, observable exact axes, lawful texture declarations, and negative-space grammar; 22,230 final matrix calls, zero findings. |
| R3 | Selected Racket text | Canonical and selected target_code differ only in whitespace. `checks/authority-sync-proposal.json`. | Supported selected-only alignment applied; active sources exactly agree, execution parity passes, semantics unchanged. |
| R4 | Strict structural diagnostic | Canonical train counts {4,12,32} and the 60-call generated set have empty exact intersection. `checks/structural-warning.json`. | Open acceptance blocker. Read-only diagnostic tool delivered; no shared check changed. |
| A1–A2 | Audit 9971f3a5882c | Answer-equivalent query falsely rejected; accepted tied-distance markers make a witness overclaim refutation. `checks/audit/9971f3a5882c/assessment.json`. | Findings only; target unchanged, 5 reference outputs retained. |
| B1–B3 | Audit bb1b1e111e1a | Reproduced false identical_panels invariant and unused mask_density; advertised dimension endpoints rejected with difficulty=None. `checks/audit/bb1b1e111e1a/summary.json`. | Findings only; target unchanged, 10 reference requests / 7 unique inputs retained. B1–B2 were already open findings. |

## Verification, denominators, and source identity

All **final** canonical-generator claims below bind to SHA-256 `450d238a82ab2de4b6c808f5f70f966a1667cbdcbf952cf322a826d5dcc51e1d` and exact Racket source SHA-256 `5e8bc7939bbc421cafb04acc3034fae164476344c7aa36f1f9e6cf584171343d`. Prototype claims have their own unchanged hashes in `checks/parametric/evidence/report.json`. Results are measured finite evidence, not unique-induction proofs.

| Check | Measured result | Retained evidence |
|---|---|---|
| Final portable task tests | 48 passed, zero failures/errors/skips: 38 canonical-generator cases, 6 live-Racket prototype tests, 4 curriculum-probe tests. | `checks/task-tests-final/result.json`, `checks/task-tests-final/checks/task_tests.xml` |
| Final full strict battery | 11 green, 1 failed, no pending/interrupted/advisory stages. Only defect_lint fails. | `checks/after-final/result.json`, `checks/after-final/checks/832404dc8a5c_after_battery_summary.json` |
| Semantic gate | 4/4 canonical pairs accepted; strict support 291/600; 6/6 witnesses fire and each claim is checked on 60 firing examples; 12/12 production smoke lessons, 0/48 ambiguous rotations, required policy. These per-witness samples overlap. | `checks/after-final/checks/832404dc8a5c_after_semantic_gate.json` |
| Canonical profile floor | Exact height/width/palette profile 24/60; envelope 25/60; all three bands pass. | `checks/after-final/checks/832404dc8a5c_after_profile_floor.json` |
| Override contract | 247 cases × 30 seeds × 3 bands = 22,230 calls; 19,080 accepted, 3,150 explicitly incompatible combinations, zero findings; unknown key rejected. | `checks/after-final/checks/832404dc8a5c_after_override_results.json` |
| Complete fixed-seed schedule | Seed 0, starts 0–7, easy/medium/hard: 24 production lessons, 96 pair occurrences, 21 unique inputs; zero ambiguous production lessons or rotations out of 96. | `checks/schedule-census-final.json`, companion summary |
| Larger production census | 100 lessons per band, requested starts 0–99; 300 production lessons, 1,200 unique inputs; zero ambiguity/errors and zero ambiguous rotations out of 1,200. | `checks/lesson-census-final.json.gz`, `.summary.json`, `.compression.json` |
| Exact counterexample and boundary probe | 15 Racket-labeled generated inputs, seven at 30×30; all 30 namespaced declarations (12 distinct rivals) have a counterexample; no rival errors. | `checks/curriculum-probe-final.json` |
| Separate input-only size census | Seeds 0–7, indices 0–15 in each band: 384/384 inputs valid. 31/51/30 distinct sizes in easy/medium/hard; no labels produced for this census. | `checks/curriculum-probe-final.json` → `input_size_census` |
| Structural warning reproduction | generate(sd,sd), sd 1–20 in each band: 60 calls / 40 distinct inputs, no exact canonical component-count hit. This does not prove equivalence or a semantic defect. | `checks/structural-warning.json` |

The larger census derives each seed from the first eight hex digits of SHA-256 of `lesson-census:v1:TASK:BAND:INDEX`, interpreted as uint32. Its observed seed ranges are easy 42,333,197–4,215,813,513; medium 8,326,709–4,287,340,194; hard 180,504,334–4,264,098,744. The report stores each actual seed and accepted index. Its legacy reporting residue modulus is six and it warns that the declared short schedule was not explicitly enumerated. The separate required eight-position census supplies that enumeration; neither report is silently treated as the other.

The semantic/floor/override tools choose their own deterministic cohorts; their exact recipes, seeds, and denominators remain in the linked machine reports and command records. Counts from different suites are not summed into a claim of independent samples. The rule-smoke and authority stages execute Racket; broad test-specification checks use an explicitly independent Python mirror and do not create training labels.

## Why the remaining warning is not hidden

`compare_structure` treats exact disjointness of finite observed component counts as a coarse `advisory_mismatch`; strict defect lint promotes it to a blocker. Canonical-profile generated counts in the exact cohort span 5–23; diagnostic spans are easy 20–42, medium 28–75, hard 45–126. Larger diagnostic grids are pooled with canonical profiles. Range overlap is insufficient to call the populations equivalent, so this report neither dismisses the warning as proven false nor claims the aggregate passed.

The independent review found no high or medium semantic issue in the repaired generator and advised against tuning the sampler solely to hit {4,12,32}. Baseline and current grammar permit adjacent lanes; changing that rule solely for this statistic was rejected. The actionable maintainer decision is whether component-count support is an intended task invariant or a shared diagnostic that should remain advisory after a conditioned comparison. F1 in `FEEDBACK_TO_CODEX.md` names the affected code and supplies a runnable exact reproduction. Completion is marked blocked for routine strict acceptance, with the repair and evidence complete.

## Proposed parametric prototype and tools

`repo/generators/832404dc8a5c/workspace/parametric/prototype.py` implements an episode-fixed endpoint threshold. Threshold 2 returns the canonical Racket text exactly; threshold 1 activates a line on either endpoint. Public challenge JSON excludes the setting and query answers. Both settings share parameter-independent input generation, and labels execute through Racket. The six tests and two retained episodes show default canonical parity, an exact 13-cell distinguishing input, all three demonstrations refuting the alternate setting, and all eight query rotations identifying the setting. Alternate Racket SHA-256: `929def3c74617a7ed9af1931624caa590c2e462ed716a4849a3054ffecc21f97`. This remains **proposed**, with no new approval or admission.

The task also includes two read-only tools. `workspace/probe_curriculum.py` dynamically enumerates actual rival declarations, exports exact Racket cases and mismatch coordinates, and separately measures input sizes. `workspace/probe_structure.py` reproduces the structural warning with profile-conditioned summaries. Both refuse to overwrite an existing report. The new probe's tests and independent static review are retained; the static reviewer did not claim to rerun its runtime checks.

From the extracted packet's outer directory, using a Python environment with NumPy, Pillow and pytest installed, examples are:

```bash
python3 review.py run python3 generators/832404dc8a5c/workspace/probe_curriculum.py --out ../checks/new-curriculum.json
python3 review.py run python3 generators/832404dc8a5c/workspace/probe_structure.py --out ../checks/new-structure.json
python3 review.py run python3 generators/832404dc8a5c/workspace/parametric/prototype.py episode --seed 23 --endpoint-threshold sample --private-out ../checks/new-private-episode.json
```

The last command prints a public challenge and writes author-only material separately. Review the prototype README before exporting a corpus.

## Earlier evidence, solves, and fresh replay

The before battery is retained with 8 green, 2 advisory, and 2 failed stages. The intermediate repair's battery had 10 green and 2 failed stages: the structural warning and three unmapped canonical shortcuts. Its exact source bytes and reports remain separately bound; the final mapping repair removes the latter warning. Initial expected test failures and genuine failed iterations remain in `checks/regression-red.log`, `checks/witness-regression-red.log`, and the prototype/probe red-test reports. The baseline/intermediate source snapshots include an explicit reconstruction provenance note.

Blind task a16e387b682a was solved before task-specific review: one genuine revision, 3/3 visible examples, earlier exposure no, reference consulted no. The final exposed solve uses the final generator bytes: one genuine revision, 3/3 visible examples, earlier exposure yes, reference consulted no during the solve. Both execute two masked queries; private correctness remains unknown. No artificial failed solution is represented as a natural attempt.

Fresh replay: **PASS for patch application and focused tests.** The supported command extracted 333 declared runtime/dependency files from the original 99,608-file packet (explicitly partial scope), initialized Git at the exact fresh `WORK/` root, applied the source patch, and verified all 12 changed file hashes against the reviewed workspace. The exact replayed source patch SHA-256 is `8a8bceda8a66d8596ebd05f9cf07b9f83dc8996180c1718a4490e807947b2e67`. All 48 tests then passed in 14.27 seconds using that checkout's own new Python environment and separately installed Racket, with zero failures/errors/skips. Evidence: `checks/replay/replay.json`, `checks/replay/extraction-manifest.json.gz`, `checks/replay/handoff.json`, and `checks/replay/task-tests/result.json`.

The shared replay receipt correctly ends at `patch_replay_passed_tests_pending`; the separate handoff receipt records the later successful tests. A first convenience `review.py check` invocation could not find an assignment in the sparse fresh extraction; its exit 2 is retained, and the explicit-task public `arcpuzzles check 832404dc8a5c` invocation above succeeded. The replay container is named candidate because final packaging adds these handoff receipts and completed prose. Its source patch is the exact final delta; the final archive is checked for byte equality with that tested patch before delivery.

The reviewer-created notes are authored work logs. No token-level model trace or likelihood claim is made. The full canonical ledger remains unchanged; selected authority whitespace alignment and the separate proposed extension are distinguished throughout.
