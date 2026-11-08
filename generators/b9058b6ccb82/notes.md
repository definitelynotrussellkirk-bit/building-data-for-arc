# Working notes: b9058b6ccb82

## Current rule and source identity

Version `4.1.0`; final generator SHA-256 `79df3b69bd681935603be34621a08a6766268825e5ca536ba1b446cc219f56ae`; pinned canonical `RULE_HASH = 7fc0dbf623b9`. The Racket authority was not changed.

A lawful input has background 0 and three or four distinct-colored, 4-connected objects separated by a one-cell Chebyshev halo. Exactly two free-polyomino (D4) classes occur with multiplicities `(n-1, 1)`. The answer is the singleton object's original normalized pose and color, cropped to its bounding box.

## Repair decisions

- Replaced retry-based random blobs with a finite audited 3/4/5-cell shape bank and deterministic 4×3 placement slots. This makes the semantic contract checkable and keeps every advertised exact override feasible throughout `grid_h=9..18`, `grid_w=10..20`, and `n_siblings=2..3` in every band.
- Strengthened `self_check` from per-color connectivity to the complete task domain: rectangular ARC colors, background 0, object count, one color per component, 4-connectivity, size, halo separation, and exactly one singleton D4 class.
- Added strict scalar/unknown-key rejection, `observe_overrides`, canonical profile hooks, a Python rule mirror, semantic rivals/witnesses, lesson identifiability, and negative mutation fixtures.
- Use a three-profile schedule: canonical-like 3-vs-4 cells; equal-size chiral F pentominoes; and a broader equal-size chiral class. Three demonstrations plus one query are the intended lesson assembly. Query position may rotate arbitrarily.
- Kept two canonical canvas/palette profiles as deterministic schedule slots, with a broader third profile by difficulty. Final profile floor: 42 exact hits in 60 draws, with support in all bands.

## Reversals and evidence

1. **Prior choice:** let each band draw only from a narrower internal axis range while advertising a larger global range. **New choice:** all advertised values work in all bands. **Reason:** the baseline override gate found 1,261 findings across 19,350 draws, including 1,230 generation errors, 13,200 rejected combinations, and silent unknown-key acceptance. Final gate accepted 16,020/16,020 draws with zero findings or warnings.
2. **Prior choice:** rely on random shapes and a connectivity-only validator. **New choice:** finite verified shape classes and full invariant validation. **Reason:** baseline defect lint accepted minimal impostors and rejected only 11/49 mutations; the final defect lint is green and task-local mutation fixtures are all rejected.
3. **Intermediate choice:** use F5 as the repeated chiral class in both equal-size schedule slots. **New choice:** retain F5 in one slot and sample a second chiral common class in the broad slot. **Reason:** the first repair was teachable but too morphologically narrow; the final 36-sample probe sees at least four common classes, six outlier classes, object sizes 3/4/5, and both same/different size relations.
4. **Intermediate choice:** make only one equal-size slot reflection-bearing. **New choice:** both equal-size slots contain a direct reflection witness. **Reason:** the semantic rotation diagnostic found 8 ambiguous held-out-query rotations out of 48 for source `133330d1...`; see `counterexamples/review-317c86a2741da44e/rotation_query_ambiguity_pre_4_1.json`. Final required-rotation smoke is 0/48 ambiguous, the task test exhausts 72 cyclic-start/query cases, and the large census is 0/1,200 ambiguous rotations.
5. **Intermediate declaration:** expose `LESSON_SCHEDULE_PERIOD`. **New choice:** retain `SCHEDULE_PROFILES` plus an exhaustive task-local cyclic-start regression, but omit the redundant period declaration. **Reason:** the current semantic CLI warns solely because it does not enumerate a declared period in ordinary battery mode; a separate required-rotation gate and task test provide the actual evidence. This tooling gap is reported as F2.

## Limits and open findings

- The finite rivals tested are `last_component`, `unique_cell_count`, and `rotation_only_equivalence`; their defeat does not prove identifiability against every conceivable hypothesis.
- The schedule uses a finite hand-audited shape bank and fixed slot topology. This deliberately trades unrestricted morphology/layout for reliable semantics and exact override support.
- `MIN_STRICT_FRAC=0.50`; the final semantic census measured 399/600 strict canonical-like draws (0.665), not universal canonical-profile sampling.
- No selected-task blocker remains. Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `79df3b69bd681935603be34621a08a6766268825e5ca536ba1b446cc219f56ae`.

# Decisions for b9058b6ccb82

Final generator SHA-256: `79df3b69bd681935603be34621a08a6766268825e5ca536ba1b446cc219f56ae`. Canonical rule hash: `7fc0dbf623b9` (unchanged).

## D1 — Repair the generator, not the Racket authority

**Original state/rationale:** the selected Racket rule solved all canonical pairs and the baseline rule smoke/authority checks passed. The defects were in generation, validation, controls, and teaching support.

**Decision:** leave canonical/Racket files untouched; pin the canonical hash in Python and add `rule_mirror` for diagnostics/tests.

**Rejected alternative:** alter the rule to fit generator artifacts. That would conceal a generator-domain defect and risk changing canonical semantics.

**Evidence/failure mode:** canonical pairs 3/3 are accepted and solved exactly; final rule smoke, Racket lint, and authority sync are green. A future authority mismatch will fail the hash pin and task tests.

