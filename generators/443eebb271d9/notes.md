# Working notes: 443eebb271d9

Final selected generator SHA-256: `ba9fea17e935d9d09ebcd6fb761a4d7350fa932337efda1bc91e152ff97c69bb`; version `4.0.0`; canonical `RULE_HASH = 9a8ad7e4958a`.

## Intended rule

A single color-7 glyph defines a bounding-box lattice with one blank row and column between copies. The complete first lattice row is drawn; horizontal instances 2, 5, 8, … (zero-based) are recolored 6 and only those instance columns repeat down later lattice rows. The selected Racket semantics did not change.

## Current native parametric handoff

The task-local adapter supports episode-fixed special_period 3 or 2,
2–6 demonstrations and 1–4 distinct queries, centered on three/four. Canonical
source and authority are unchanged. Input streams match across settings and
retain demo/query prefixes when counts change. The exact default lives in
workspace/parametric/canonical.rkt.

Current authoring evidence: workspace/parametric/evidence/native-final/.
Protected Racket checked 18 episodes / 138 labels; six two-demo lessons reject
all 13 declared rivals, including the repaired only-third-copy ambiguity.
The original seed-2 lesson and both Racket interpretations are retained in
WORK/checks/443eebb271d9/ambiguity-before-repair.json; the second demo now
exposes the sixth copy without increasing its count. The 30x30 query varies
over 70 lawful shape/origin choices. Current focused tests: 52 passed.

The first native authoring attempt exposed a bare-lambda/native rule! contract
mismatch; the alternate program is now wrapped and a regression exercises the
real normalizer. Public views have visible-byte hash names and one query only.
Serve one file per turn; never expose the staging pool. Old setting-named public
examples are superseded historical evidence.

Native qualification and source-bound causal replay accompany the return;
owner acceptance on exact integrated bytes remains pending. No training
admission. The existing frozen task-test fixture canonical-path preflight
still fails; its unchanged source is not a passing aggregate result.
See the workspace README for commands and finite-check limits.

## Repair decisions

- The prior independent audit lead showed a teaching shortcut: demonstrations could all be connected while a disconnected query was answered by the full bounding-box glyph. A “largest 4-connected component only” rival therefore fit every demonstration and changed the query.
- Ordinary generation now uses a seed-rotated four-slot schedule: canonical connected, low-fragmentation disconnected, general connected, high-fragmentation disconnected. Every four-pair window has exactly two disconnected witnesses; every three-demo holdout of that window retains at least one.
- Added `split_bar` and `split_corner` as two-component witnesses. Retained broader disconnected shapes for diversity. Removed the redundant `cup` profile so the declared enum remains within the framework's 16-value probe cap.
- Seed rotation uses a four-state Gray-code offset. This preserves the curriculum while keeping both fixed-index and diagonal seed/index streams diverse.
- `generate` and `schedule_profile` now reject non-literal seeds/indices and negative sample indices.
- Added executable rival/witness declarations and `lesson_identifiable`; labels still come only from the selected authority.
- The selected authority file's `racket_target.target_code` was synchronized textually to the canonical multiline program. Tokens, behavior, archival `raw_code`, and rule hash are unchanged.

## Evidence and limits

The final strict battery is 12/12 green at `checks/after-final2/`. The source-bound census materialized 300 lessons (100/band), 1,200 pairs and 1,200 query rotations with zero ambiguity or execution errors and 806 unique inputs; see `checks/lesson-census-final.summary.json`. This is finite named-rival evidence, not proof against every possible hypothesis.

The isolated `workspace/parametric/` prototype varies the episode-level special-column period between canonical 3 and proposed 2. Both live-Racket settings are reachable and demonstration-distinguishable; it is not selected or approved production behavior.

The 13 new permitted tests pass. The official portable `task_tests` stage remains blocked by the unchanged inherited frozen fixture `tests/test_generator_443eebb271d9.py`, whose fixed path expects `data/canonical/puzzles.jsonl` beneath the task in the staged runtime. Per assignment policy, that fixture was restored byte-for-byte and left for maintainer migration.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ddcbd409ea699054:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `3834c7e2571f5ba5f40ae1b8e9835be808079565e2156568a0018ed20c1f9aaa`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved by accepted source ba9fea17e935d9d09ebcd6fb761a4d7350fa932337efda1bc91e152ff97c69bb, based on reviewer-reported repair evidence from review-263d7c68d7b23715:v0001; no owner rerun. Four-slot curriculum with two disconnected witness classes, executable largest-component rival, 13 focused tests and 300 lessons/1200 rotations. See checks/focused-tests-final/new-tests.log and checks/lesson-census-final.summary.json. Generic defect-lint and frozen-fixture limits remain as recorded; no other audits are cleared.

### Assessment or prior finding

## 443eebb271d9

**Classification: reproduced lesson ambiguity (`A-443-1`).** Current source SHA-256 is `3834c7e2571f5ba5f40ae1b8e9835be808079565e2156568a0018ed20c1f9aaa`; declared rule hash is `9a8ad7e4958a`.

