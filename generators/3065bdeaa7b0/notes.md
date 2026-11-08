# Working notes: 3065bdeaa7b0

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## October 2, 2026 review intake

Integrated `review-100d2bc82ed31673` v1: exact dimensions, pair/decoy controls,
constructive overlap-safe placement, strict literal ARC cells, and a four-profile
teaching schedule. The source-bound workspace probe uses actual selected Racket
labels and independently defined rivals. Maintainer replay: all 12 battery stages
green, 53 focused tests passed, 300 three-demo/one-query lessons produced 1,200
pairs (1,072 unique inputs), zero surviving declared rivals or oracle mismatches.

The selected Racket rule remains `1bc66fae4078`. Generator SHA-256:
`164f907b2d6fc73face87f4691a8a09fde3ecdd1d912bfa9c272470891524c15`.
The retained solve passed both private queries but disclosed prior rule exposure;
it is reviewer-authored, not a blind model trajectory or training admission.

Limits: placement uses a finite endpoint-template family; singleton/four-or-more
decoys and paths overwriting foreign markers are outside the generated domain.
Refuting four rivals on 300 lessons does not establish universal identifiability.
Full provenance and feedback dispositions: `REVIEW/intake-20261002-batch25c.json`.
## Current reviewer considerations

Source SHA-256: `164f907b2d6fc73face87f4691a8a09fde3ecdd1d912bfa9c272470891524c15`.

# Distribution and implementation decisions

## D1 — Keep the canonical Racket authority unchanged

- **Original rationale:** Unknown; the baseline rule already passed smoke and authority-sync checks.
- **Decision:** Pin `RULE_HASH = "1bc66fae4078"` and change only the Python sampler, tests, and workspace tools.
- **Alternatives rejected:** Rewriting the Racket rule, or narrowing the rule to match the baseline sampler.
- **Probe:** Final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green; the independent Python oracle matched Racket on every one of 1,200 census pairs.
- **Failure mode / limit:** Python parity is still a transcription; the canonical Racket program remains authoritative.

## D2 — Replace broad decorative metadata with four observable controls

- **Original rationale:** Inferred from baseline code; `palette_kind`, `position_bias`, `density`, and texture names appeared intended to increase variety, but several never changed bytes.
- **Decision:** Advertise only `grid_h`, `grid_w`, `n_pairs`, and `n_decoys`, each recoverable from a returned grid.
- **Alternatives rejected:** Keeping dead singleton enums as “diagnostic” controls, or preserving invalid negative fixtures in the ordinary texture domain.
- **Probe:** `observe_overrides` is checked against independent counts in task-local tests; the final override gate accepted all 25,380 draws.
- **Failure mode / limit:** Color identities and horizontal reflection remain latent stochastic variation rather than user-selectable axes.

## D3 — Use exact pairs plus triple-occurrence decoys

- **Original rationale:** The selected rule qualifies colors by occurrence count exactly equal to two. Canonical inputs contain no non-pair colors, leaving an obvious “first two occurrences” shortcut.
- **Decision:** Normal lawful inputs contain 1–4 colors occurring exactly twice and 0–2 colors occurring exactly three times.
- **Alternatives rejected:** Singletons as decoys, because they would not distinguish “at least two” from “exactly two”; four-occurrence decoys, because triples are the smallest direct counterexample.
- **Probe:** `first_two_occurrences_of_every_color` fits all five canonical pairs but disagrees with generated rich profiles. The 300-lesson census refuted it in every lesson.
- **Failure mode / limit:** Only count three is sampled as the non-pair case; behavior for counts 1 or 4+ is not directly taught.

## D4 — Use a four-position curriculum rather than independent profile draws

- **Original rationale:** Independently sampling witnesses can produce complete lessons that omit a necessary distinction even when pooled witness frequency is high.
- **Decision:** Repeat `canonical_anchor → pair_count → one_pair_decoy → combined`; consume three consecutive demonstrations.
- **Alternatives rejected:** Purely random profile selection and a two-position alternation. Neither guarantees all cyclic three-demo windows contain both shortcut counterexamples.
- **Probe:** Tests enumerate all four cyclic starts in every difficulty band. The source-bound census uses stride 11, giving exactly 25 lessons at each start residue per band; all 300 lessons refuted all four declared rivals in their demonstrations.
- **Failure mode / limit:** This guarantee assumes the repository continues assembling lessons from consecutive sample indices and three demonstrations.

## D5 — Preserve canonical scale while expanding difficulty bands

