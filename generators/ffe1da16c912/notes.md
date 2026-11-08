# Working notes: ffe1da16c912

## 2026-10-02 review `review-fbbfb8ac285f8294`

### Baseline findings

Version 2 passed the rule and broad distribution checks but failed three battery stages:

- lint: no `RULE_HASH`, and `proto_shapes` was declared but not probeable;
- defect lint: easy, medium, and hard were byte-identical;
- override contract: no exact realization observer, phantom shape axis, and unknown overrides were silently accepted.

The semantic gate was advisory because no semantic contract or lesson-level rival analysis existed.

### Selected design

Version 3 enumerates connected 3×3 shape families modulo D4 for cell counts 4, 5, and 6. All three prototypes in a sample have the same area and pairwise-distinct D4 families. The matched family is drawn from the full eight-image orbit subset. Match positions cycle over 0, 1, 2 and transforms follow `id, fh, r1, fv, r2, tr, r3, atr`; the complete joint product appears every 24 samples.

The strongest canonical shortcut is “choose the leftmost prototype with the query's occupied-cell count.” It fits both canonical demonstrations and fails the canonical test. Equal-area generated prototypes make this shortcut choose panel 0, while each three-example lesson includes correct matches at panels 1 and 2.

### Validation

- focused pytest: 80/80 pass;
- official after battery: 12/12 green;
- semantic gate: 600/600 strict, 3/3 canonical accepted, 2/2 grouped witnesses, 2/2 rival claims, 12/12 lessons identifiable;
- override gate: 6,480/6,480 accepted draws over 72 cases and three bands; unknown key rejected;
- rule smoke: 120 applications, zero crashes, 100 distinct outputs, Python/Racket mirror 120/120;
- authority sync: selected sources exact, archival source text-divergent, execution parity PASS.

### Implementation corrections retained as evidence

The first implementation passed scheduled singleton domains to the draw helper even for explicit overrides, causing 71 of 80 focused tests to fail. The corrected path consumes each axis once: full declared domain for an explicit override, scheduled singleton for a natural draw.

A later dynamic check found that `mutation_fixtures` must be a zero-argument hook returning `(name, grid)` pairs. The hook was corrected; the check was not weakened.

### Known limitations

The natural distribution is intentionally limited to the rule's fixed 3×15 grammar and 4–6-cell prototype families. Difficulty changes area but is not a proven monotonic reasoning scale. The deterministic curriculum requires callers to advance `sample_index`. The task still needs independent monitor review before approval.

Imported associated notes, if any, retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `628f4406f88e82c7792de1a6865100c7b611ca3ab139452b56d103017c670a30`.

# Design decisions for `ffe1da16c912`

## D1. Preserve the selected Racket rule

**Input choice.** Keep the canonical and selected task-local rule unchanged and pin its normalized hash as `c4020b613ba0`.

**Original rationale.** The precise authorship rationale is unknown. The rule itself is explicit: split the 3×15 grid into four 3×3 panels, match the query support to one of three prototype families under D4, and emit the displayed prototype support in the query color.

**Alternatives considered.** Rewrite the rule for style, copy the archival text into the selected authority, or alter the rule to accommodate broader panel layouts.

**Probes.** Canonical self-check accepted all 3 canonical inputs; Racket smoke applied the rule to 120 revised inputs with no crash; Python mirror parity was 120/120; authority sync reports selected exact synchronization and execution parity across both distinct source texts.

**Failure modes and limitation.** A future source migration can still desynchronize authorities. The archival source remains text-divergent, though execution-equivalent. Re-run authority sync after any rule-source edit.

## D2. Use `cell_count` as the difficulty axis

**Input choice.** Easy uses 4 cells, medium/default 5, and hard 6.

**Original rationale.** The prior `proto_shapes` declaration was not probeable, and all difficulty bands were byte-identical. A visible cell-count axis is simple, exact, and reconstructable from the grid.

**Alternatives considered.** Random 3–6-cell sizes independent of difficulty; larger panels; changing prototype count; or difficulty-specific transform subsets.

