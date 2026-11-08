# Working notes: c286f4a2923f

## 2026-10-25 native parametric admission build

- Preserved the exact canonical `transfer_only` Racket program and added the nearby episode-fixed `fill_transferred_holes` setting.
- Sequential rule: transfer the source topology to the target, then consume that intermediate by filling all enclosed zero regions. The protected skip-A witness changes the final label.
- Inputs are matched across settings and prefix-stable for 3..6 demonstrations and 1..4 queries. The fourth query is a substantive 30×30 multi-pocket lattice.
- The first lesson uses an asymmetric right-side source, defeating the plausible mirror-toward-target shortcut. A reusable `workspace/parametric/audit.py` checks six finite rivals on seeds 0, 17, and 97.
- Native qualification: 4 jobs / 40 protected-Racket evaluations passed. Public projection: 16 views; combined first-turn audit across both assigned families passed 32 views and 48 private-field invariance checks.
- Status is reviewer-ready only. Owner acceptance and training admission remain external.

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-09-28 review (`review-2e3af094b3276d32`)

- Baseline battery: 10 green, 2 advisory. The profile gate measured only 6/60 canonical-envelope draws, with zero medium/hard support; the semantic gate reported `NO_CONTRACT`.
- Added a Python authority mirror, six executable rival rules, five witness families, and a three-example lesson-identifiability hook. The strongest canonical ambiguity is top-left versus centered placement inside a larger target.
- Reordered the six-shape schedule so every right-side example is horizontally asymmetric, making every three-example window reject a “mirror toward target” interpretation.
- Interleaved the three canonical grid profiles every third sample across all bands. Broad 8..16 by 13..20 canvases remain on the other samples.
- After battery: 12/12 green. Profile support rose to 33/60 envelope hits (easy 13, medium 7, hard 13); semantic strictness was 600/600, all rival claims held, and all 12 sampled lessons were identifiable.
- The canonical Racket rule was not edited. Selected authority sources remain exact and execution parity passed; the archival raw source remains text-divergent but behaviorally equivalent.
## Current reviewer considerations

Source SHA-256: `40ed04e4f0ac7ab44f9fd54264db7dd38bb6cc61ecb0d83701bd26a5f7aad9ae`.

# Decisions for `c286f4a2923f`

## Design brief used

Preserve the existing mask-transfer grammar and exact override contract, repair the measured canonical-profile gap, and convert shortcut claims into executable semantic evidence. Do not change the Racket authority unless parity or canonical correctness demands it.

## D1. Keep the existing object grammar and palette

**Choice.** Retain one connected color-2 nonrectangular source, one solid color-3 target rectangle, background 0, color-8 output, horizontal separation, and the existing six exact source shapes.

**Original rationale.** Prior task evidence says the old palette/density/texture controls were replaced with six directly observable axes. The baseline structural and override gates were already green, and all three canonical inputs passed `self_check`.

**Alternatives considered.** Generate arbitrary connected masks; add rotations/reflections as axes; introduce multiple source or target objects; vary semantic colors.

**Probe.** Baseline lint, selfcheck, override, grammar, diversity, and Racket smoke were green. No structural defect justified widening the grammar during a shortcut/profile repair.

**Failure modes and limitations.** Fixed masks cover only a small silhouette family. Arbitrary masks would add breadth but would need new uniqueness checks, override representation, and safeguards against accidental rectangles/symmetries. I left that expansion out rather than weaken a working grammar.

## D2. Interleave exact canonical grid profiles every third sample

**Choice.** At `sample_index % 3 == 0`, use `(8,13)`, `(9,13)`, or `(9,14)`, cycling through all three. Otherwise preserve the 8..16 by 13..20 draws. Explicit `grid_h` and `grid_w` overrides still take precedence.

**Original rationale.** The associated note explicitly says broad canvases were intentional but asks an independent reviewer to revisit the 10% envelope rate. The baseline measurement confirmed 6/60 pooled support and zero medium/hard support.

**Alternatives considered.** Narrow every sample to the canonical envelope; use an unpinned random weight; add a new `canvas_profile` axis; anchor only easy samples.

**Why this option.** It raises exact/envelope support above the strict floor in every band while retaining broad positional/scale variation for two thirds of the stream. A deterministic schedule is testable and cannot accidentally miss a band in a small lesson.

**Probe.** Strict profile gate changed from WARN to PASS: exact 6/60 to 31/60, envelope 6/60 to 33/60, and medium/hard from zero support to 7/20 and 13/20.

**Failure modes and limitations.** Sampling only one residue class can bias dimensions. The schedule couples size to `sample_index`, although no semantic output depends on canvas size. A future scheduler could expose an explicit profile axis if consumers need independent balancing.

## D3. Reorder shapes so right-side lessons are orientation-decisive

