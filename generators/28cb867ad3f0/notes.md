# Current account: 28cb867ad3f0

## Intended rule

For each 4-connected color-0 chamber, count cardinal adjacencies to colors 1..4 **with incidence multiplicity**. Fill the entire chamber only when one color has a unique plurality. Tied or marker-free chambers stay 0. Color 5 and every marker cell are preserved. The selected canonical Racket authority remains unchanged at rule hash `56654a66f781`.

## Review leads and confirmed defects

This review used two prior audit returns only as leads: `review-89f5b99eb7c514ec:v0001` (the hook omitted already-declared rivals) and `review-a3075f0dc5c94ce5:v0001` (query rotation could remove the sole nonrectangular witness). Both were bound to the older selected source and were independently replayed against this packet's baseline.

The baseline `3.0.0` curriculum had four related defects:

1. `LESSON_COMPETITORS` checked only two of five named partial rivals.
2. Consecutive four-pair lessons had query rotations where shared-marker, tie, or nonrectangular shortcuts survived all three demonstrations.
3. Five partial rivals were incorrectly advertised as canonical-fitting shortcuts even though they failed canonical pairs.
4. `seed` and `sample_index` accepted non-literal scalar values; negative sample indices were also accepted.

A stronger previously undeclared shortcut was found: count each **distinct adjacent marker cell once** rather than each marker-to-zero incidence. It fits all five usable canonical pairs exactly.

## Decisions in version 3.1.0

- Declare all six executable rivals in `SEMANTIC_RIVALS` and check all six through `LESSON_COMPETITORS`.
- Declare only `distinct_cardinal_marker_cells` in `CANONICAL_SHORTCUTS`, because it alone fits all five canonical pairs.
- Add the named `boundary_incidence_multiplicity` witness.
- Add a compact `full_contrast` scene that separates every declared rival in one lawful input.
- Alternate `full_contrast` at every even sample index with the previous nine public/controlled profiles at odd indices. The declared schedule period is 18. Every consecutive four-pair lesson therefore has two full-contrast pairs, so any one query holdout leaves at least one full-contrast demonstration.
- Reject non-literal `seed`/`sample_index` values and negative sample indices before constructing `gen_ctx`.

The repair does not modify the canonical Racket rule or its hash.

## Final evidence

- Generator SHA-256: `402c0cb6bc5f73f1cbd70a739f4792dd4e1f398c27e239b383a7a9cfc4977324`.
- Focused portable regressions: 15/15 pass in `checks/final-task-tests/`.
- Fixed-seed cyclic schedule census: 54/54 lessons and 216/216 query rotations materialized across easy/medium/hard; 0 ambiguous, 0 hook warnings, 40 unique inputs. See `checks/final-schedule-s0.summary.json`.
- Source-bound shortcut probe: the distinct-marker shortcut matches 5/5 canonical pairs and disagrees on 18/36 generated draws per band over sample indices 0..35. See `checks/final-shortcut-probe.json`.
- Exact selected-Racket counterexample: `counterexamples/review-0593b7fc4490852a/distinct-cardinal-marker-cells/`.
- The fresh exposed solve is frozen to the same generator SHA and passed 3/3 visible examples in one revision.

## Known limits

The 18-residue proof is exhaustive only for seed 0 and the declared six rivals. It does not prove identifiability against every conceivable program or every random seed. Public anchor families and the deterministic full-contrast family have finite transformed/recolored support, so repeated inputs are expected. The repair intentionally spends half of ordinary samples on a composite witness; this favors robust three-demo teaching over maximum marginal diversity.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-a3075f0dc5c94ce5:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `ab2420691e1a7784bc1ad766e1c77eb313dbfe60176f235c388604e0736b4432`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Full named-rival hook and scheduled fullcontrast repair; original rotation seed88555953889319 directly present in test;15tests plus54seed0lessons/216holdouts reviewerreported. Originalseed123 recipe not separatelyreplayed. Exact-source repair accepted with reviewer-reported evidence. Finite declared-rival/regression evidence; root must explicitly dispose source-bound audit.

### Assessment or prior finding

## 28cb867ad3f0

**Finding A2 — arbitrary query rotation can remove the only nonrectangular
witness.**  Generator SHA-256
`ab2420691e1a7784bc1ad766e1c77eb313dbfe60176f235c388604e0736b4432`;
canonical rule hash `56654a66f781`.

The required-rotation semantic gate materialized the easy lesson replay
`seed=88555953889319 sample_index=0`.  When pair 0 is the query and pairs 1, 2,
and 3 are demonstrations, the declared `rectangles_only` rival matches all three
demonstration outputs but differs from the canonical query at 31 cells.  The
source-bound lesson and exact canonical/rival outputs are in
`checks/audit/28cb867ad3f0/rectangles-rotation/counterexample.json`; the supported
Racket receipt is
`checks/audit/28cb867ad3f0/rectangles-rotation/racket.json`.

Across the semantic smoke sample, **14/48** rotations were ambiguous.  The report
also found **5/12** lessons that the custom `lesson_identifiable` hook called
identifiable even though an auto-scored declared shortcut still survived the
demonstrations.  Lint, defect lint, and the override contract passed, so this is a
teaching-schedule/contract mismatch rather than a basic input-validity problem.
The complete source-bound semantic report is
`checks/audit/28cb867ad3f0/semantic-final/checks/28cb867ad3f0_before_semantic_gate.json`.

**Suggested repair direction, not applied:** either make lessons explicitly
ordered and document that rotations are unsupported, or ensure every three-demo
subset contains nonrectangular, shared-marker, and tie witnesses; also make
`lesson_identifiable` score the full `CANONICAL_SHORTCUTS` set so it cannot disagree
with the gate.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-a3075f0dc5c94ce5-v0001/audit_assets.json), manifest SHA-256 `bcdfec4501ec7bbb0ac88261d96adf71eae4acb2e37560be3b2cb74fe8f9e50c`.

