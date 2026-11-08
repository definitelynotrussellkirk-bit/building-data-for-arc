# Working notes — a7d4df2828a0

## Review handoff: review-a0fe7111a89db996

Baseline 2.0.1 placed only the input bounding box: quarter-turn output could clip. Original easy seed=67/sample_index=67 produces four motif cells but Racket retains two. A real-Racket census of seeds 0–999 in each band found 58/3,000 clipped motifs (18 easy, 19 medium, 21 hard). The canonical rule executed as written; the generator's lossless teaching domain was the defect.

Version 2.1.0 reserves both footprints, enumerates finite generic connected shapes, and checks symmetry only under the selected operation. This restores canonical train[1]'s T motif, which the prior all-transform asymmetry filter excluded. Stronger self_check rejects malformed or semantically inconsistent inputs. Advertised axes are honored across difficulties; rule pin, branch coverage, and strict override hooks were added. Half of defaults in each band use compact dimensions/four cells to preserve canonical-scale support without copying fixtures.

Observed evidence: all 12 inherited battery stages green; 41 focused tests pass; 3,072 axis combinations pass; inherited override probe accepts all 21,150 draws; actual Racket conservation 0/3,000 failures; all three stored canonical labels match. These are bounded tests, not downstream model evaluation. Generator SHA256 and Racket/source receipts are in the return's checks directory and REVIEW.md. The Racket rule, canonical examples, shared tooling, and two audit-target sources were not modified.

## Next agent

Run `python3 -m pytest -q repo/generators/a7d4df2828a0/tests` from the packet root, plus the workspace conservation probe. The inherited battery does not automatically discover these new task-local tests. Preserve generator version/source hashes with new evidence. Do not weaken footprint validation or revert to all-transform asymmetry just to simplify shape sampling.

The next meaningful gap is demonstration-episode identification, not more count-only witnesses. Enumerate the 24 assignments of four operation meanings to control codes, filter them against demonstrations, and check whether the test output is unique. Four random demonstrations need not cover all four controls; transforms may agree on some shapes. Keep this distinction from current branch coverage explicit. Family-disjoint shape holdouts and a measured training ablation remain future work.

Imported associated notes retain their original evidence/timestamps in evidence/associated_notes.jsonl; that ledger was empty for this task. No historical design rationale beyond visible source/examples is asserted.
## Current reviewer considerations

Source SHA-256: `2a710e880d69b1c86cdc64eea19c274c9dd7a26dbcf4bcc06f461c04c8ffca9c`.

# Decisions and limitations — a7d4df2828a0

The source, three canonical pairs, empty imported associated-notes ledger, and inherited checks were inspected. No historical rationale is invented below: “inferred” means an interpretation of visible code/examples, not an author statement. All changes stay inside the assigned generator's allowed files. The Racket rule and approval/evidence authorities are unchanged.

## D1 — Keep background 0 and the control at (0,0)

Original choice: fixed zero background, control values 1–4 at the origin. Rationale: directly specified by the rule and illustrated by canonical inputs. Alternative: palette-permute the control/background or move the control; rejected because these change the task without a corresponding justified authority change. Retain control meanings and sample motif color from 1–9 excluding the selected control. Test the input control separately from the motif. A transformed motif may repaint the old control location; output validation must not erase that cell from its count.

## D2 — Preserve one small connected motif and its separation

Original choice: one random-growth motif, 3–6 cells depending on difficulty, one color, at least two rows and columns, separated from control. Inferred rationale: isolate the local transformation from component-selection ambiguity. Alternatives: disconnected motifs, multiple colors, straight shapes, large objects, or adjacent control. These broaden the teaching grammar and make shortcut/branch interpretation harder; not needed to fix the observed defect. Retain the 3–6-cell, 4-connected, single-color, two-dimensional domain. Make the existing separation explicit as no motif cell in the top-left 2×2 area. The three canonical inputs remain accepted. Limitation: self_check validates this selected teaching domain, not every input the Racket program could execute.

