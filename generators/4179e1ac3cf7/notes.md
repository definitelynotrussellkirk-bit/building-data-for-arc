# Working notes: 4179e1ac3cf7

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `c2c235135ccbb3997dd9ce55f1d9d0b0524c772562104b5c5a7eae41e533778b`.

# Decisions for 4179e1ac3cf7

## D1 — Replace the baseline rather than patch individual placement branches

**Input choice.** Use a constructive six-slot layout: two rows of three isolated 3x3 boxes on every 10..14 by 12..16 canvas.

**Rationale.** The maximum request is one template, three matches, and two distractors—exactly six components. A constructive layout makes every declared override combination realizable and removes the baseline's silent object loss and retry-dependent behavior.

**Original rationale.** The baseline appears to have favored broad random placement and many nominal controls, but no retained note explains why silent under-production was acceptable; the intent is therefore inferred, not known.

**Alternatives rejected.** Increasing random placement retries would still make support seed-dependent. Declaring many incompatibilities would hide a construction problem rather than solve it. Enlarging grids would reduce canonical-profile support.

**Failure modes/limits.** The layout intentionally supports only motifs fitting 3x3 boxes. It does not teach touching or nested components.

## D2 — Keep only five exact, pixel-observable axes

**Choice.** Public axes are `grid_h` 10..14, `grid_w` 12..16, `n_matches` 1..3, `n_distractors` 0..2, and `shape_size` 3..5.

**Rationale.** Each value is consumed through `GenCtx`, observable from the returned grid, independently variable, and legal in every difficulty band. Decorative palette aliases, locked density/position controls, and malformed negative textures were removed.

**Original rationale.** The baseline exposed a larger nominal control surface, apparently to maximize variety, but no retained note explains why controls that did not reliably alter pixels were advertised; that rationale is unknown.

