# Current repair notes: b8aea529acfd

## Selected implementation

Version **2.1.0**; generator SHA-256 `5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999`.
Assignment `review-894bbef1db37ca78`. The selected rule remains crop all nonzero content, then reflect the crop left-to-right. Racket authority `8e26e8f07755` and all reference files are unchanged.

The input grammar remains one completely filled two-color rectangular body, strictly padded on a zero background, with a strict majority color and a sparse asymmetric minority motif. The general validator now rejects holes in the body. Exact profile recognition includes the ordered majority/accent roles, so swapping colors no longer masquerades as the original profile.

## Shortcuts and distribution

Two plausible rivals fit all four retained canonical input/output pairs: crop the bounding box of the most frequent nonzero color before reflecting, and infer background as the modal canvas color before cropping and reflecting. The original four `CANONICAL_SHORTCUTS` declarations were already refuted by all four pairs. They remain useful transform rivals in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`; only the two actual canonical-fitting rivals remain in `CANONICAL_SHORTCUTS`.

The original generator produced no disagreement with either new rival in a finite Python-mirror probe of 600 draws (seed 7301, indices 0–199, all three difficulty bands). This does not prove the majority-box rival had zero support; the modal-background shortcut followed from the original canvas/body sizes. Baseline witnesses and exact Racket outputs are retained in `counterexamples/` and the return's `checks/diagnosis/`.

All twelve original named profiles, dimensions, and ordered palette roles remain available. Three dense profiles were added: easy 8×9 canvas / 6×7 crop, medium 9×10 / 7×8, and hard 10×11 / 8×9. Each puts the minority color along one full vertical extreme and uses an unpaired interior accent. The majority color then fails to span the whole crop, and it is more frequent than zero on the canvas. Both new rivals disagree with the unchanged Racket rule on each ordinary dense witness.

Ordinary draws alternate an original anchor and a dense witness. The four original profiles in each band rotate across an eight-slot period. `EXAMPLES_NEEDED = 3` supports ordinary three-demonstration/one-query lessons with any of their four pairs held out. Each four-slot window contains two anchors and two witnesses; removing one pair leaves a witness in the demonstrations. Explicit `scene_profile` overrides intentionally bypass this curriculum and do not carry the ordinary-lesson coverage promise.

## Rejected iterations and duplicate handling

An initial anchor/witness/witness schedule used two demonstrations and a twelve-slot period. Its full battery failed the canonical profile envelope floor: 11/60 draws (18.3%), below 25%. The balanced schedule restores measured canonical-envelope coverage to 24/60 (40%) in the final profile-floor check, with all four canonical pairs accepted.

Independent review then found a real production collision in an intermediate balanced version: easy seed 370, start 0 generated identical witness inputs at indices 1 and 3. The assembler rejected index 3 and accepted `[0,1,2,4]`; holding out the sole witness left both new rivals ambiguous. Witnesses now alternate their full accent edge by `sample_index // 2` parity. Consecutive witness slots cannot coincide, and anchors have distinct signatures and canvas sizes. The same supported generation command now accepts `[0,1,2,3]` with no rejections; all four rotations refute all six rivals. See the return's `checks/review-collision/`.

## Verified scope

The selected source passes all twelve battery stages with required query-rotation identifiability and all **22 task test cases, zero skips**. A public Racket-backed census materialized 300 ordinary lessons (100 per band), 1,200 labeled pairs and 1,200 query rotations, with 1,155 unique inputs and zero production or rotation ambiguity against the declared rivals. Fixed seed 7301 enumerated all eight starts in all three bands: 24 lessons, 96 rotations, 33 unique inputs, zero ambiguity. These are finite results, not a claim about every possible hypothesis.

The reusable `workspace/probe_crop_contract.py` checks current declarations and validators and retains source-bound witnesses. Seeds 7301 and 91327, indices 0–199 in each band produced 1,200 draws, 1,160 unique inputs and 600 joint witnesses. Its generated labels are explicitly Python-mirror observations; authoritative labels come from the separate Racket apply and lesson-census receipts. The exact final generated seed-7301/index-1 easy witness is retained in `counterexamples/generated-crop-shortcuts.json` with its Racket result.

The new schedule makes density and edge motifs predictable. Anchors still require general crop-and-reflect behavior, both witness edges occur, and all original profiles remain reachable; this limits the introduced correlation without claiming resistance to undeclared hypotheses. No color-permutation training expansion, authority edit, audit-target edit, or training-approval change is part of this repair.