**Choice.** Change the shape schedule from `L,T,ring,C,cross,zigzag` to `T,L,ring,C,cross,zigzag` while retaining alternating left/right placement.

**Original rationale.** Existing notes claimed both-side placement ruled out fixed-side shortcuts. That was true, but it did not fully rule out a more plausible rule: reflect the source so it faces the target. In the old order, a right-side `T` is horizontally symmetric and provides no orientation evidence.

**Alternatives considered.** Randomize side independently; add a source-reflection axis; increase `EXAMPLES_NEEDED`; replace the symmetric masks.

**Why this option.** Every odd residue (the right-side residues) is now horizontally asymmetric: `L`, `C`, or `zigzag`. Every three-consecutive-example window contains a right-side asymmetric witness while the first two examples still form the equal-count/different-shape pair.

**Probe.** Exhaustive tests checked all starts 0–17 in all three bands, and the semantic gate observed the right/asymmetric witness 287/600 times with 60/60 sampled rival disagreements.

**Failure modes and limitations.** The guarantee depends on the side and shape schedules remaining synchronized. The regression test makes that coupling explicit.

## D4. Treat placement ambiguity as the strongest canonical shortcut

**Choice.** Declare centered placement, bottom-right placement, and mirror-toward-target as `CANONICAL_SHORTCUTS` and verify they fit every canonical pair.

**Original rationale.** In all three public pairs, the target rectangle has the same dimensions as the source bounding box, so top-left, center, and bottom-right alignment collapse to the same output. The public source is also always left of the target, so a conditional mirror-on-right rule is untested.

**Alternatives considered.** Discuss these ambiguities only in prose; test only count/bbox/recolor shortcuts; declare a large automatically enumerated DSL of rivals.

**Why this option.** Executable rivals make the claim falsifiable and are consumed by the repository semantic gate. The list stays small enough to inspect.

**Probe.** Canonical tests confirm all three rivals fit all three pairs. A generated 8x13 ring with a 5x5 target makes centered placement disagree with the authority. The exact input and both outputs are in `checks/after/c286f4a2923f_after_center_shortcut_counterexample.json`.

**Failure modes and limitations.** Other programs can fit three examples. The contract establishes coverage against named, plausible rivals rather than a theorem over all programs.

## D5. Add a strict semantic contract rather than more comments

**Choice.** Add `strict_canonical_like`, `rule_mirror`, `SEMANTIC_RIVALS`, `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, and `lesson_identifiable`; declare `MIN_STRICT_FRAC = 1.0`.

**Original rationale.** The baseline docstring and notes asserted shortcut resistance, but the semantic gate reported `NO_CONTRACT`. A prose assertion was therefore not source-bound evidence.

**Alternatives considered.** Add tests without hooks; lower the strict fraction; define witnesses without rival functions; rely only on Racket smoke.

**Why this option.** The gate can now independently sample inputs, evaluate witnesses, check rival disagreement, check canonical ambiguity, and validate complete lessons. Because `generate` always returns a scene accepted by `_analyze`, 1.0 is the honest strictness floor.

**Probe.** After gate: 600/600 strict hits, all five witnesses firing in every band, all rival claims verified, all 12 requested lessons identifiable, and all three canonical inputs accepted.

**Failure modes and limitations.** `rule_mirror` and rivals call the same analyzer, so analyzer bugs could affect all of them. Canonical tests, mutation fixtures, independent Racket parity, and the structural battery provide separate checks.

## D6. Keep the Racket rule unchanged

**Choice.** Do not patch canonical `program_solution`, selected base `target_code`, or archival `raw_code`.

**Original rationale.** The selected canonical and base authorities were already exact; the archival source was text-divergent but execution-equivalent. Baseline and after Racket smoke both solved all sampled scenes.

**Alternatives considered.** Rewrite the archival implementation to match the selected text; replace the selected rule with the new Python mirror translated to Racket.

**Probe.** Authority sync and execution parity are green. The after smoke applied the real Racket rule 120 times with no crash, mutation, out-of-bounds output, or mirror mismatch.

**Failure modes and limitations.** Archival text divergence remains and is explicitly reported. Changing it in a generator-local review would add source-sync risk without changing behavior.

## D7. Use test-first changes and preserve replayable evidence

**Choice.** Write five focused tests before implementation, snapshot the frozen baseline runtime, observe the expected failures, implement the minimum generator changes, then run the task tests and all twelve gates.

**Alternatives considered.** Implement first and add tests afterward; rely on the generic battery alone.

**Probe.** Frozen baseline: 7 pass / 5 fail. Repaired runtime: 12 pass. Logs are under `checks/tdd/`.

**Failure modes and limitations.** The focused tests do not replace repository gates. Conversely, the generic gates do not exhaust every consecutive lesson window, which is why both layers are retained.
