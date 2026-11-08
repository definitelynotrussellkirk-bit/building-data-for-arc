# Current notes: a61246736c26

## Proposed selected-source repair

Version 5.0.0; generator SHA-256 `b32f4411f071041b98d3108b0a85fe948eabe607038faa663e47f2357fa3da14`.
Canonical Racket is unchanged; normalized rule hash `08238424436c`, exact text SHA-256 `08238424436c623860a641cc900a30929c1013105ff83faf2756f6283d97e85c`.
This note proposes a repair and records its evidence. It does not grant source, variant, or training approval or modify historical audit states.

## Intended rule and supported domain

Color-8 separator rows and columns delimit three row bands and three or four tile columns. A leading swatch strip gives frame colors as a permutation of `(5,9,0)`. Each column contains two identical framed patterns and one solid tile; the solid tile's row selects the frame swatch and its interior selects fill color. Replace pattern 1 with frame, 2 with fill, preserve 8, and concatenate the recolored tiles horizontally with 8 separators.

General generated square tiles use size 4–8 for three columns and 5–6 for four columns. Exact retained public scenes are preserved. Colors 1,2,8 have fixed roles; this is not arbitrary palette augmentation. Every solid-row assignment is supported under the structural domain, with all six row-swatch permutations. Fills come from distinct choices among 3,4,6,7. Both input dimensions must be at most 30. Valid scalar identities are Python integer seeds (excluding bool) and nonnegative Python integer sample indices.

## Findings, reversals, and current decisions

- **G1: joint support.** The pinned original v4.0.0 rejected 99/648 independently constructed lawful row/swatch combinations. Its generated same-row examples selected only frame 0. General classification now admits all row signatures; `recombined_rows` covers unnamed signatures, and swatch permutations vary independently. The default bounded probe observes both column counts, all six permutations, and same-row selected frames 0,5,9. See returned `checks/regressions/red_receipt.json` and `checks/coverage/canonical-census-candidate-final.json`.
- **G2: malformed geometry.** A separator-cell mutation of original seed 3/index 0/easy/permuted_frames raised `IndexError`; prior fail-closed language is reversed. Output calculation now occurs only after structural validation succeeds. The exact input is in `counterexamples/current-review/malformed-separator.json`. Oversized width/height also reject before semantic execution; size-7 and size-8 four-column regression cases cover the discovered boundary.
- **G3: conditional teaching shortcut.** An initial three-demo, period-two repair crossed same-row solids with nonstandard swatches but did not separately teach mixed-row lookup. A rival using actual swatches on same-row scenes and fixed swatches otherwise fit seed-3/easy demonstrations 0–2 and missed query 3 by 80 cells. Actual Racket labels are retained in the returned `checks/teaching/before-conditional.json`, with a compact task-local witness and replay CLI.
- **G3 decision.** The final default period is three: same-row counterfactual, mixed-row counterfactual, varied. `EXAMPLES_NEEDED=5` means five ordered demonstrations plus one query. Six consecutive nominal draws give two of each necessary witness; accepted-index production assembly and every query-role rotation are checked separately by the census. Three rivals are declared explicitly. This finite contract does not claim unique induction against arbitrary rules.
- **G4: argument and override integrity.** Thirty-three invalid scalar probes accepted by the baseline now reject. A strict intermediate battery caught 17 exact controls exceeding its cap of 16, and missing keyed profile provenance on scheduled draws. The redundant `same_row_middle` name was removed; that input family remains in `recombined_rows`. All paths record profile choices through the public context. Exact overrides bypass the default teaching schedule deliberately.
- **G5: portability.** The allowed inherited task test now resolves its own repository/staged root with `reviewer_support`; the frozen root fixture was not edited. Two portable authoring tools use the same local rule parser through a task-local namespace binding when the repository lacks `scripts`, without changing shared runtime.

The retained audit leads `review-66a96f3e3fde9097:v0001` (needs_triage) and `review-e3fe90a3dfb3e6d7:v0001` (unresolved) motivated reproductions against the pinned baseline. The new evidence proposes resolving the selected source's support/validation issues. Their explicit index statuses remain unchanged for maintainer disposition; unrelated findings are not silently closed.

## Evidence and reusable tools

The final standard after battery passes all 12 stages with required query-role rotations and a verified fixed-seed schedule receipt. The required isolated task-test run passes 66 tests (49 new focused regressions, 10 inherited task tests, 7 prototype tests). Earlier failed environment/staging invocations remain separately recorded. The independent coverage probe executes canonical Racket for 648 fixed-pattern recombinations, 600 balanced default draws and 3 canonical controls; all 1,251 comparisons pass on the final generator bytes.