Imported associated notes and explicit audit status remain in the existing `evidence/` files. This repair does not close unrelated retained findings. The return's `REVIEW.md`, `DECISIONS.md`, and `RESULTS.json` identify final acceptance checks, intermediate failures, infrastructure interruptions, and the fresh patch replay.
## Current reviewer considerations

Source SHA-256: `5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999`.

# Repair decisions — b8aea529acfd

Final selected generator: version **2.1.0**, SHA-256 `5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999`. Selected Racket authority remains `8e26e8f07755`.

## Source bindings

| Source | Generator SHA-256 | Meaning and retained evidence |
| --- | --- | --- |
| Baseline | `b22defa3a47fdd3a5b944160a672248b1df9188eb50b1a65583b18fed6cd218c` | Original 12-profile generator; `checks/before/`, `checks/diagnosis/` |
| Rejected AWW curriculum | `daa3d65088077bc3b92285295dc0c53c6606c876ba954eada7d6e0627fcef1cb` | Period 12, two demonstrations; semantic evidence passed, profile-envelope floor failed; `checks/after/`, `checks/lesson-census.json`, `checks/schedule-census.json` |
| Intermediate balanced curriculum | `ef3d5004a125590f7af14f3fbe8bd0228532233557fde310f1d92ad8a01b1212` | Period 8, three demonstrations, random witness edge; duplicate-rejection defect reproduced in `checks/review-collision/before.jsonl` |
| Final balanced curriculum | `5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999` | Alternating forced witness edges; `checks/verified-after/`, `checks/task-tests-final/`, `checks/lesson-census-verified.json`, `checks/schedule-census-verified.json` |

Intermediate receipts remain evidence for their recorded source and settings. They are not reinterpreted as final-source passes. In particular, the green semantic results for `daa3…` do not erase its profile-floor failure, and consecutive raw-draw checks for `ef3…` do not erase its production duplicate defect.

## D1 — Teach real canonical-fitting crop distinctions

**Decision:** add majority-color-bounding-box and modal-background crop rivals to the lesson competitors, and reserve `CANONICAL_SHORTCUTS` for these two actual canonical-fitting alternatives. Both fit every labeled canonical pair. The original crop-only, crop/UD, crop/180, and whole-canvas-flip rivals are already refuted by all four canonical pairs; retain them as semantic rivals, not as canonical shortcuts.

The baseline finite probe found **0/600** generated disagreements for each new rival: seed 7301, indices 0–199 per easy/medium/hard. Generated labels in this probe are Python mirror outputs. This is a bounded observation, not proof of zero possible majority-bbox separation. Evidence: `checks/diagnosis/dense-report.json` and its reproduction script.

Reject merely expanding the rival dictionary without adding teaching inputs. Dense, fully occupied rectangles with an entire extreme accent column separate both shortcuts while preserving the task grammar. Racket-confirmed witnesses are retained in `checks/diagnosis/racket.json`, `checks/diagnosis/dense-racket.json`, and `checks/shortcut-witness-final-racket.json`.

## D2 — Balance canonical support with rotation-safe demonstrations

**Decision:** preserve all **12 original exact profile controls**, add **3 compact dense profiles** (one per band), and alternate an anchor with a witness in a **period-8** ordinary schedule. Each band rotates its four original anchors. Set `EXAMPLES_NEEDED = 3`; a three-demo/one-query lesson contains two witnesses, so holding out any pair leaves a joint witness among the demonstrations.

Reject the earlier period-12 **AWW** schedule with two demonstrations. Its `daa3…` source had strong semantic results but missed the required canonical envelope: **11/60 = 18.3%**, below **25%** (`checks/after/checks/b8aea529acfd_after_profile_floor.json` and `.log`). The final one-half anchor/one-half witness balance preserves more canonical support and passes the final battery's profile floor. `checks/profile-floor-balanced/` also retains the earlier focused balance check; its source binding remains its own.

Reject broad grammar expansion to disconnected objects, holes, or extra colors. Compact padded filled bodies already provide the needed lawful counterexamples.

## D3 — Prevent duplicate skipping from removing a witness

**Decision:** force successive ordinary dense slots to alternate full accent edge left/right using `(sample_index // 2) % 2`; keep interior motif variation seeded.

Random witness edges in `ef3…` allowed easy seed **370**, start 0, train 3/test 1 to repeat the witness at raw indices 1 and 3. Public materialization rejected index 3 and accepted **[0,1,2,4]**. Its production hook passed, but holding out the sole witness left three anchor demonstrations fitting both shortcuts. Evidence: `checks/review-collision/before.jsonl`, `rotation.json`, and `commands.json`; the red regression is retained in `checks/collision-red.xml`.