## D3 — Reject only selected-transform invariance

Original code demanded asymmetry under all four operations. Inferred rationale: avoid identity-output training cases. That rationale does not justify rejecting unrelated symmetry: canonical train[1]'s T is mirror-symmetric but changes under its code-1 rotation. Alternative: permit all no-ops; rejected for now because an unchanged motif is a weaker per-example witness. New choice: compare the normalized coordinates only under the selected operation. The controlled T-support test fails on the baseline and passes on the candidate. Limitation: two different nonidentity transforms may still yield the same result on a shape. This is not a proof that one pair or one episode uniquely determines the operation.

## D4 — Enumerate a finite generic shape domain instead of retrying random growth

Original choice: bounded random growth and retries. Historical reason is unknown; simplicity is a plausible implementation motive. Alternatives: retain growth with more rejection, hard-code canonical motifs, or recursively enumerate connected shapes. Choose recursive addition of one adjacent cell with translation normalization and deduplication, capped at six cells. This supports every oriented connected shape in the chosen size range before explicit admissibility filtering, includes canonical families, avoids seed-dependent retry starvation, and does not embed canonical fixtures. Sorted tuples and bounded caches stabilize draws. The new distribution is uniform over admissible oriented shapes, not the old growth-process distribution, nor uniform over rotation/reflection equivalence classes. Version 2.1.0 deliberately changes old seed mappings. No learning advantage from this reweighting is measured.

## D5 — Reserve both footprints, then choose an anchor

Original choice: place the input bbox within the canvas. Inferred rationale: keep emitted input legal; this missed quarter-turn extent changes. Alternative: enlarge the output, move the output anchor, modify Racket clipping behavior, or reject samples after labeling. All are inferior here: they change authority/semantics or waste draws. New choice: reserve max(input height, output height) by max(input width, output width), with code 1 swapping dimensions. Enumerate legal anchors respecting input control separation, then choose one. This allows all canvas edges without truncation. The legacy seed-67 input is rejected; matched 3,000-input Racket probes go from 58 conservation failures to zero.

Feasibility argument: a connected n-cell motif spanning at least two rows and columns has each span at most n−1. For n≤6, both spans are at most five. A 7×7 canvas always accommodates either transform at anchor (2,2) with the required control gap. Thus every declared axis combination has a legal anchor; no structured incompatibility exemption is needed. This is an argument for placement feasibility, not full program correctness.

## D6 — Keep difficulty variation while retaining compact support in every band

Original defaults: easy dimensions 7–9 and 3–4 cells, medium 9–11 and 3–5, hard 11–14 and 4–6. Historical tuning rationale is unknown; the likely intent is more space/complexity at higher difficulty. Canonical-profile checking showed zero hard-band support in 20 draws. Alternatives: collapse every band to canonical dimensions, leave the gap, inject literal fixtures, or mix a compact stratum with the old bands. Choose the mixture: 50% probability of independently sampled 7–9 dimensions and exactly four cells, otherwise the old band ranges. This preserves generative diversity rather than copying fixtures. Exact profile support rises from 5/60 to 17/60; envelope support rises from 10/60 to 29/60. These metrics justify support repair, not an optimized 50% weight or a strict easy-to-hard curriculum. No sampled output is used to set an input.

## D7 — Make declared axes truthful

Original AXES advertised global ranges, but draw bounds narrowed them by difficulty and unknown override keys could disappear. New choice: validate keys/types, use the declared global bounds for explicitly pinned axes, preserve difficulty bounds only for defaults, and expose realized values via observe_overrides. Keep no infeasible combinations and use strict rejection accounting. The exhaustive 3,072-combination unit test and inherited 21,150-draw override contract both pass. Alternative: narrow advertised ranges per band; rejected because it breaks the existing global contract and is not necessary. Unrecognized difficulty labels retain the prior medium-style fallback; no new global difficulty API is introduced.