## D2 — Use a finite audited free-polyomino bank

**Original state:** random connected blobs followed by retry/rejection. It gave diversity but made exact D4-class guarantees opaque, and `self_check` did not verify the central law.

**Decision:** use distinct 3-, 4-, and 5-cell free-polyomino classes with explicit D4 canonicalization. Generate one majority class and one singleton class directly, then validate the result.

**Rejected alternatives:**

- Keep random blobs and increase retries: still obscures support, weakens override feasibility, and makes reflection witnesses accidental.
- Hard-code only canonical shapes: strongest profile fidelity, but too little morphology and no robust same-size counterexamples.

**Probe:** `test_schedule_restores_shape_and_size_diversity` sees at least four common classes, six outlier classes, sizes 3/4/5, and both same/different-size relations in 36 medium samples.

**Known limit:** this is still a finite bank, not all free polyominoes.

## D3 — Fixed halo-separated slots with randomized pose/color/class

**Decision:** reserve 4×3 corner/bottom slots that remain valid at the minimum 9×10 canvas; randomize colors and legal D4 poses. Three objects use top-left, top-right, and bottom-center; four use the four corners.

**Rationale:** exact canvas overrides become feasible without packing retries, and the validator can guarantee a one-cell Chebyshev halo.

**Rejected alternative:** arbitrary rejection-sampled packing. It would make endpoint overrides expensive and introduce seed-dependent failures.

**Shortcut review:** the singleton is placed at a nonterminal reading-order rank, and a retained witness proves `last_component` differs from the rule. Fixed broad slot topology remains a documented distribution restriction.

## D4 — One public domain in every difficulty band

**Decision:** `grid_h=9..18`, `grid_w=10..20`, `n_siblings=2..3` are exact controls in every band. Difficulty changes only the broad-profile defaults, not override legality. Unknown axes and non-exact scalars reject.

**Rationale:** AXES should describe valid explicit controls, not merely a union of incompatible sampling priors.

**Rejected alternative:** declare a large incompatibility matrix. The geometry supports the full product, so incompatibilities would add complexity without benefit.

**Evidence:** baseline had 1,261 findings/19,350 draws and 13,200 rejected combinations; final override gate accepted 16,020/16,020 and rejected the unknown-key probe.

## D5 — Three demonstrations, cyclic schedule, arbitrary query position

**Decision:** `EXAMPLES_NEEDED=3`; four consecutive generated pairs form a lesson window. Schedule profiles cycle by sample index:

1. canonical-like L3 majority vs. four-cell singleton;
2. equal-size chiral F5 majority vs. pentomino singleton;
3. broader equal-size chiral majority vs. same-size singleton.

Both equal-size profiles contain mirrored majority poses. A query may be any of the four pairs.

**Rationale:** the demonstrations must refute cell-count, reading-order, and rotation-only rivals rather than merely label lawful inputs.

**Reversal:** an intermediate design made only profile 1 reflection-bearing. Holding it out left `rotation_only_equivalence` alive in 8/48 rotations. Profile 2 was made independently reflection-bearing; see the retained counterexample and regression.

**Rejected alternative:** ordered-only queries. That would be cheaper but fragile if downstream assembly changes pair order.

**Evidence:** 72/72 local cyclic-start/query cases, required smoke 48/48, and large census 1,200/1,200 rotations are identifiable against declared rivals.

## D6 — Canonical profile floor plus broader support

**Decision:** schedule profiles 0 and 1 exactly hit `(9,10,5)` and `(10,11,5)` by default; profile 2 broadens canvas/object count by band. `MIN_STRICT_FRAC=0.50` is explicit.

**Rationale:** deterministic floor support is more reliable than hoping random draws land on canonical dimensions/palettes, while the third slot avoids training only on canonical canvases.

**Evidence:** 42/60 exact profile hits and all bands nonzero; semantic census strict rate 399/600 = 0.665.

## D7 — Full validator, mutation fixtures, and source-bound hooks

**Decision:** `self_check` enforces grid type, ARC colors, background, object count, one 4-connected object per color, size, halo, and `(n-1,1)` D4 multiplicity. Add `observe_overrides`, `strict_canonical_like`, three executable rivals, three witnesses, `lesson_identifiable`, and eight mutation fixtures.

**Rationale:** a training generator must prove its input domain and pedagogy, not merely avoid exceptions.

**Failure modes covered:** all-background, one object, no singleton, no majority, disconnected same-color noise, halo touching, ragged grid, boolean cell, malformed public scalars, unknown controls, output pose/color loss.

## D8 — Do not declare `LESSON_SCHEDULE_PERIOD` under the current ordinary gate

**Prior choice:** declare the obvious period 3.

**Decision:** keep `SCHEDULE_PROFILES=(0,1,2)` and exhaustive task tests, but omit `LESSON_SCHEDULE_PERIOD`.

**Reason:** ordinary semantic-gate mode emitted a blocking/warning condition because it does not enumerate the declared period there, even though a separate rotation gate and task test did. This is a tooling-interface issue, not hidden schedule behavior; it is documented in F2.

**Risk if wrong:** future tooling may not automatically infer the period. The explicit schedule tuple, regression, and census commands remain reproducible.
