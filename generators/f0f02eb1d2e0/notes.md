# Working notes: f0f02eb1d2e0

## Current decision

Use the unchanged canonical Racket rule `bf8c9dd4f7fa` and generator version `3.0.0`. The generator treats colors independently: a color is completed only when it has exactly three cells on exactly two rows and two columns. Bent three-cell sets spanning a 3×2 or 2×3 box, diagonal pairs, lines, and already complete rectangles are lawful no-ops.

The production lesson is four demonstrations plus one query. Default samples follow a seed-independent four-profile cycle. Every cyclic four-profile window supplies redundant evidence for five declared competitors, and every allowed query rotation must remain identifiable.

## Reversed choices

The imported `2.1.0` sampler advertised inert single-token `position_bias` and `density` controls, four ignored helpful textures, and three invalid degenerate textures. It had no `RULE_HASH`, semantic witnesses, executable rivals, or lesson contract. It sampled only simple exact targets, allowing the prior retained shortcut “complete every noncollinear three-cell bounding box.” That design was replaced rather than patched incrementally.

An intermediate `3.0.0` draft used one canonical-envelope profile in every four samples. The shared pinned profile census observed only 12/60 canonical-profile hits, below the 25% floor. A failing regression captured that exact census; profile 1 was then kept at canonical dimensions/palette while carrying a bent-three-cell no-op. Final support is 29/60: easy 11/20, medium 6/20, hard 12/20.

## Exact controls

Only pixel-observable controls are exposed: `grid_h`, `grid_w`, `n_targets`, `n_bent_decoys`, `n_other_decoys`, and `corner_offset`. All legal joint combinations are constructively supported; unknown, mistyped, and out-of-range controls fail loudly. No incompatible combinations are declared.

## Evidence and reusable probes

- Prior lead consulted: `review-45b274eb01fbf4c5:v0001`, specifically its noncollinear-bounding-box finding.
- Minimal Racket-labelled contrast: `counterexamples/review-2570c321002ebca3-v0001/counterexample.json`.
- Exhaustive task-local schedule/override probe: `workspace/probe_curriculum.py`.
- Focused regressions: `tests/test_generator.py`.

Final generator SHA-256: `298856f2690d5a5a8bfe71c6ce9adeb703684a9df4f5a6180620d9ab1b9cc27c`.

## Known limits

The retained checks establish the rule against five declared plausible competitors, not every possible hypothesis. The production sampler intentionally covers a bounded configuration grammar and at most four target colors, two bent decoys, and two other decoys. Query-rotation support is claimed only for the materialized four-profile curriculum and the tested cyclic starts; it is not a proof of universal induction.
## Current reviewer considerations

Source SHA-256: `298856f2690d5a5a8bfe71c6ce9adeb703684a9df4f5a6180620d9ab1b9cc27c`.

# Decisions: f0f02eb1d2e0

## D1 — Keep the canonical Racket authority unchanged

**Choice.** Pin `RULE_HASH = "bf8c9dd4f7fa"` and change only the sampler, semantic contract, focused tests, and review evidence.

**Rationale.** All three canonical pairs and the retained base solution agree with the rule: complete a color only when it has exactly three cells spanning exactly two rows and two columns. Racket rule smoke, authority sync, and the independent Python mirror agree on final source.

**Rejected alternative.** Broaden the Racket rule to complete any noncollinear three-cell bounding box. That is exactly the canonical-fitting shortcut the repair must refute; it changes lawful bent-three-cell no-ops.

**Failure mode/limit.** The Python mirror is test support, not label authority. Final labels remain Racket-derived.

## D2 — Replace the imported sampler rather than preserve its axes

**Choice.** Remove `position_bias`, `density`, `palette_size`, and `texture`; expose only six exact, observable controls.

**Original choice.** Imported `2.1.0` advertised two single-token axes, one effectively fixed palette-size axis, four ignored helpful textures, and three invalid degenerate textures in the same ordinary domain.

**Reason for reversal.** Baseline lint and defect lint reproduced missing rule pinning, unprobeable controls, dead textures, and texture-domain overlap. Keeping names while inventing semantics would make old calls look compatible while changing their meaning.

