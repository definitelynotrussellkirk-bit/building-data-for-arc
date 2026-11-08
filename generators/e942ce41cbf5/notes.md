# Working notes: e942ce41cbf5

## Review diagnosis — 2026-10-02

The imported v2.1.0 generator reproduced the broad rule but not a dependable teaching distribution.

- It had no `RULE_HASH` pin.
- Public axes included dead palette/texture controls and negative fixtures in the ordinary texture domain.
- It did not expose `observe_overrides`; dimensional overrides frequently failed to realize exactly.
- Unknown override keys were accepted.
- Its default scale was usually far outside the canonical profiles: only 2/60 profile-floor draws were exact, all in `easy`; `medium` and `hard` had zero support.
- `self_check` accepted all 15 `absent_color_cell` mutations, including missing-transform cases.
- It declared no strict-canonical, witness, rival, schedule, or lesson-identifiability contract.
- The active base-bank `target_code` differed textually from the canonical Racket authority, although sampled execution agreed.

## Selected redesign

Version 3.0.0 narrows the public contract to four real dimensions and makes the lesson schedule explicit. Every three-example window covers operation controls `3/4/6` and transform controls `7/8/9`. Seed phase rotates the transform cycle so the pooled schedule covers all nine pairings.

Masks are sparse connected polyominoes at canonical canvas scale. Candidate mask pairs are accepted only if:

1. all three transformed red masks differ;
2. blue and every transformed red mask have overlap and exclusive cells;
3. union/intersection/xor are nonempty and non-solid; and
4. changing either control changes the final normalized/cropped output.

The fourth condition must be evaluated after normalization. An earlier draft compared absolute result coordinates, which allowed two different absolute masks to crop to the same visible output. A focused regression now guards this failure mode.

## Semantic ambiguity addressed

The four canonical demonstrations never contain transform control `7`. Therefore these rules both fit every canonical demonstration:

- interpret `7` as rotate-clockwise (`8`);
- interpret `7` as horizontal reflection (`9`).

Both fail on the canonical query. The generator declares them in `CANONICAL_SHORTCUTS`, emits a transform-`7` witness in every three-demo lesson, and verifies all twelve single-branch control aliases through `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`.

## Verification

- Focused pytest: all tests pass.
- Official after battery: 12/12 stages green.
- Profile floor: 60/60 exact and 60/60 envelope.
- Semantic gate: 600/600 strict; six witness classes fire in all bands; every rival claim holds 60/60; 12/12 lessons identifiable.
- Override contract: 5,310/5,310 accepted; no findings or warnings; unknown keys rejected.
- Rule smoke: 120 applications, 0 crashes, 97 distinct outputs, 120/120 mirror parity.
- Self-check: 60/60 defaults clean, all five canonical inputs accepted, 60/60 destructive mutations rejected.
- Independent solve: one revision and 3/3 visible examples; masked-query correctness remains withheld by the reviewer protocol. Prior rule exposure was recorded honestly as `yes`, with reference consultation `no`.

## Remaining limitations

- Difficulty changes mask-size/box sampling, not the semantic branch schedule; this is deliberate so every band teaches the same dictionary.
- The finite rival set proves the intended twelve control aliases are eliminated, not that every imaginable program is eliminated.
- Python `rule_mirror` is a diagnostic mirror. The synchronized Racket program remains the rule authority.
- Canonical canvases are intentionally retained instead of exploring large grids; morphology diversity comes from shapes, placements, and all nine control profiles.
## Current reviewer considerations

Source SHA-256: `b2e95fc62d0e6005f1868935d880fe2e9b58eeba0032c48bd84772d048359cb3`.

# Decisions for e942ce41cbf5

## D1 — Preserve the canonical transformation and pin it

**Choice.** Keep the canonical normalize/transform/set-operation/crop rule unchanged and add `RULE_HASH = "7aa66cd7d9ab"`.

**Original rationale.** The imported generator and Racket code already targeted the right task semantics. The missing hash was a provenance defect, not evidence that the rule needed replacement.

**Alternatives considered.** Rewrite the Racket rule; edit canonical data; treat the base-bank text as a separate authority.

**Probe.** The Python mirror matched all four canonical demonstrations and the canonical query. Racket smoke and mirror parity passed 120/120 after synchronization.

**Failure modes/limitations.** A hash pins source identity, not semantic correctness. Execution parity and canonical examples remain necessary.

## D2 — Synchronize active authority text, not behavior

**Choice.** Replace the selected base-bank `target_code` with the exact canonical `program_solution`. The two removed comments were behavior-neutral.