The same supported public generation on `5f2…` accepts **[0,1,2,3]**, with **zero rejections**. All four query rotations have zero hook reasons and zero ambiguity against all six semantic rivals (`checks/review-collision/after.jsonl`, `after-rotations.json`, `report.md`). Opposite full edges cannot yield identical witnesses; anchor signatures are distinct within each band, and witness canvas sizes differ from anchor sizes. Therefore the four raw positions are distinct and the duplicate-rejection problem cannot invalidate the ordinary lesson proof.

Reject a general materializer or rotation-hook change: the defect has a narrow constructive generator repair, and a hook-only rejection could turn a valid request into a failure without ensuring resampling.

## D4 — Align validation and exact controls with the declared grammar

**Decision:** enforce complete bounding-box occupancy in `self_check`, and include ordered majority/accent roles in profile signatures. The previous validator accepted interior holes despite its solid-body invariant. Its sorted-palette signature also accepted a role-swapped grid as the original profile. Portable task tests now cover both defects, canonical fit, every exact override, witness geometry, four-input uniqueness, and seed 370.

Reject relaxing the profile's color-role meaning or leaving occupancy only in the stricter helper: that would retain misleading general validation and observation contracts. Final task-local receipt: **22 passed, 0 failed/errors/skipped**, `checks/task-tests-final/result.json`.

## D5 — Preserve authority and state the evidence limits

**Decision:** leave the selected Racket rule unchanged. Its operation remains explicit black-background content cropping followed by left-right reflection. `scene_profile` is an exact input control; explicit overrides intentionally bypass the ordinary curriculum. The rotation-safe lesson claim applies to ordinary three-demo/one-query materialization, not arbitrary collections of overridden anchors.

Final source-bound evidence:

| Receipt | Result and scope |
| --- | --- |
| `checks/verified-after/checks/b8aea529acfd_after_battery_summary.json` | **12/12 green**, no advisory or failed stages |
| `checks/task-tests-final/result.json` | **22 passed**, zero skips |
| `checks/lesson-census-verified.json` | **300 lessons / 1200 rotations**, **1155 unique inputs**, no ambiguity, scoring/materialization errors, or hook warnings |
| `checks/schedule-census-verified.json` | Fixed seed 7301, every declared start in each band: **24 lessons / 96 rotations**, **33 unique inputs**, complete fixed-seed coverage, no ambiguity |
| `checks/crop-contract-final.json` | Finite Python mirror probe: **1200 draws**, **1160 unique inputs**, **600 joint teaching witnesses** |

These results concern six declared rivals and retained finite populations; they do not prove universal identifiability, exhaust all seeds, or turn the Python mirror probe into Racket execution evidence.

The broader repository run records **507 passed, 3 skipped, 1 failure** in archival-reference task `defba1ab4f90` (`checks/repository-tests-verified.log`). A targeted run on the untouched extraction reproduces the identical mismatch; the failing test and that generator match the original manifest (`checks/root-suite-baseline/report.md`). This pre-existing failure lies outside the repaired task. **See REVIEW.md for final scope and disposition.**

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-045026c983176de4:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/b8aea529acfd/generator.py,unchanged SHA256 5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999. No issue found within bounded repaired duplicate-skipping audit:seed370 all8 starts x3 bands yields24 lessons/96 rotations/33 unique inputs clean.96 Python draws,all15 exact profiles,determinism/validators and10 real Racket labels(4 canonical/6 dense) pass. Fixed-seed support proof is not every-seed/undeclared-rival certification;explicit overrides bypass curriculum by design. No target edit or new approval. No owner audit rerun or new target approval. Target-local receipts: `checks/audit/b8aea529acfd/AUDIT.md` `checks/audit/b8aea529acfd/census.json` `checks/audit/b8aea529acfd/census.summary.json` `checks/audit/b8aea529acfd/commands.json` `checks/audit/b8aea529acfd/expected.json` `checks/audit/b8aea529acfd/input.json` `checks/audit/b8aea529acfd/probe.json` `checks/audit/b8aea529acfd/probe.py` `checks/audit/b8aea529acfd/racket.json` `checks/audit/b8aea529acfd/verification.json` `checks/audit/b8aea529acfd/verify.py` `checks/audit/b8aea529acfd/witness-rivals.json`

### Assessment or prior finding

## b8aea529acfd

**No issue found within the tested scope.** Findings-only audit 1 for immutable assignment `review-045026c983176de4`; no selected generator, rule, notes, catalog, or shared source was edited.

### Source binding and inspection