- **Original rationale:** Baseline canonical-profile support was only 1/60 and zero in easy.
- **Decision:** Half of scheduled positions use canonical dimensions; rich positions use difficulty-aware dimensions in 9..18. Explicit dimension overrides always use the full 9..18 domain.
- **Alternatives rejected:** Canonical dimensions on every draw (too narrow) and the baseline declared 5..24 domain (unsupported and unnecessary for the fixed constructive geometry).
- **Probe:** Final profile floor is 29/60. The extended census contains 100 strict canonical anchors per band and observes rich-profile dimensions up to 12 easy, 15 medium, and 18 hard.
- **Failure mode / limit:** Canonical-anchor dimension choice itself is not difficulty-skewed; the band distinction lives in rich profiles.

## D6 — Use constructive pair templates, reflection, and color permutation

- **Original rationale:** Rejection sampling made it harder to prove every override combination constructive and to guarantee path-overlap / reverse-endpoint witnesses.
- **Decision:** Use four dimension-parametric endpoint templates valid for every 9..18 grid, then optionally reflect horizontally and permute colors.
- **Alternatives rejected:** Arbitrary random endpoints with retries, and completely fixed unreflected examples.
- **Probe:** Every tested override combination passes `self_check`; the final grammar, diversity, and override gates are green. `top_right_first` and `path_overlap` fire in all bands.
- **Failure mode / limit:** Geometry is structurally diverse but still generated from one template family; a learner could exploit template-specific coordinates if trained on enough samples without additional augmentation.

## D7 — Keep decoy markers outside qualifying paths

- **Original rationale:** A qualifying path may overwrite any cell under the true rule, but letting a path cross a triple marker makes visual attribution unnecessarily ambiguous.
- **Decision:** Place triple-occurrence colors on the top or bottom row only at cells outside every pair path.
- **Alternatives rejected:** Allowing arbitrary overlap with decoys, or moving decoys after labels are produced.
- **Probe:** `self_check` verifies no pair path passes through a foreign marker. Racket parity remained exact.
- **Failure mode / limit:** The distribution does not teach what happens when a path overwrites a non-pair marker, even though the selected rule is total there.

## D8 — Make the validator structural and non-throwing

- **Original rationale:** The baseline validator accepted/rejected inconsistently around declared textures and did not strongly bind the intended family.
- **Decision:** Validate rectangularity, ARC color types, dimensions, exact occurrence counts, pair offsets, and foreign-marker path exclusion; malformed values return diagnostics rather than raising.
- **Alternatives rejected:** Validator logic tied to generation metadata or exact template coordinates.
- **Probe:** Mutation tests cover removed endpoints, fourth decoy occurrences, same-row pairs, and foreign markers on paths; malformed-grid tests cover empty, ragged, and boolean-cell cases.
- **Failure mode / limit:** The validator intentionally accepts lawful endpoint arrangements not emitted by the constructive sampler.

## D9 — Declare executable rivals and witnesses

- **Original rationale:** The baseline semantic gate had no contract.
- **Decision:** Declare four rivals and four corresponding witnesses, plus a lesson-level check.
- **Alternatives rejected:** Text-only descriptions of possible shortcuts and pooled witness-rate claims without whole-lesson testing.
- **Probe:** Final semantic gate verifies all 4/4 rival claims and 12/12 smoke lessons. `repo/generators/3065bdeaa7b0/workspace/lesson_probe.py` dynamically reads the declarations and checks 300 full lessons with canonical Racket labels.
- **Failure mode / limit:** Named rivals are not exhaustive. Novel shortcuts remain possible.

## D10 — Build independent, source-bound review tools

- **Original rationale:** Generator-internal helper reuse could make tests reproduce the same bug, and the required 100-lessons-per-band evidence needed exact source provenance.
- **Decision:** `repo/generators/3065bdeaa7b0/workspace/reference_probe.py` independently implements the oracle/rivals; `repo/generators/3065bdeaa7b0/workspace/lesson_probe.py` stages the final source and uses the actual runner and Racket bridge.
- **Alternatives rejected:** Calling private functions from `generator.py` in tests, or labeling large samples with only the Python transcription.
- **Probe:** The lesson report records generator, probe, runtime-manifest, and rule hashes; all 1,200 Python-oracle outputs equal Racket outputs.
- **Failure mode / limit:** The source-bound probe uses repository runner helpers with leading underscores because no public batch lesson API is exposed; see feedback F3.

## D11 — Fresh solve policy

- **Original rationale:** Required by the assignment after generator freeze.
- **Decision:** Prepare on final generator SHA, read only `solve/challenge.json`, implement one visible-example solution, and declare earlier exposure honestly.
- **Alternatives rejected:** Pretending the solve was blind, reopening the generator/reference during solving, or manufacturing a failed teaching-negative attempt.
- **Probe:** Revision 1 passed 3/3 visible examples and was frozen with `earlier-exposure=yes`, `reference-consulted=no`.
- **Failure mode / limit:** Masked query correctness is unavailable to the reviewer and remains `unknown`.