This same current bounded resolution also covers prior report `review-89f5b99eb7c514ec:v0001`, audited source `ab2420691e1a7784bc1ad766e1c77eb313dbfe60176f235c388604e0736b4432`. Its reported finding is retained here with the current decision:

## 28cb867ad3f0

**Issue found: the advertised three-demo lesson is not identifiable against one of the generator's own named rivals, and the semantic hook omits that rival.**

Reproducer: seed `123`, difficulty `easy`, demonstration sample indices `0,1,2`, query index `3`. The profiles are `public_1`, `public_2`, `public_3`, then `public_4`. `SEMANTIC_RIVALS["ignore_shared_markers"]` exactly matches all three demonstration outputs but differs from the canonical query output in 32 cells. `lesson_identifiable(demos, query)` nevertheless returns `[]` because `LESSON_COMPETITORS` contains only `unique_presence_only` and `global_plurality`.

This is not merely an undeclared hypothesis: the module already names the rival and claims `EXAMPLES_NEEDED = 3` with `MIN_STRICT_FRAC = 1.0`. A learner can therefore receive a nominally complete lesson that does not determine whether shared boundary markers count. The smallest repair would either include every semantic rival in `LESSON_COMPETITORS` and redesign the three-slot windows, or increase/reorder the schedule so every declared lesson kills `ignore_shared_markers`, `tie_break_smallest`, and `rectangles_only` as well. Exact evidence is in `checks/shortcut_probes.json` under this task ID.

<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `402c0cb6bc5f73f1cbd70a739f4792dd4e1f398c27e239b383a7a9cfc4977324`.

# Decisions for 28cb867ad3f0

## D1 — Treat incidence multiplicity as an explicit teaching obligation

**Original choice.** The baseline described incidence multiplicity in prose but did not declare a canonical-fitting rival that deduplicates marker cells.

**Probe.** I implemented the rival “one vote per distinct adjacent marker cell.” It matches all 5 canonical pairs and disagrees with the selected rule on the generated `full_contrast` sample at seed 0/index 0.

**Decision.** Add `distinct_cardinal_marker_cells` to `SEMANTIC_RIVALS`, make it the sole `CANONICAL_SHORTCUTS` entry, and add a named `boundary_incidence_multiplicity` witness.

**Rejected alternatives.** Calling all partial heuristics canonical shortcuts was rejected because five fail labeled canonical pairs. Omitting the new rival was rejected because it is strictly stronger evidence-wise: unlike the old partial rivals, it really does fit every canonical pair.

**Limit.** This is one plausible program class, not an exhaustive synthesis of all canonical-fitting rules.

## D2 — Use one composite witness rather than many fragile single-purpose slots

**Original choice.** The nine-profile cycle distributed tie, shared-marker, nonrectangular, local/global, and plurality evidence across separate samples.

**Failure mode.** A query rotation could remove the only demonstration that refuted a particular rival. The old hook also checked only two named rivals, masking some of those failures.

**Alternatives considered.** Increasing `EXAMPLES_NEEDED`; supporting only an ordered query position; rejection-sampling each assembled lesson; or designing a single profile that separates all named rivals.

**Decision.** Keep three demonstrations and arbitrary single-query rotation support. Add a compact `full_contrast` scene that refutes all six declared rivals in one lawful grid. This avoids coupling lesson assembly to a rejection loop and preserves the existing public/general profiles.

**Limit.** The composite scene is larger and more information-dense than ordinary examples. It is intentionally overrepresented for teaching reliability.

## D3 — Alternate full contrast with the prior curriculum

**Original choice.** The baseline cycled nine public/controlled profiles directly.

**Decision.** Even sample indices are `full_contrast`; odd indices cycle the previous nine profiles with the existing difficulty offsets. This creates an 18-step period. Any four consecutive pairs contain two full-contrast inputs, so any one query holdout leaves at least one in the demos.

**Evidence.** The final fixed-seed census enumerated all 18 starts in each of three bands: 54/54 lessons, 216/216 query rotations, 0 ambiguous, 0 hook warnings, 40 unique inputs.

**Rejected alternative.** Putting one contrast every four positions was rejected because some cyclic windows and query positions could still remove the only contrast.

**Limits.** The exhaustive result is for seed 0, the declared period, and six declared rivals. Half of marginal samples now come from a finite transformed/recolored family.

## D4 — Make the semantic hook and declarations agree

**Original choice.** `LESSON_COMPETITORS` contained only `unique_presence_only` and `global_plurality`, while five rivals existed elsewhere.

**Decision.** Set `LESSON_COMPETITORS` from all six `SEMANTIC_RIVALS`; retain a focused test that fails if they diverge. `CANONICAL_SHORTCUTS` now contains only rules verified to fit all canonical pairs.

**Reason.** A hook that checks fewer rivals than the gate can return a false “identifiable” verdict. One declaration should drive both task-local and shared checks.

## D5 — Reject invalid scalar calls at the public boundary

**Original choice.** Booleans, floats, strings, and negative `sample_index` values reached `gen_ctx` and were accepted.

**Decision.** Require literal integers for `seed` and `sample_index`, and require a nonnegative sample index before generator construction. The same validation is used by `schedule_profile`.

**Alternative.** Coercion was rejected because values such as `True` and `1.0` silently alias valid seeds/indices and weaken reproducibility.

## D6 — Leave the Racket authority unchanged

The canonical rule already implements the intended incidence plurality, tie, and preservation behavior. All defects were in the Python generator contract and curriculum. No Racket source or rule hash changed; `RULE_HASH` remains `56654a66f781`.