Medium seed `2`, sample indices `0,1,2,3` produces three connected training glyphs (`hollow_square`, `aitch`, `tee`) and a disconnected `diamond` query. All four grids pass the target validator and are in its documented domain. The rival “take only the largest row-major 4-connected color-7 component, then perform the same bbox-periodic repeat, every-third recolor, and vertical extension” matches **3/3 demonstrations** but disagrees with the Racket query answer in **62 cells**. It also fits the two visible canonical training pairs and is refuted by the labeled canonical query, so this is an undeclared lesson/solver rival rather than a canonical shortcut.

Evidence: `checks/audit/443eebb271d9/lesson.jsonl`, `input.json`, `racket.json`, `probe.py`, and the self-contained `counterexample.json`. The target source was not modified.

Reproduction from the extracted packet root:

```sh
python3 review.py run python3 -m arcpuzzles generate 443eebb271d9 --count 1 --seed 2 --sample-index 0 --difficulty medium --train 3 --test 1 --allow-unapproved --timeout 300 --out ../checks/audit/443eebb271d9/lesson.jsonl
python3 review.py run python3 -m arcpuzzles apply 443eebb271d9 --input ../checks/audit/443eebb271d9/input.json --out ../checks/audit/443eebb271d9/racket.json
python3 review.py run python3 ../checks/audit/443eebb271d9/probe.py
```

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ddcbd409ea699054-v0001/audit_assets.json), manifest SHA-256 `3b3a90abc9803c04ac59c9d66324e56b00cd6727bed274ca5a2e7f5645538379`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `ba9fea17e935d9d09ebcd6fb761a4d7350fa932337efda1bc91e152ff97c69bb`.

# Decisions — 443eebb271d9

All final selected-source decisions are bound to generator SHA-256 `ba9fea17e935d9d09ebcd6fb761a4d7350fa932337efda1bc91e152ff97c69bb` and unchanged canonical rule hash `9a8ad7e4958a`.

## D1 — Preserve the ARC transformation; repair the lesson distribution

**Original rationale:** The baseline rule mirror, selected Racket authority, and canonical outputs already described the intended bounding-box lattice transformation correctly. The concrete defect was pedagogical: connected-only demonstrations did not determine how a disconnected glyph should be treated.

**Choice:** Keep the transformation unchanged. Repair only input scheduling and semantic diagnostics so lessons teach that every color-7 cell in the bounding-box glyph participates.

**Rejected alternatives:** Change the Racket rule to process connected components separately; prohibit disconnected inputs; or always use canonical public inputs. The first would alter task semantics, the second would preserve the shortcut, and the third would collapse diversity.

**Evidence/limits:** Rule smoke and canonical parity pass. Finite rival checks do not prove that every conceivable shortcut is refuted.

## D2 — Use a four-slot, seed-rotated curriculum

**Choice:** Declare `canonical_connected`, `disconnected_a`, `general_connected`, and `disconnected_b`, with `EXAMPLES_NEEDED=3`. A complete four-pair window contains exactly two connected and two disconnected inputs. Holding out any one pair leaves at least one disconnected witness in the three demonstrations.

**Why four:** Three slots cannot guarantee a witness after arbitrary one-pair holdout without heavily biasing most demonstrations; a longer period complicates exhaustive cyclic testing without adding a needed semantic role.

**Rejected alternatives:** Independent weighted random sampling can omit witnesses; a fixed unrotated sequence correlates profile with sample index; making every input disconnected overstates a rare canonical property and introduces an easier “disconnection means special” cue.

**Probe:** All starts 0..7, all query positions, three bands, and multiple seeds are covered by `test_every_four_pair_window_refutes_largest_component_rival_under_rotation` and the required-rotation semantic battery.

## D3 — Split disconnected evidence into low- and high-fragmentation slots

**Choice:** Add `split_bar` and `split_corner`, each exactly two 4-connected components, to the low-fragmentation witness slot. Retain `public_3`, `diagonal_cross`, and `diamond` in the broader disconnected slot.

**Reason:** The first repair mixed many 4–8-component glyphs, raising generated object-count statistics far above canonical training. The two-component slot supplies the semantic distinction at a near-canonical object count; the broad slot prevents all disconnected witnesses from sharing one visual template.

**Rejected alternatives:** Use only the public disconnected example, which would produce excessive exact duplicates; use only highly fragmented glyphs, which failed distribution diagnostics; generate arbitrary random disconnected masks, which would weaken recoverable profile metadata and grammar.

## D4 — Keep the declared profile enum within the framework cap

**Choice:** Remove the redundant connected `cup` profile while adding two disconnected profiles, leaving exactly 16 total public/general profile values.

**Reason:** The framework's exact enum probe can qualify at most 16 choices. `cup` added little geometry beyond other connected profiles and had no dedicated semantic role.

**Rejected alternative:** Keep 17 values and accept an advisory/untested axis value. That would make the declared override contract larger than the verifier can exhaust and block lint.