**Probes.** Defect lint no longer reports dead bands; override testing covers every 4/5/6 value; `observe_overrides` recovers the exact value; canonical 3-cell examples remain accepted by the validator.

**Failure modes and limitation.** Cell count is a distributional difficulty signal, not a guaranteed reasoning-difficulty ordering. Natural 3-cell generation is omitted for curriculum-support reasons.

## D3. Give all three prototypes equal area

**Input choice.** Within an example, all prototypes and the query have the same occupied-cell count.

**Original rationale.** Unknown for the baseline. In the canonical demonstrations, the intended family can be selected by “leftmost prototype with the query's area,” which is the strongest plausible shortcut.

**Alternatives considered.** Let prototype sizes vary naturally, or merely include occasional equal-area collisions.

**Probes.** The named rival `same_count_leftmost` fits both canonical demonstrations and fails the canonical test. In revised samples it always chooses panel 0, while the scheduled correct index cycles through 0, 1, and 2. Semantic-gate rival claims and 12/12 lesson checks pass.

**Failure modes and limitation.** Equal area removes one shortcut but also reduces one source of superficial variety. Shape-family and color variety carry the useful diversity instead.

## D4. Enumerate connected 3×3 D4 families instead of rejection-sampling arbitrary shapes

**Input choice.** Precompute all connected 4-, 5-, and 6-cell subsets of a 3×3 panel modulo D4.

**Original rationale.** The baseline used bounded random growth plus a fixed fallback. Its output was valid, but it offered no proof that each band had enough distinct families or that the matched family exposed all transforms.

**Alternatives considered.** Handwritten shape tables, unbounded rejection sampling, or retaining the previous fallback.

**Probes.** The census finds at least three D4-distinct families and at least one eight-image family for every selected cell count. Import-time assertions guard that assumption. Exact-axis tests cover all 72 combinations.

**Failure modes and limitation.** The enumeration is tied to 3×3 panels and the selected 4–6-cell range. Enlarging the grammar would need a new census and performance review.

## D5. Require the matched prototype to have eight distinct D4 images

**Input choice.** The family selected by the query comes from the full-orbit subset; distractors need only be D4-distinct families.

**Original rationale.** Unknown for the baseline. Symmetric matched shapes make some requested transform labels observationally indistinguishable.

**Alternatives considered.** Permit symmetric matched shapes and report a set of possible transforms; expose transform only in metadata; or constrain all three prototypes to full orbits.

**Probes.** `observe_overrides` recovers exactly one transform for every generated sample; the override gate passes all eight transform values; focused tests cover every transform × position × cell-count combination.

**Failure modes and limitation.** Distractors may be symmetric because their exact displayed transform is irrelevant to the rule. This is intentional, but consumers should not infer that every prototype has eight distinct images.

## D6. Schedule match position and transform by `sample_index`

**Input choice.** Match position is `sample_index mod 3`; transforms follow `id, fh, r1, fv, r2, tr, r3, atr`.

**Original rationale.** The baseline drew these independently at random. Random sampling can leave a short lesson without a position or reflection witness.

**Alternatives considered.** Fully random draws, a random permutation per lesson, or separate position/transform periods.

**Probes.** Every three consecutive examples cover positions `{0,1,2}` and include a reflection; every 24 cover all 24 position-transform pairs. Tests verify the exact schedule and 12/12 generated lessons are identifiable.

**Failure modes and limitation.** A caller that never advances `sample_index` sees only the first profile. The schedule intentionally prioritizes lesson coverage over independent per-example randomness.

## D7. Keep four distinct visible colors and reserve 0 and 5

**Input choice.** Draw four distinct colors from `{1,2,3,4,6,7,8,9}`: one per prototype and one novel query color. Color 0 is background and 5 is the separator.

**Original rationale.** The baseline already excluded background and divider colors, but did not make the four colors explicitly distinct through the contract.

**Alternatives considered.** Reuse prototype colors, allow query color to equal the matched prototype, or use a smaller palette.

**Probes.** Self-check enforces monochrome panels and divider purity; semantic rival `keep_prototype_color` is refuted; semantic gate verified that rival on 60/60 authoritative checks.