`workspace/coverage_probe.py` is the reusable joint-axis/reference probe; `workspace/replay_retained_lesson.py` replays the old ambiguous lesson from retained inputs instead of depending on a superseded seed stream. The current return's `REVIEW.md` and `RESULTS.json` give exact final lesson-census, solve and fresh-patch replay outcomes and source-bound commands. Do not infer wider coverage from an intermediate hash or from individual label correctness.

## Parametric assessment

Status: prototype/proposed, separate from canonical repair. `workspace/parametric/prototype.py` exposes `frame_row_offset` 0,1,2, selected once per episode. Offset 0 preserves exact canonical program bytes; variants change only the row used to look up frame color. Public challenges omit the parameter, rule, seed and query outputs. Generate/check replay all three settings through actual Racket and test distinction against the other offsets, including query-role rotations. Its explicit-profile three-demo/one-query episodes have their own bounded policy and do not replace the repaired five-demo production schedule.

## Limits

No approval metadata, shared source, canonical authority, audit target, or historical evidence is patched. Production claims apply to five demonstrations and the reported sampler; fixed three-demo consumers need an explicit policy change. Complete recombination coverage is for the stated 4×4 fixture family, not every lawful grid. Seeded default and lesson checks are finite. The post-repair solve is exposed, and masked-query correctness is not available to this reviewer. The final brief distinguishes observed results, proposed variants, and remaining maintainer decisions.

## Current overlapping proposal

Overlapping old-baseline alternative retained without replacing accepted v5 b32f4411. Both start from33e5c3a1 and repair the same shortcut/validator/scalar findings, but collide on generator, tests, notes and prototype. Current v5 broadens structural validation to648 lawful recombinations and has66 reported tests; alternative v4.1 f6be3b03 has43 reported tests,576 explicit-profile cases and a six-position schedule. Neither evidence set qualifies combined bytes. Retain its distinct stroke_symbol2/8 prototype, six episodes/54 Racket applications and24 holdouts as a source-bound proposal requiring rebase onto selected v5; do not count it as a current prototype or production repair. Canonical Racket unchanged; no variant or training admission. Retained at `workspace/proposals/review-0a75bb185b4fe284/manifest.json`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e3fe90a3dfb3e6d7:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `33e5c3a10739251440d40b658e523234ff2ef3fe823b9fbe76f74a1717a41767`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicitly resolve same-row nonzero-frame support gap, asymmetric standard-swatch rejection and malformed separator IndexError on selected v5 b32f4411: structural648 recombinations, geometry-first rejection, crossed same/mixed-row five-demo schedule and3unique rivals. Reviewer66 tests portable/fresh,12/12 battery,1251 Racket calls,300lessons/1800rotations; finite bounds, canonical rule unchanged. Unselected f6be alternative does not qualify current/combined bytes.

### Assessment or prior finding

## a61246736c26

**Confirmed teaching-support gap plus validator exception; audited source left unchanged.** Source SHA-256: `33e5c3a10739251440d40b658e523234ff2ef3fe823b9fbe76f74a1717a41767`; canonical rule hash `08238424436c`.

### Same-row nonzero-frame gap

Starting from seed `3`, sample index `0`, difficulty `easy`, profile `permuted_frames`, I swapped each column's solid swatch tile into row band 0 while moving the displaced pattern copy back to the old solid row. The resulting 16×16 lattice still has one solid and two identical pattern copies per column, row swatches `(9,0,5)`, and solid rows `(0,0,0)`. `self_check` returns `[]` and `observe_overrides` reports `permuted_frames`.

Canonical Racket selects frame 9 and returns a 4×14 output. A plausible rival—perform the intended recoloring but force frame 0 whenever all solids occupy one row—differs in 36 cells. The actual Racket output matches the independent Python mirror and does not match the rival. Yet across 396 explicit generated profile draws (all 11 general profiles, 12 seeds, and all three bands), all 36 generated same-row cases used frame 0. Thus the rival fits the sampled supported same-row distribution while a validator-accepted in-domain counterexample refutes it.

### Validator exception

On the same generated base, changing input cell `(5,0)` from 8 to 9 removes one full separator row. Instead of returning structural errors, `self_check` raises `IndexError: list index out of range`. The malformed grid is outside the supported rule domain, and canonical Racket also exits with an indexing error; the actionable defect is that the validator does not fail closed with an error list after it has already detected malformed geometry.