## D5 — Rotate the schedule with a Gray-code seed offset

**Choice:** Use `(seed ^ (seed >> 1)) mod 4` as the stable schedule offset.

**Reason:** A simple linear offset made the common diagonal sampling path (`seed == sample_index`) alias profile selection and produced too many duplicate public grids. Gray-code rotation balances fixed-index and diagonal streams while preserving four-slot periodicity.

**Rejected alternatives:** Hash-based random offsets were unnecessary and harder to reason about; no rotation failed seed-only diversity; linear `seed mod 4` failed the strict-lint stream uniqueness threshold.

**Probe:** At least 70% unique inputs in each 20-draw band stream, at least five seed-only default grids across 40 seeds, all 16 profiles reachable, and full battery diversity green.

## D6 — Fail closed on call scalars

**Choice:** Require `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0` in both generation and schedule-profile entry points.

**Reason:** Python booleans are integers and the context machinery can serialize/coerce floats and strings. Accepting those values undermines reproducible schedule semantics and produced 33 strict-lint warnings in the baseline.

**Rejected alternative:** Coerce with `int(...)`. That aliases `True` with 1, truncates floats, accepts numeric strings, and maps negative indexes into valid schedule residues.

## D7 — Declare one executable rival and one direct witness

**Choice:** Add `largest_4_connected_component_only` to `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`, `disconnected_source_glyph` to `SEMANTIC_WITNESSES`, and a `lesson_identifiable` hook that reports a rival only when it fits all demonstrations and changes the query.

**Reason:** The retained counterexample is exactly described by that rival. Executable predictions make the defect reproducible and source-bound instead of relying on narrative review.

**Rejected alternatives:** Witness-frequency counts alone do not show whole-lesson identifiability; adding many speculative rivals would increase maintenance without evidence; using the rival for labels would violate authority separation.

**Limit:** One named rival plus generic census searches is not universal induction proof.

## D8 — Apply a formatting-only selected-authority synchronization

**Prior choice:** The selected JSON held a single-line `target_code`, while canonical `program_solution` used equivalent multiline formatting. The authority gate treated exact text as the selected-source contract and failed.

**New choice:** Apply the tool-generated selected-only proposal changing `/racket_target/target_code` to the canonical multiline text. Preserve archival `raw_code` byte-for-byte.

**Reason/evidence:** The proposal verified identical tokens in the supported Racket subset; live-Racket smoke and canonical outputs pass after application. Old file SHA `5dd2e464…`, new SHA `9be68294…`, patch SHA `ce40dd45…`.

**Limit:** This is an exact-source synchronization, not a claim that arbitrary reformattings are semantically equivalent.

## D9 — Keep the rule parameter isolated

**Choice:** Prototype `special_period` as an episode-level enum with canonical/default 3 and proposed 2. The period is chosen once from the episode seed; all three demonstrations and the query share it. Every retained input is constructed so periods 2 and 3 differ.

**Rejected alternatives:** Add the parameter to selected `generate`, which would mix unapproved labels into canonical production; vary several parameters simultaneously, which would make inference attribution unclear; use a setting that can be observationally identical on short canvases.

**Evidence/limits:** Live-Racket labels, Python mirror parity, canonical-default parity, redacted public challenges, and one deterministic full episode per setting pass. This is proposal evidence only.

## D10 — Preserve the frozen fixture and report the blocker

**Prior intermediate action:** The frozen root test was briefly portability-edited so the aggregate suite could run. This violated the packet's explicit fixture policy.

**Final choice:** Restore it byte-for-byte to baseline SHA `047ccc273c3fc59c92218e309b48edef119b992cd2a24498ad97a0f2aef2b514` and do not include that edit in the return.

**Reason:** The maintainer owns migration of inherited frozen fixtures. The official portable preflight correctly identifies its fixed canonical-data path. The new permitted tests remain portable and pass 13/13.

**Consequence:** `completion_state` is blocked despite a green generator battery, because the required task-test aggregate cannot pass under assignment policy.

## D11 — Audit-only targets remain unchanged

Both `6c2353a2cdee` and `0da360b839c1` accept seven invalid scalar call cases. Their target tests and semantic gates pass, so the findings are narrowly reported as call-contract defects rather than wrong-label claims. No audit target files were edited.

## D12 — Verify the return on a fresh full-packet replay

**Choice:** Build a draft return, replay its exact `source.patch` onto a fresh extraction of all 80,279 packet files, compare every declared changed-file hash, and run the 13 permitted focused tests inside that reconstructed checkout.

**Result:** Replay status is `patch_replay_passed_tests_pending`; the separate reconstructed-checkout test run passes 13/13. The final generator, selected authority, and protected frozen fixture hashes match the reported values exactly. This verifies that the repair does not depend on unbundled working-tree state.

**Limit:** The official aggregate remains blocked for the independently documented inherited fixture path; replay verification does not redefine that required-stage result.