**Probe.** The shared override gate tested 327 exact cases in each of three bands for 30 seeds, plus deterministic replay and an unknown-key probe.

**Failure mode/limit.** The new API is deliberately incompatible with undocumented old override calls; they now fail loudly instead of silently doing nothing.

## D3 — Use a four-profile curriculum with four demonstrations

**Choice.** Set `EXAMPLES_NEEDED = 4` and use a seed-independent period-four schedule. Test every cyclic start and every possible query position.

**Rationale.** A single canonical anchor cannot simultaneously carry all useful negative evidence without becoming crowded and distributionally unlike the source task. Four profiles permit canonical anchors plus redundant bent, diagonal, long-span, >2-target, and noncanonical-dimension evidence. Each competitor is refuted at least twice in every task-local four-pair window.

**Rejected alternatives.** Randomly scatter witnesses and hope each lesson receives them; or use a longer schedule with only one witness for each shortcut. Both make complete-lesson support fragile under query rotation.

**Probe.** `workspace/probe_curriculum.py` iterates the actual `LESSON_COMPETITORS` declaration over 12 cyclic windows and 48 rotations.

**Failure mode/limit.** This supports the selected lesson assembly and tested cyclic starts, not arbitrary subsampling of unrelated profiles.

## D4 — Treat bent triples and diagonal pairs as lawful no-op evidence

**Choice.** Admit per-color no-op configurations in `self_check`, while requiring at least one true target so the overall pair is non-identity.

**Rationale.** The exact distinction is negative: shape cardinality alone is insufficient. Bent triples distinguish exact two-row/two-column targets from a loose bounding-box rule; diagonal pairs distinguish “complete any implied rectangle” from the exact three-cell trigger.

**Counterexample.** `counterexamples/review-2570c321002ebca3-v0001/counterexample.json` is Racket-labelled and covered by a focused test.

**Rejected alternative.** Keep `self_check` target-only and test rivals on out-of-domain grids. That would not improve training data because the production sampler could never emit the distinguishing evidence.

## D5 — Preserve canonical distribution support while broadening semantics

**Choice.** Profiles 0 and 1 remain within canonical dimensions/palette size; profiles 2 and 3 broaden dimensions and semantics.

**Reason for revision.** The first repair draft had one canonical-envelope profile per four default indices but the shared pinned census samples off-diagonal indices; it observed 12/60, below the 25% floor. A regression copied the exact seed/index recipe, failed red, and profile 1 was revised to retain canonical dimensions/palette while carrying a bent no-op.

**Result.** Final exact support is 29/60: easy 11/20, medium 6/20, hard 12/20.

**Failure mode/limit.** Canonical-profile matching uses dimensions and palette cardinality; it does not claim every generated structural composition is canonical.

## D6 — Declare executable competitors, not prose-only claims

**Choice.** `CANONICAL_SHORTCUTS` contains the four shortcuts that fit all usable canonical pairs; `LESSON_COMPETITORS` adds adjacent-only completion. Witness-to-rival claims are executable.

**Rationale.** A frequency statistic for bent/diagonal examples does not prove they occur in a complete lesson or actually change a rival’s output. Executable rivals permit canonical-fit checking, lesson survival testing, and query prediction comparison.

**Failure mode/limit.** Five rivals are a useful adversarial set, not an exhaustive hypothesis class.

## D7 — Keep before evidence honest

**Choice.** Report the untouched before battery as incomplete, while citing its completed stage checkpoints.

**Rationale.** The outer process interrupted the aggregate run repeatedly. A running aggregate with pending stages is not a battery pass. Finished stage outputs still reproduce the relevant defects.

**Rejected alternative.** Infer the untouched aggregate result from later one-stage runs. That would erase execution history and overstate evidence.

## D8 — Audits are findings-only

**Choice.** Leave `cdf26af5c935` and `f0e701850a95` byte-for-byte unchanged and retain separate Racket-backed reproducers under `checks/audit/`.

**Rationale.** The assignment requests adversarial findings, not repairs, for those targets. Their source hashes match `AUDIT_ASSIGNMENT.json`.