Evidence:

- `checks/audit/a61246736c26/probe.py`
- `checks/audit/a61246736c26/evidence.json`
- `checks/audit/a61246736c26/input.json`
- `checks/audit/a61246736c26/racket.json`
- `checks/audit/a61246736c26/malformed.json`
- `checks/audit/a61246736c26/malformed-racket.json`

Commands from the packet root:

```sh
python3 review.py run python3 ../checks/audit/a61246736c26/probe.py
python3 review.py run python3 -m arcpuzzles apply a61246736c26 --input ../checks/audit/a61246736c26/input.json --out ../checks/audit/a61246736c26/racket.json
python3 review.py run python3 -m arcpuzzles apply a61246736c26 --input ../checks/audit/a61246736c26/malformed.json --out ../checks/audit/a61246736c26/malformed-racket.json
```

The first two commands exit 0; the malformed Racket command intentionally exits 1. These reproduce still-open findings attached to the same source hash. No source was edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e3fe90a3dfb3e6d7-v0001/audit_assets.json), manifest SHA-256 `6139bc766f9d836cd51b45909935a144c53b57687c9daf9fc6ebf9dbaafe7020`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `b32f4411f071041b98d3108b0a85fe948eabe607038faa663e47f2357fa3da14`.

# Decisions — a61246736c26 / review-db01808940396009

## D1 — Preserve the canonical transformation

The canonical rule selects the duplicated pattern in each tile column, uses that column's solid tile to select a fill and row, looks up the row's leading frame swatch, and emits the recolored patterns horizontally. The literal lattice separator stays color 8. The selected canonical Racket text and normalized `RULE_HASH=08238424436c` remain unchanged. Actual Racket, not the Python mirror or independently written fixture, supplies authoritative labels.

The original family is `training:15660dd6`. The original source is v4.0.0, SHA `33e5c3a10739251440d40b658e523234ff2ef3fe823b9fbe76f74a1717a41767`. This return proposes v5.0.0. Its intended behavior is a broader lawful input domain and a teachable production lesson, with the original reasoning roles preserved.

## D2 — Recombine row signatures and swatch permutations

The original sampler used a finite set of row signatures; its only generated same-row configuration selected frame 0. The validator also rejected standard-swatch combinations it accepted after permuting the swatches. The baseline regression run reproduced **99 rejected cases among 648 lawful independent fixtures**, plus the missing same-row nonzero support. Historical findings `review-66a96f3e3fde9097:v0001` and `review-e3fe90a3dfb3e6d7:v0001` supplied leads; the current-source failures were reproduced instead of accepting the older claims as measurements.

The repair accepts every combination of six swatch permutations and 27 three-column or 81 four-column solid-row assignments within the existing tile constraints. It generates arbitrary row signatures under `recombined_rows` and permuted swatches under `permuted_frames`. Known profiles remain observable controls. All-top is available explicitly; all-middle remains available through `recombined_rows`. Sixteen exact controls stay within the frozen override tool's finite-enum qualification cap. Removing the redundant `same_row_middle` label after an actual lint failure did not remove that input family.

The independent fixture exhausts these 648 combinations for a fixed 4×4 pattern family. It is not exhaustive over sizes, textures, or every lawful grid. The 600 default calls use 200 seeds in all three bands, at index `seed * 29`; cycling bands with that index would have aliased difficulty to a period-three phase, so that sampling design was corrected explicitly. `workspace/coverage_probe.py` executes the canonical rule and retains source-bound counts, input/output batch hashes and compact witnesses.

## D3 — Five demonstrations and separate crossed witnesses

The first repair scheduled same-row, nonzero, permuted-swatch examples every other draw and declared three demonstrations. Independent review produced a conditional rival that still fit all demonstrations: use actual swatches for same-row scenes, otherwise use fixed row colors. The exact seed-3/easy lesson and its 80-cell query disagreement are preserved in `checks/teaching/before-conditional.json`. A new six-draw regression failed on 30 of 36 windows before the repair.

The final schedule has period three: same-row counterfactual, mixed-row counterfactual, varied scene. `EXAMPLES_NEEDED=5`. The same-row phase selects a nonzero frame that differs from the standard frame at that row; the mixed-row phase selects at least two solid rows and an actually used nonstandard swatch. The varied phase retains exact public profiles, ordinary row signatures, shared-pattern scenes, and other lawful combinations. Scheduled profile selection goes through the public keyed-draw context so exact-control provenance remains truthful.

