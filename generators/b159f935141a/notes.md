# Current notes: `b159f935141a`

## Intended rule and authority

For every zero cell, fill it with color `v` iff its four cardinal neighbors are all the same nonzero `v`. Preserve every other cell. The selected Racket/canonical rule is unchanged and pinned as `RULE_HASH = "d4bb39745d13"`.

## Current sampler

Version `3.1.0` uses a period-4 schedule:

1. one exact canonical-size two-plus profile;
2. a compact contrastive profile emphasizing three-arm evidence;
3. a compact contrastive profile emphasizing mixed-arm evidence;
4. a compact joint contrastive profile.

Contrastive profiles contain true hollow pluses plus separated decoys drawn from horizontal pairs, vertical pairs, three arms, mixed arms, occupied centers, and diagonal clusters. Five-cell slot spacing prevents motif interactions. Default contrastive area is capped at 104/117/126 cells for easy/medium/hard.

Exact axes are `grid_h` 5..22, `grid_w` 5..22, `n_plusses` 1..8, and `n_decoys` 0..8. `observe_overrides` recovers all four from pixels. Joint requests that exceed separated-motif capacity raise structured incompatibility errors.

## Semantic contract

Declared competitors are `horizontal_only`, `vertical_only`, `three_arms`, `mixed_majority`, `overwrite_occupied`, and `diagonals_also`. Witnesses are diagonal clusters, occupied centers, three-arm motifs, and mixed-arm motifs. Every three-demonstration subset of a scheduled four-pair lesson refutes all declared competitors; `lesson_identifiable` checks the actual labeled demonstrations and query.

## Decisions reversed during review

- Baseline nominal `position_bias`, `density`, and texture controls were removed because they were non-probeable, dead, or overlapping.
- An initial large contrastive layout was reduced after distribution drift (~224 generated cells versus canonical ~36).
- Fixed decoy counts were replaced with a 3..5 default range after axis-span evidence.
- Difficulty now changes count/area/layout support after dead-band evidence.
- Diagonal and occupied witnesses were made redundant after an intermediate schedule produced 14/48 ambiguous held-out-query rotations.
- Canonical dimensions are recorded as exact choices so provenance remains honest without hiding contrastive choice support from static analysis.

## Final evidence and limits

Final generator SHA-256: `d060270b16f1515c9dedbaa944256700a5da3608ada0bb82bb7bd432e2301460`.

- Final battery: 12/12 green with required rotations.
- Task tests: 14/14 pass.
- Census: 300/300 production lessons and 1200/1200 query rotations have no ambiguity against the six declared competitors; 1135 unique inputs.
- Exact shortcut reproducer: `counterexamples/horizontal-only.json`.

Finite competitor checks do not prove universal rule identifiability. Catalog approval/training safety remains outside this generator patch. No prior return was used as a lead.
## Current reviewer considerations

Source SHA-256: `d060270b16f1515c9dedbaa944256700a5da3608ada0bb82bb7bd432e2301460`.

# Decisions: `b159f935141a`

## D1 — Preserve the canonical authority

**Choice.** Keep the Racket/canonical rule unchanged and pin `RULE_HASH = "d4bb39745d13"`.

**Rationale.** Canonical examples, the selected Racket rule, and the Python mirror agree on a simple local law: fill a zero cell exactly when all four cardinal neighbors are the same nonzero color. The defect was in sampling and teaching support, not label authority.

**Alternatives rejected.** No rule rewrite or canonical-row edit was justified. Changing authority merely to accommodate a weak sampler would have hidden the real problem.

**Probe/evidence.** Final `rule_smoke`, `racket_lint`, and `authority_sync` all pass in `checks/final-battery/`.

## D2 — Replace nominal controls with four exact, observable axes

**Prior choice.** The baseline exposed `position_bias` and `density`, but each had only one token and could not be meaningfully probed. Texture controls were dead or overlapping.