**Original rationale.** Unknown; the baseline appeared to contain an unsynchronized beautified copy.

**Alternatives considered.** Relax authority sync to comment-normalized equality; leave the failure documented.

**Probe.** Before: two active exact-text groups with sampled execution parity. After: one exact group and execution parity pass.

**Failure modes/limitations.** Exact-text synchronization can create noisy changes for comments, but it removes ambiguity about which source is authoritative.

## D3 — Remove inert and invalid public axes

**Choice.** Keep only `grid_h`, `grid_w`, `op_control`, and `transform_control`. Set helpful and degenerate texture declarations to empty tuples.

**Original rationale.** The v2.1.0 axis list seems inherited from a generic combinatorial template. The named palette and texture values were not implemented as meaningful lawful variation.

**Alternatives considered.** Implement all advertised palette/texture semantics; retain negative fixtures under a lawful-degenerate declaration; hide them without changing the schema.

**Probe.** Baseline defect lint found four dead helpful textures and negative fixtures in the ordinary domain. After override testing accepted 5,310/5,310 draws with no findings, and unknown keys were rejected.

**Failure modes/limitations.** The narrower contract offers fewer knobs, but every remaining knob has exact semantics and is testable.

## D4 — Use canonical canvas profiles

**Choice.** Schedule only `(10,11)`, `(10,13)`, `(11,11)`, and `(11,12)` by default; allow the finite cross-product `10|11 × 11|12|13` under explicit overrides.

**Original rationale.** The baseline’s difficulty ranges (`10..18` by `13..22`) favored much larger canvases, probably to increase visual variety.

**Alternatives considered.** Preserve the broad ranges; mix canonical anchors with large exploratory canvases; add scale as a private teaching branch.

**Probe.** Baseline exact support was 2/60 and zero in medium/hard. After support is 60/60 exact and 60/60 within the canonical envelope, with 100% unique generated inputs in the diversity probe.

**Failure modes/limitations.** Large-grid extrapolation is no longer trained. Shape and control diversity carry the variation instead.

## D5 — Use sparse connected polyominoes

**Choice.** Grow 4-connected masks of 4–8 cells in small boxes, rejecting solid rectangles and disconnected shapes.

**Original rationale.** Baseline masks were random partitions of a bounding box with shared/exclusive cells. This made set operations nontrivial but produced dense masks unlike the canonical examples.

**Alternatives considered.** A fixed catalog of canonical-like shapes; unconstrained random cells; dense masks with explicit holes.

**Probe.** `strict_canonical_like` accepted 600/600 generated draws and all five canonical inputs. The morphology gate and diversity probe both passed.

**Failure modes/limitations.** Connectedness is stronger than the abstract rule strictly requires; it is a fidelity prior derived from canonical morphology.

## D6 — Guarantee every control branch in every three-demo lesson

**Choice.** Set `EXAMPLES_NEEDED = 3`, cycle operations by sample index, and cycle transforms with a seed phase.

**Original rationale.** The baseline sampled both controls independently, so a short lesson could omit a branch or repeat controls.

**Alternatives considered.** Pure random sampling plus rejection at lesson assembly; six demonstrations; a fixed nine-profile block.

**Probe.** Every tested three-example window over all bands, twelve seeds, and nine starts contained `{3,4,6}` and `{7,8,9}`. The semantic gate represented all nine pairings and found 12/12 sampled lessons identifiable. The independent shortcut probe found 216/216 identifiable.

**Failure modes/limitations.** Operation and transform profiles are correlated within a single seed phase. Pooling seeds covers all nine pairings, while each lesson prioritizes dictionary completeness.

## D7 — Require visible differences after final normalization

**Choice.** Reject a mask pair unless changing any operation or transform changes the final normalized/cropped output.

**Original rationale.** The baseline guaranteed overlap and exclusive cells only for the selected branch; it did not prove that alternate controls were visibly distinguishable.

**Alternatives considered.** Compare pre-crop absolute masks; rely on random chance; check only the selected branch.

**Probe.** A draft using absolute-coordinate comparison admitted pairs whose alternatives collapsed after cropping. A regression now enumerates all three operation and transform outputs and requires three distinct rendered results for each axis.

**Failure modes/limitations.** Rejection sampling costs some generation time, though rule smoke p95 remained about 11.5 ms and no generation crashes occurred in the semantic census.

## D8 — Make structural validity exact

**Choice.** Require exactly one operation control at bottom-left, exactly one transform control at bottom-right, only expected colors, two nonempty connected masks off the control row, and a lawful selected result.

**Original rationale.** The original self-check searched the palette for any operation and treated absence of `8`/`9` as identity, so missing control `7` could pass.