**Alternatives rejected.** Retaining `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, or texture aliases would advertise choices that did not change the fixed-color rule. Keeping `no_template`, `no_match`, and `mirror_oob` as ordinary textures would mix invalid examples into positive training data.

**Probe.** The final override gate tested 164 cases over three bands and accepted 14,760/14,760 draws; focused tests cover boundaries, strict types, exact observation, unknown keys, and combined maxima.

**Failure modes/limits.** Fixed colors and these five axes intentionally exclude palette-learning and invalid-example curricula; adding either later requires a separate observable contract.

## D3 — Use all connected asymmetric 3x3 polyominoes of size 3..5

**Choice.** Enumerate the finite shape bank at import time, normalize translations, require 4-connectivity, and exclude horizontally symmetric shapes.

**Rationale.** Horizontal asymmetry makes completion visibly add cells and permits a reflected template to be a distinct, high-value distractor. Exhaustive enumeration avoids a tiny hand-picked silhouette list while keeping the domain auditable.

**Original rationale.** No retained note explains the baseline motif-selection policy or why symmetric motifs were allowed even when they obscured the completion operation; the original rationale is unknown.

**Alternatives rejected.** Symmetric templates make “copy the match” indistinguishable from “copy plus mirror.” Arbitrary larger random walks complicate placement and exact domain validation. A single hand-coded shape would invite memorization.

**Probe.** Focused tests exhaust shape-bank invariants, and the final semantic/lesson probes require every generated template to be connected and horizontally asymmetric.

**Limits.** Generalization beyond 3x3, size 3..5 shapes is not established.

## D4 — Make the reflected template the first distractor

**Choice.** Whenever `n_distractors > 0`, include the template's horizontal reflection as a green component; a second distractor, when requested, is another distinct same-size shape.

**Rationale.** The reflected shape is deliberately close to a true match: same size and reflection-congruent, but not equal after translation normalization. It directly refutes the canonical-fitting shortcut `match_up_to_lr_reflection` and also tests that nonmatches are erased.

**Original rationale.** The baseline could sample distractors but did not retain a reason for their semantic distance from the template or guarantee this nearest confounder; the original curriculum rationale is unknown.

**Alternatives rejected.** Random unrelated distractors often make the distinction too easy and do not target the observed ambiguity. Changing distractor size alone allows size-based filtering.

**Probe.** The semantic gate verified the reflected-distractor witness against both reflection-equivalence and “complete every green” rivals. The final 300-lesson probe recorded a reflected-distractor demonstration in all 300 lessons.

**Failure modes/limits.** This targets left/right reflection specifically; rotations, diagonal reflections, and shape decompositions remain outside the declared competitor set.

## D5 — Add a deterministic four-sample counterexample schedule

**Choice.** With no explicit `n_distractors` override, every sample index divisible by four is a `counterexample_slot` with at least one distractor. Explicit overrides always win.

**Rationale.** `EXAMPLES_NEEDED` is four. Therefore every four consecutive demonstrations contain a reflected-shape counterexample, independent of seed and difficulty.

**Original rationale.** The baseline sampled examples independently and retained no explanation for accepting lesson-level coverage gaps; its scheduling rationale is unknown.

**Observed failure motivating the choice.** The first otherwise-correct implementation let distractor count remain fully random. A source-bound 300-lesson probe found 3/100 easy lessons where both declared reflection-insensitive competitors fit every demonstration while differing on the query (`checks/lesson-probe-intermediate-failed.json`). This was converted into a failing regression before the schedule change.

**Alternatives rejected.** Raising the demo budget would change the training contract. Merely increasing distractor probability would reduce but not eliminate holes. Forcing a distractor on every sample would weaken axis diversity and make `n_distractors=0` impossible.

**Final evidence.** `checks/lesson-probe-final.json` reports 0/300 unidentifiable lessons and 1,500 unique inputs.

**Failure modes/limits.** The guarantee assumes the current four-consecutive-demo assembly policy. A different demo count or nonconsecutive sampler must re-evaluate all cyclic starts.

## D6 — Strengthen the validator around semantic ownership

**Choice.** Validate rectangular ARC grids, exact `{0,1,3}` input palette, exactly one blue component, template size/shape/asymmetry, green component counts, exact-match counts, distractor counts, and isolated component structure. `observe_overrides` derives values only from pixels.

**Rationale.** The baseline accepted structurally invalid negatives and could not prove that requested counts were returned. Pixel-derived observation makes override claims independently checkable.

**Original rationale.** The weak validator appears to have treated several malformed textures as intentional stress cases, but no retained note defines them as a separate negative-example domain; the intended ownership boundary is unknown.

**Alternatives rejected.** Trusting generation bookkeeping would let pixels and metadata drift. Treating malformed negatives as valid “difficulty” examples would poison a positive-only rule distribution.

**Probe and limits.** Final self-check, strict-profile, override, and destructive-mutation checks pass. The validator deliberately rejects multi-template, touching-component, and out-of-palette grids rather than defining rule behavior for them.

## D7 — Add executable semantics rather than prose-only claims

**Choice.** Implement a non-mutating Python rule mirror, strict canonical predicate, witnesses, rivals, witness ownership, canonical shortcut declaration, and lesson-level identifiability.

**Rationale.** A rule can be label-correct while teaching a shortcut. Executable rivals let the gate ask whether demonstrations actually rule out plausible alternatives.

**Original rationale.** The baseline had no executable semantic contract, so there is no retained rationale for which shortcuts or lesson-level teaching obligations were considered.

**Declared competitors.** Exact-match omission (`copy_matches_without_completion`), reflection-equivalence matching, and completing every green component.

**Limits.** This list is deliberately finite; undeclared hypotheses may survive.

## D8 — Build a reusable source-bound lesson probe

**Choice.** `workspace/lesson_probe.py` stages the actual source, uses the canonical Racket bridge, dynamically reads declaration dictionaries, materializes 100 lessons per band, records replay tuples and source hashes, checks uniqueness/validation/parity, and scores every declared competitor.

**Rationale.** The 12-lesson semantic battery is a smoke test. The assignment explicitly called for at least 100 lessons per band when plausible canonical-fitting rivals exist.

**Original rationale.** No task-local large-sample lesson probe existed in the baseline, and no note explains why marginal distribution checks were considered sufficient.

**Alternatives rejected.** Copying rival names into the probe could drift from source. Using only the Python mirror would not establish authority parity. Reporting marginal witness rates alone would not prove each complete lesson contains a counterexample.

**Limits.** The final sample is 300 deterministic lessons, not exhaustive over all seeds.

## D9 — Do not change the Racket authority

**Choice.** Leave canonical and selected Racket source bytes untouched; pin the generator to existing rule hash `1cfd3e1c42af`.

**Rationale.** Canonical outputs and rule smoke showed the authority was correct. The defect was in distribution, validation, and lesson construction, not the transformation.

**Evidence.** Final authority sync passed; rule smoke had 120/120 Python-mirror parity.

## D10 — Preserve failed evidence and honest solve provenance

**Choice.** Retain RED tests, the failed first implementation test, the failed intermediate lesson probe, and both solve histories. Do not manufacture a failed solve attempt.

**Rationale.** The intermediate failure is the clearest evidence for why deterministic curriculum support was necessary. The blind solve and exposed solve answer different provenance questions and remain separate.