- Generator version `2.1.0`, SHA-256 `5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999`.
- Selected executable rule hash `8e26e8f07755`; full selected-rule SHA-256 `8e26e8f07755275993a3cc2f3a1e95d3c3ff2dc44c4bd7d008bc376c9fe73c33`. The public apply receipt separately records rule-text SHA-256 `b599713c7e7b3883413720d1d05ef4f24675cbd9c397fc46272a9285b7f41049`.
- Read the selected generator, current notes, canonical ledger row, solution record, current `evidence/review_index.json`, and relevant associated notes. The current index has no explicit audit entries. Retained reports were treated as provenance, not as rerun results.

### Tested scope and observations

The adversarial target was the earlier duplicate-skipping failure: easy seed 370 previously lost its second witness and became ambiguous under query rotation. The public Racket-backed `lesson-census` now materialized all eight declared starts at seed **370** in each of easy, medium and hard: **24 lessons, 96 labeled pairs, 96 query rotations, 33 distinct inputs**. Production and rotation status are both `no_ambiguity_found`; materialization/scoring errors and hook warnings are zero. This is complete fixed-seed start coverage, not all-seed coverage.

An independent retained Python probe exercised seed 370, indices **0–31** per band (**96 draws**), determinism, both validators, all **15** exact profile controls, and four-pair windows at starts 0–7. All checks passed. These generated observations use the Python mirror; they are not represented as 96 independent Racket calls. All **48** dense draws separated both canonical-fitting shortcuts; all four canonical labels fit both shortcuts. The four simpler transform rivals are already refuted by canonical labels and are not relabeled as canonical-fitting shortcuts.

Public `apply` executed the actual selected Racket rule on all **four canonical pairs** and **six generated dense witnesses** (indices 1 and 3 in each band). All ten outputs exactly matched the retained expectations, and the generator-domain checks accepted them. Every one of the six exact generated witnesses disagrees with all six declared semantic rivals. Inputs, authoritative outputs and exact rival outputs are retained in `input.json`, `racket.json`, and `witness-rivals.json`.

Source inspection supports the specific repaired schedule claim: four consecutive ordinary positions contain two witnesses; their forced opposite full accent edges prevent duplicate inputs, anchor signatures differ, and dense canvas sizes differ from anchors. Removing any one of those four pairs leaves a witness against both crop shortcuts.

### Limits and evidence

No additional source-bound defect was reproduced. Explicit profile overrides bypass the ordinary curriculum by declared design; validator-only acceptance and arbitrary off-distribution grids were not counted as generated support. Dense-edge/palette correlations remain disclosed distribution limits. This audit does not certify resistance to undeclared hypotheses, every seed, arbitrary lesson sizes, or training admission. No full battery or task-local test suite was rerun.

Reproduction commands and exit codes: `checks/audit/b8aea529acfd/commands.json`. Main receipts: `probe.json`, `census.json`, `census.summary.json`, `racket.json`, and `verification.json`; runnable probes: `probe.py`, `verify.py`. All paths in this paragraph are beneath `WORK/`, with receipt basenames relative to this audit directory.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## D6 — Native reflection-policy family (2026-10-24)

**Decision:** keep `generator.py` and the exact canonical Racket program byte-identical, and add a task-local native parametric family whose episode-fixed `reflection_policy` is `left_right`, `top_bottom`, `long_dimension`, or `short_dimension`. The canonical default remains `(rule! (lambda (g) (flip-lr (crop-to-content g))))`.

The conditional policies implement a real dependency: crop the foreground, measure the cropped body's row/column dimensions, then choose the reflection from that result. The first two demonstrations put a wide crop on a tall canvas and a tall crop on a wide canvas, so an outer-canvas-aspect shortcut cannot fit the lesson. Episodes support 2–6 demonstrations, exactly four distinct queries, strict private/public projection, and two substantive 30×30 query inputs.

Fresh retained evidence: **21 focused tests** and **43 staged task tests** passed; native protected-Racket qualification passed all four settings on seeds 0 and 17 at demonstration counts 2, 3, and 6 (**24 jobs total**); the two-case protected-Racket counterfactual replay performed four evaluations and changed both final outputs when crop-derived aspect was replaced by canvas aspect. The generator SHA remains `5f2c9d9237f759ae3b52d75e7c9eb1d3e7b801e554713d55ff3e265061c1d999`; the source inventory SHA is `ecbc779d1b2a5e16e68aa976650ac6ede1da5301cb832ca521be3dd52953c889`.

**Limits / next action:** qualification and the causal witness are finite source-bound reviewer evidence, not universal identifiability or training benefit. Status is `ready`, not accepted. After integrating these exact bytes, the owner must rerun native qualification and fresh acceptance before use or training admission.