**New choice.** Advertise only `grid_h`, `grid_w`, `n_plusses`, and `n_decoys`. Validate types/ranges before generation and recover all four values from pixels with `observe_overrides`.

**Rationale.** These controls directly change the generated grid, can be round-tripped independently of draw provenance, and let tests state exact expectations.

**Alternatives rejected.** Keeping decorative axes as “diagnostic” was rejected because they added no useful training support. Randomly approximating requested counts was rejected because exact overrides are a contract.

**Failure modes and limits.** Separated motifs have finite capacity. Impossible joint requests raise a structured incompatibility over the involved axes. The full override matrix accepted 13,500/15,120 draws and explicitly rejected 1,620 impossible combinations with no contract findings.

## D3 — Use a period-4 curriculum with one canonical and three contrastive profiles

**Choice.** `sample_index % 4` selects `canonical`, `contrastive_three`, `contrastive_mixed`, or `contrastive_joint`.

**Rationale.** A canonical branch preserves the original small shape/palette regime. Three contrastive branches teach boundary cases often enough that a normal three-demonstration-plus-one-query lesson distinguishes the intended conjunction.

**Alternatives considered.** Pure random mixing could omit a needed witness from a small lesson. A positive-only canonical sampler was too ambiguous. A schedule containing only contrastive examples risked distribution drift and losing canonical support.

**Ordering/query policy.** The production materializer uses three demonstrations and one query. Required rotation checks hold out each of the four materialized pairs in turn. The task-local test additionally enumerates all four cyclic schedule starts.

## D4 — Add executable rivals and explicit witness motifs

**Choice.** Declare six wrong-but-plausible rules:

- `horizontal_only`;
- `vertical_only`;
- `three_arms`;
- `mixed_majority`;
- `overwrite_occupied`;
- `diagonals_also`.

Witnesses are diagonal clusters, occupied centers, three-arm motifs, and mixed-arm motifs. The diagonal witness also refutes the horizontal/vertical pair shortcuts induced around it.

**Rationale.** These are the strongest local relaxations of the intended four-way conjunction that fit the clean canonical pluses. Executable rivals let the semantic gate test outputs, rather than trusting names or frequency counts.

**Alternatives rejected.** Merely asserting witness names without rival functions would not show a disagreement. Treating induced pair signatures around a diagonal cluster as four extra primary decoys made exact counts dishonest, so `_primary_decoys` folds those signatures into the single diagonal motif.

## D5 — Redundantly teach occupied and diagonal exclusions

**Prior choice.** An intermediate schedule placed some rival-refuting evidence in only one pair of the four-pair episode.

**Failure.** Required query rotation found 14/48 ambiguous rotations: when that pair became the query, `overwrite_occupied` or `diagonals_also` fit all remaining demonstrations. Evidence is retained in `checks/after-semantic-required/`.

**New choice.** Every contrastive profile starts with diagonal and occupied motifs; three-arm and mixed-arm evidence is also distributed so every three-pair demonstration subset refutes all six rivals.

**Evidence.** Final semantic smoke: 0/48 ambiguous rotations. Large census: 0/1200. Exhaustive local test: all bands × six seeds × four cyclic starts × four query positions pass.

## D6 — Keep contrastive grids compact and motifs isolated

**Prior choice.** Six widely spaced motifs forced examples near 13×17 (about 224 cells), triggering distribution drift from canonical area ~36.

**New choice.** Use a five-cell-spaced slot lattice, cap default contrastive area by band (easy 104, medium 117, hard 126), and limit default total motifs to at most six.

**Rationale.** Five-cell spacing prevents arms from adjacent motifs from accidentally forming a target or a new pair decoy. The area cap keeps examples near the canonical visual scale while still fitting the teaching set.

**Alternatives rejected.** Dense packing without a proof of noninteraction was rejected. Suppressing the distribution detector was rejected because the drift was real.

## D7 — Make count and difficulty controls non-dead