## D8 — Strengthen self-check without manufacturing labels

The old checker accepted malformed semantics and degenerate impostors. New input-only checks cover grid shape, colors, connectivity, population, code separation, selected-operation visibility, and output bounds. Geometry uses coordinate transforms only for admissibility; generate still returns an input grid alone. All training labels remain the Racket authority's responsibility. Add strict_canonical_like and four branch witnesses to make the teaching domain inspectable. MIN_STRICT_FRAC=1 follows constructive admission rather than selectively accepting a measured subset. Coverage witnesses intentionally do not claim rival elimination.

## D9 — Keep authoritative outputs unchanged; pin and test them

No canonical correction was warranted: all three stored outputs agree with real Racket before and after. Silent clipping is prevented at the input distribution, not “fixed” by altering correct authoritative execution. Add RULE_HASH=089b88c1e5ad to bind the generator. Retain archival text and its existing provenance even where it differs textually from selected authority. The authority-sync stage passes without source changes. A rule pin is not an approval token.

## D10 — Add a narrowly scoped conservation probe

The existing rule-smoke stage proves execution, not preservation of task-specific semantic quantities. The new workspace tool labels with actual Racket and compares nonzero color Counters, excluding only the input control, plus canvas shape. It also performs a cheap independent geometry check, canonical exact-output checks, and records source/rule/runtime hashes. False-positive risk: applying this to intentional cropping, selection, duplication, or recoloring tasks. Therefore it is explicitly opt-in and task-specific. False-negative risk: a wrong transform preserving counts; canonical exact checks do not eliminate all such errors. Metadata/evidence remain reviewer-side, not model-visible training features. The v1 report's failed_cases field counts failed validation events; use racket_pair_failures for unique labeled-input failures. Unexpected runtime setup errors are nonzero process failures, not passes.

## D11 — Keep audit targets read-only and preserve bad runs

The two assigned audits are independent task investigations, not independent human/code reviews of this candidate. Findings and real Racket counterexamples are returned without changing their source. The first audit script needed canonical test-dict normalization; preserve its failed log and the successful corrected run. Preserve baseline failing tests and gate logs. No clean-looking report replaces contrary evidence.

## Unresolved work, deliberately not represented as complete

Episode-level identification, family-disjoint train/test construction, no-op teaching policy, relative frequencies of shape families, trace quality, and model-training value remain unmeasured. Shared pair-contract hooks and automatic discovery of task-local tests need separate library changes. The finite sample count does not prove absence of all defects. No external reviewer/subagent was available; source and diff review were performed locally, followed by actual execution checks.

## Native parametric handoff — review-1e27b399ba9aad55 (2026-10-25)

Added the task-local `placement={bbox_top_left,preserve_first_cell}` family. The
default program is the exact selected canonical source. The alternative applies
the same control-coded transform but preserves the row-major first motif cell's
absolute position, forcing a transform → transformed-pivot → translation chain.
Inputs are matched across settings; requests support 2–6 demos and 1–4 queries
with stable prefixes and four distinct controller-side queries. The 30×30 audit
case has 98 motif cells and the settings disagree on 170 output cells.

Fresh evidence: 52/52 staged task tests; 42 protected-Racket self-audit
executions; four qualification jobs at seeds 0 and 17 with 32 protected labels;
16/16 sequential public projections; one causal replay with an 8-cell
counterfactual disagreement. The final deterministic sweep covered 67 seeds
through `2^63-1`, 268 episodes and 2,680 typed grids for this target with no
retained rival, prefix, privacy, stress, or source-binding failure. Exact paths:
`workspace/parametric/evidence/manifest.json`,
`checks/a7d4df2828a0/qualification/qualification.json`, and
`checks/a7d4df2828a0/causal/witness.json`.

Limit: finite declared rivals and seeds do not prove universal identifiability.
Owner exact-source acceptance and training admission remain pending.