**Failure modes and limitation.** Distinct colors make recoloring highly visible and may make that subrule easier. This is preferable to hiding it accidentally; color choice still varies across seeds.

## D8. Keep the canonical 3×15 layout fixed

**Input choice.** Four 3×3 panels separated by solid color-5 columns.

**Original rationale.** The selected Racket authority explicitly splits four panels from this layout.

**Alternatives considered.** Variable panel sizes, vertical arrangements, variable separators, or more prototypes.

**Probes.** Canonical inputs and all generated inputs pass the strict grammar. Mutation fixtures reject a broken separator and duplicate prototype family.

**Failure modes and limitation.** Layout invariance is a learnable cue. Varying it would require a justified rule change, not merely a generator edit.

## D9. Reject unknown controls and make exact overrides observable

**Input choice.** Unknown difficulty values and unknown override keys raise `ValueError`; each declared axis is consumed exactly once and reconstructed from the output grid.

**Original rationale.** The baseline silently accepted unknown keys, declared an unprobeable axis, and lacked `observe_overrides` for `match_index`.

**Alternatives considered.** Ignore extra keys for backward compatibility or mark axes diagnostic-only.

**Probes.** The final override gate passes 6,480 draws over 72 cases and three bands, with unknown-key verdict `rejected`.

**Failure modes and limitation.** Strict rejection can break callers that relied on misspelled or retired keys, but silent acceptance made test results misleading.

## D10. Add an independent Python rule mirror and full structural analyzer

**Input choice.** Parse grid facts from pixels, validate grammar, find the unique D4 family match, and generate the expected output independently of hidden generation metadata.

**Original rationale.** The baseline checker covered only broad structure and could not support exact override or rival checks.

**Alternatives considered.** Trust generation metadata, call Racket for every local assertion, or use a minimal shape-only checker.

**Probes.** Python/Racket mirror parity is 120/120; canonical outputs match; destructive mutation checks and grammar gate pass.

**Failure modes and limitation.** The mirror and selected rule could share a conceptual mistake. Canonical examples plus authoritative Racket execution reduce, but do not eliminate, that risk.

## D11. Declare explicit rivals and use three-example lessons

**Input choice.** Rivals are fixed-panel selection, same-area-leftmost, rotations-only fallback, copying query orientation, and keeping prototype color. Three demonstrations are required so all three prototype positions can appear.

**Original rationale.** The baseline had no semantic or lesson contract.

**Alternatives considered.** One or two demonstrations, one witness per rival, or only prose documentation.

**Probes.** Semantic gate reports 600/600 strict inputs, 2/2 grouped witnesses, all declared rival claims verified, and 12/12 identifiable lessons across all bands.

**Failure modes and limitation.** This rival set is strong but not mathematically exhaustive. Future audits should add a rival only when a concrete surviving hypothesis is found.

## D12. Group semantic witnesses into two obligations

**Input choice.** One witness group covers selection shortcuts; the other covers transform/orientation/color shortcuts.

**Original rationale.** A one-witness-per-rival draft multiplied authoritative Racket bridge work without adding distinct generated grids.

**Alternatives considered.** Seven separate witnesses or one catch-all witness.

**Probes.** The final strict gate verifies both groups and each attached named rival; the full battery completes green.

**Failure modes and limitation.** Grouping makes per-witness counts less granular. Per-rival counts remain available in the semantic-gate evidence.

## D13. Add focused tests before relying on the full battery

**Input choice.** A task-local pytest suite covers rule pinning, canonical parity, strict control rejection, all 72 exact axis combinations, band distinctions, shortcut elimination, schedule coverage, determinism, freshness, and global RNG purity.

**Original rationale.** There was no task-local test suite.

**Alternatives considered.** Rely solely on the repository battery or add only smoke tests.

**Probes.** The test-first run failed; the first implementation run exposed 71 override-domain failures; the corrected suite passes 80/80. The independent 12-stage battery then passes.

**Failure modes and limitation.** Tests exercise the declared grammar and known rivals, not every possible learner hypothesis.