The intended production assembly is **five ordered demonstrations followed by one query** from the production sampler. We also require every leave-one-pair-as-query role rotation of each materialized six-pair lesson to remain distinguishable against the three declared rivals, keeping the remaining pair order. This does not rotate grid geometry. Two witnesses of each type occur in every six nominal consecutive indices; this structural fact does not substitute for testing accepted indices after duplicate/rejection handling. The fixed-seed enumeration and 100-lessons-per-band census retain the actual assembly.

Rejected alternatives: leaving three demonstrations gives no guaranteed duplicate coverage of both witness types across all query positions; suppressing mixed-row queries would conceal the rule distinction; forcing only counterfactual scenes would unnecessarily narrow the varied distribution. Five demonstrations increases lesson length. Downstream consumers that hard-code three examples must adopt the declared count or use their own explicit resampling/identifiability policy; this return does not certify three-example production.

## D4 — Fail closed on malformed geometry and strict identity types

The original `_analysis` continued into `rule_mirror` after detecting malformed geometry. A one-cell separator mutation of seed 3/index 0/easy/permuted_frames raised `IndexError` instead of returning validation errors. Earlier fail-closed language is superseded by this reproduction. The repaired validator computes an output only after structural checks succeed.

Both dimensions are now checked against the 30-cell ARC bound. A separately discovered four-column, size-7 fixture demonstrated the missing boundary; size-7 and size-8 oversized regressions remain in the task tests. Four-column generated tiles stay at size 5 or 6; three-column tiles use the existing band-specific 4–8 ranges. These are sampler limits, not a claim that every reference-executable grid is admissible ARC data.

Seed must be a Python integer excluding bool. Sample index must also be a nonnegative Python integer. Thirty-three invalid scalar calls accepted by the original source now raise `ValueError`. Negative integer seeds remain supported: the restriction is on type and on nonnegative sample indices, not an invented nonnegative-seed contract.

## D5 — Portable task tests and immutable authority

The inherited task-local test guessed the root using fixed path depth. The standard staged preflight reproduced its canonical-data lookup failure. Its allowed task-local file now uses `find_root`, `canonical_path`, and `load_selected_generator`. Frozen root fixtures, canonical data, shared runtime, audit sources, assignment contracts and historical evidence are not patched.

Some early checks failed because the environment lacked pytest, exhausted temporary storage, or omitted the Racket wrapper. These remain infrastructure/invocation failures in the evidence history and are not counted as generator test failures. Final aggregate claims use the completed standard task-test receipt and fresh replay run only.

## D6 — Proposed parametric extension

Status: **prototype/proposed**, independently of canonical repair acceptance.

The single parameter `frame_row_offset ∈ {0,1,2}` changes the frame lookup to `(solid_row + offset) mod 3`. Offset 0 preserves the exact canonical program bytes. Other settings substitute one guarded expression, preserving pattern selection, solid fill, separators, and horizontal composition. The parameter is selected once per episode. Public challenges omit the setting, programs, provenance and query labels.

The prototype uses explicit profiles, three demonstrations plus one query, and actual Racket execution for all three settings. Its own lesson policy is distinct from the repaired canonical production sampler's five demonstrations. The checker replays materialized programs, seeds, hashes, public/private separation and all parameter rivals; it also checks each query-role rotation. The evidence covers seed 1701 and four specified medium profiles. It does not approve variants, certify production admission, or establish uniqueness beyond the three offsets. See `workspace/parametric/README.md` and the current `checks/parametric/` receipts.

A second parameter was not added: the row-offset family is a small semantic extension with clear demonstrations, while adding an unrelated transform would expand the induction burden without evidence that the extra family is needed.

## D7 — Scope of audit and acceptance

The two randomly drawn peer targets are findings-only. Their counterexamples and bounded clean checks are in `AUDIT.md`; their sources remain unchanged. Maintainer audit states and training approval are not edited. Existing open findings for the selected task receive proposed evidence-based resolutions in current notes, not forged status updates.

All measured results are finite and source-bound. Passing a declared-rival census does not exclude undeclared rules. The exposed post-repair solve is not a blind solve, and masked-query correctness remains unknown. The return contains the actual patch and all decisive failures; final replay is checked against that patch in an independent checkout.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a61246736c26/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