**Prior failures.** One intermediate revision always drew exactly two decoys; another produced byte-identical easy/medium/hard examples for every sampled seed.

**New choice.** Plus counts vary by band and phase; decoy counts vary from 3 to 5 by default; the area envelope and keyed layout RNG depend on difficulty.

**Evidence.** Focused tests require at least a two-value span for plus and decoy counts and require at least one seed to differ across difficulty bands. Final defect lint reports zero findings.

**Limit.** Difficulty changes density/size/layout, not the logical rule. This is intentional.

## D8 — Record exact canonical provenance without narrowing declared support

**Prior failure.** Canonical pixels were correct but the canonical branch did not record all four exact axes. A subsequent singleton integer recording pattern caused the static axis-span detector to overlook wider `draw_choice` support.

**New choice.** Record canonical dimensions as exact singleton choices and motif counts as exact strict integers. Contrastive dimensions remain selected from all valid capacity-preserving choices.

**Rationale.** Override evidence should bind pixels and provenance. The final form is honest to both the generated instance and the declared override domain.

## D9 — Retain the smallest practical shortcut reproducer

**Choice.** Keep seed 19, sample 1, easy as `counterexamples/horizontal-only.json`.

**Rationale.** It is an ordinary final-generator draw, passes the validator, contains true targets, and differs from the selected Racket rule at exactly one cell for the strongest canonical-fitting shortcut. Supported Racket evidence is under `checks/counterexamples/`.

**Coverage.** `test_horizontal_only_canonical_shortcut_has_a_generated_counterexample` regenerates the same episode and requires both the witness and output disagreement.

## D10 — Leave audit targets unchanged

The assigned audits were adversarial review only. `bc72c2d915c9` has a reproduced validator/domain-contract defect; `34f8510e39d0` had no issue in the bounded scan. Neither source was edited.

## Evidence and epistemic limits

No prior return was used as a lead. Intermediate failures were preserved rather than overwritten. All final quantitative claims in this handoff bind to generator SHA-256 `d060270b16f1515c9dedbaa944256700a5da3608ada0bb82bb7bd432e2301460`.

The declared-rival checks are finite. A zero count of survivors means the tested executable rivals were refuted under the sampled and enumerated policies; it is not a proof that no other program can fit the demonstrations.

## 2026-10-25 parametric admission candidate — select a qualifying color before filling

The canonical default remains exactly `fill_scope=all_qualifying`: every zero center
whose four cardinal neighbors share one nonzero color is filled by the accepted
program. The new branch `fill_scope=rarest_color_only` uses a genuine two-stage rule.
It finds all qualifying centers, counts them by arm color, selects the uniquely rarest
qualifying color, and then fills only centers carrying that selected color. A
protected-Racket wrong-intermediate witness substitutes the most common qualifying
color and changes the output, so the fill predicate consumes the first-stage result.

The minimum two-demonstration lesson was adversarially hardened after an early sampler
made “rarest” synonymous with “appears once” and sometimes leaked numeric or scan-order
shortcuts. The final first two demonstrations vary the minimum count (one, then two),
place the rarest color once below and once above competing color values, and keep it
away from first/last qualifying scan positions. The retained `rival_audit.py` checks
six named alternatives: singleton-only, lowest/highest numeric color, first/last
qualifying color, and most-common color. Across 256 consecutive seeds none survives
both demonstrations. This is finite rival evidence, not a universal uniqueness proof.

Final reviewer evidence is source-bound to the task-local inventory. Native
qualification covers both settings at seeds 0 and 17, with two demonstrations and
four distinct queries per job: 4 jobs and 32 protected-Racket evaluations. The
matched-input self-audit covers all supported demonstration counts 2–6 over three
seeds (30 episodes, 240 labeled pairs), preserves first-turn serialization, and
includes substantive 30×30 stress with up to 16 qualifying centers and 19 detected
decoys. The production `generator.py`, canonical authority, and shared runtime were
not modified. Exact-source owner acceptance and any training admission remain pending.