**Alternatives considered.** Preserve permissive canonical parsing; validate only generated instances; add a separate strict checker.

**Probe.** Baseline rejected 0/15 absent-color mutations. After self-check rejected 60/60 destructive mutations and accepted all five canonical inputs.

**Failure modes/limitations.** Inputs encoding identity by omission are deliberately rejected because the task grammar uses an explicit `7` marker.

## D9 — Declare rivals and witnesses as executable code

**Choice.** Define all twelve single-control aliases, six branch witnesses, witness-to-rival claims, two canonical shortcuts, and `lesson_identifiable`.

**Original rationale.** None existed in v2.1.0.

**Alternatives considered.** Document rival rules only in prose; test only the two canonical `7` aliases; rely on branch-frequency coverage.

**Probe.** Every witness class fired in every difficulty band. Each claimed rival disagreed on 60/60 checked witness cases. No declared rival survived any of 12 official or 216 focused lessons.

**Failure modes/limitations.** More complex relational shortcuts could exist outside the named finite set. The reusable probe is intended to make additions cheap.

## D10 — Add a Python mirror while retaining Racket authority

**Choice.** Implement `rule_mirror` from independent set/transform helpers and use it for tests, witnesses, and lesson assembly.

**Original rationale.** The baseline relied only on external Racket execution.

**Alternatives considered.** Call Racket for every semantic probe; duplicate stored outputs; parse the Racket source.

**Probe.** After rule smoke reported 120/120 Python/Racket parity with zero mismatches and no input mutation.

**Failure modes/limitations.** Parallel implementations can drift; the battery’s mirror-parity check is therefore required.

## D11 — Add focused tests and a future-agent probe

**Choice.** Add eight focused pytest regressions and `workspace/shortcut_probe.py` with text/JSON output.

**Original rationale.** The selected task had no task-local regression suite or shortcut reproducer.

**Alternatives considered.** Rely only on the shared battery; place one-off scripts outside the returned patch.

**Probe.** The probe test was written first and failed because the tool did not exist, then passed after implementation. The full focused suite passes, and the default probe checks 216 lessons with zero survivors.

**Failure modes/limitations.** The probe uses the Python mirror for speed; Racket parity remains a separate battery responsibility.

## D12 — Native post-transform control-4 parametric family (review-8aee66b709b13528)

**Choice.** Preserve the selected canonical program byte-for-byte as `operation_policy=canonical`. Add `rank_control4`, which first normalizes the two masks and applies the visible red transform, then—only for control 4—chooses the smaller post-transform result between intersection and XOR. Controls 3 and 6 retain canonical union/XOR behavior.

**Why this family.** An earlier symmetric rank-all-nonunion draft made both minimum demonstrations look like XOR, allowing an `always_xor` shortcut. Restricting the changed behavior to control 4 produced a two-setting matched-input family whose minimum two-demo lesson visibly teaches both possible control-4 outcomes while preserving the original control dictionary elsewhere.

**Sequential dependency.** Step A computes the transformed red mask and the post-transform intersection/XOR counts. Step B consumes that ordering to select the control-4 result. A retained 30x30 qualified query reverses the raw ordering after reflection; replacing the intermediate with the pre-transform ordering changes the final protected-Racket output.

**Lesson construction.** Demonstration 0 is the post-transform-order reversal. Demonstration 1 constructively distinguishes identity, clockwise rotation, and horizontal reflection and produces the opposite control-4 choice. Demonstration 2 exercises unchanged XOR behavior. The family supports 2–6 demonstrations and 1–4 deterministic, prefix-stable queries; the fourth query is a substantive boundary-spanning 30x30 case. Public projection hides settings, programs, future queries, and labels.

**Evidence.** `workspace/parametric/self_audit.py` passed 64 episodes, 320 two-to-six-demo prefixes, 1,920 broad named-rival checks, 120 protected-Racket rival checks, 64 substantive 30x30 checks, and two wrong-intermediate protected counterfactuals. Native qualification passed both settings at seeds 0 and 17 (4/4 jobs, 40 protected-Racket label evaluations). The standardized source-bound witness is under `checks/e942ce41cbf5/causal/witness.json` in the return packet.

**Portability repair.** The inherited focused test no longer assumes a fixed checkout depth or unstaged local package; it locates canonical data through `reviewer_support.find_root` and `canonical_pairs`.

**Limits.** The bounded rival set is not a universal uniqueness proof. Production `generator.py` and canonical authority remain unchanged. Reviewer status is ready, but exact-source owner admission, fresh acceptance, and any training activation remain pending.
