# Current notes: `95705262dbee`

## Intended rule and authority

Extract each nonzero 4-connected monochromatic component, crop it to its tight bounding box, sort crops by increasing colored-cell count, and pack them top-aligned left-to-right with one all-zero column between crops. The selected canonical Racket rule is unchanged. Generator `2.0.1` pins normalized `RULE_HASH=7d39da4c591e`.

## Current production grammar

- canvas is one of `(10,12)`, `(11,13)`, `(10,14)`, `(12,12)`;
- exactly three isolated components use three distinct nonzero colors;
- sorted component sizes are `(3,4,5)`, `(3,5,8)`, or `(4,5,8)`;
- a 12-step schedule covers every grid-profile × size-profile combination;
- public exact controls are only `grid_h`, `grid_w`, and `size_profile`;
- packed output stays within the observed 4×10 envelope.

## Reversed decisions

The prior generator used smaller/under-scaled random sizes, omitted a rule hash, and declared palette/texture-style axes that were dead or degenerate. Its notes did not record a rationale. Those choices were replaced with a canonical-profile schedule and only observable exact axes because the before checks showed distribution drift, sparse/no per-band canonical support, and no semantic contract.

The first v2 draft left difficulty bands byte-identical. After a failing regression test and defect-lint reproduction, version `2.0.1` gives each band a distinct non-identity color-to-size counterbalance. This is not a claim that hard is cognitively harder than easy.

## Teaching decisions

Ordinary draws guarantee that row-major input order and numeric color order differ from increasing size order. Profiles with sizes 5 and 8 force cell-area order to disagree with bounding-box-area order. Declared rivals are descending area, input order, color order, and bbox area; executable witnesses and `lesson_identifiable` score complete three-demo lessons.

Final evidence:

- battery: 12/12 green (`checks/after/`);
- task tests: 35/35 (`checks/task-tests/`);
- random lesson census: 300 lessons, 1,200 pairs/rotations, zero declared-rival ambiguities (`checks/lesson-census.json`);
- fixed-seed schedule census: all 36 band/start lessons and 144 rotations unambiguous (`checks/lesson-census-schedule.json`).

## Known limits and open findings

The generator intentionally covers exactly three distinct-size components. Equal-area ties, more/fewer components, touching components, and same-color disconnected components are outside its production grammar. The finite rival set and finite seed censuses do not prove unique induction against all possible rules. The selected authority is synchronized; one archival historical source remains divergent but is not used for labels. No repair blocker remains.
## Current reviewer considerations

Source SHA-256: `f15b6fe8b10e5f03e76df4847aa470a29885c27fa43e5d18543f4b6e716e0c57`.

# Decisions for `95705262dbee`

## D1 — preserve the selected Racket authority

**Prior choice/rationale:** the baseline had a working selected rule; its historical rationale was not documented in the empty task notes.
**Decision:** do not alter the canonical Racket program. Pin its normalized hash as `RULE_HASH="7d39da4c591e"` and test the Python mirror against all five labeled canonical pairs.
**Alternatives considered:** rewrite the rule for style; extend tie behavior. Both were rejected because no authority defect was observed and tie semantics are not identified by the canonical data.
**Evidence/failure mode:** rule smoke, Racket lint, grammar, and selected authority sync pass. An archival rule copy is divergent, but execution parity for the selected authority passes. A future canonical rule change will now fail the hash pin.

## D2 — replace broad under-scaled randomness with a canonical-profile schedule

**Prior choice/rationale:** version 1.1.0 sampled smaller grids and component sizes, but the original notes did not explain why. It also exposed controls that did not reliably enter generation.
**Decision:** schedule the four observed canvas profiles and three observed size profiles with periods 4 and 3, giving all 12 combinations over `LESSON_SCHEDULE_PERIOD=12`.
**Why:** it guarantees every band supports canonical scale while retaining deterministic, source-bound diversity.
**Rejected alternative:** merely widen old random ranges. That could pass an envelope check while leaving sparse or zero exact canonical support and no guarantee per complete lesson.
**Limit:** the sampler intentionally does not teach equal-area ties, two/four-plus components, or profiles outside the canonical family.

## D3 — expose only observable exact axes

**Decision:** retain only `grid_h`, `grid_w`, and `size_profile` in `AXES`; all are consumed through `GenCtx`, independently observable, and exact-or-loud. Remove the old palette/texture-style declarations rather than simulate controls that do not change the rule-bearing structure.
**Alternatives:** add explicit palette or shape axes. Rejected as unnecessary API surface; color and shape diversity remain internal keyed draws.
**Probe:** final override stage passes with no findings; task tests verify all three size profiles at `12×14` in every band and reject unknown/type/range errors.

## D4 — use constructive non-touching placement

**Decision:** place one component in each of three separated zones (northwest, northeast, south), with horizontal jitter. This gives reliable isolation without retry-driven failure.
**Alternative:** unconstrained random placement with rejection. Rejected because tight canonical grids make retries fragile and can bias the realized shape distribution.
**Failure modes considered:** collision, orthogonal touching, changed row-major order, and gallery overflow. `self_check` and task tests cover each structural contract.

## D5 — counteract input-order and color-order shortcuts on every ordinary draw

**Decision:** use non-identity permutations for both component size rank versus row-major slot and size rank versus sorted numeric color.
**Reason:** random permutations can accidentally produce identity examples or whole lessons; guaranteed non-identity support is cheap here.
**Alternative:** rely on frequency across many lessons. Rejected because each individual three-demo lesson should teach the rule.
**Limit:** numeric colors remain literal and distinct; same-color disconnected components are outside this generator's domain.

## D6 — create an explicit cell-area versus bbox-area witness

**Decision:** whenever sizes 5 and 8 occur together, choose a 5-cell polyomino spanning a 3×3 box and an 8-cell 2×4 rectangle. The true cell areas order 5 before 8, while bbox areas order 8 before 9.
**Reason:** all canonical examples are compatible with the bbox-area shortcut, so generated counterexamples are necessary.
**Rejected alternative:** hope random polyominoes occasionally reverse bbox order. That provides no lesson guarantee.
**Evidence:** semantic gate verifies the canonical shortcut claim and generated witness; larger censuses report no surviving declared rival.

## D7 — treat difficulty as counterbalancing, not calibrated hardness

**Intermediate failure:** the first v2 draft produced byte-identical easy/medium/hard draws. A new test reproduced it, and defect lint flagged `dead-bands`.
**Decision:** assign each band a different guaranteed non-identity color-to-size permutation; leave semantic scope, canonical profiles, and exact overrides unchanged.
**Why:** it makes banded sampling observably distinct without inventing unsupported complexity tiers.
**Alternative:** force easy/medium/hard to different size profiles. Rejected because each band must cover every canonical profile.
**Limit:** no claim is made that hard is cognitively harder than easy.

## D8 — make lesson identifiability executable

**Decision:** declare four pure rivals, four witnesses, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS`, `EXAMPLES_NEEDED=3`, and `lesson_identifiable`.
**Reason:** pairwise label correctness is insufficient when a shortcut can fit all demonstrations and change the query.
**Testing policy:** task tests enumerate every cyclic start of the 12-step schedule at a representative seed; official census covers 100 random lessons per band and all query rotations; a second official census enumerates every start residue in every band at seed 0.
**Limit:** only declared rivals are scored, and fixed-seed schedule enumeration is not an all-seed proof.

## D9 — validate the rule-bearing domain rather than only grid syntax

**Decision:** `self_check` rejects unsupported size profiles, repeated component colors, touching components, bad dimensions/cells, wrong component count, and gallery overflow. `mutation_fixtures` retain named negative cases.
**Alternative:** accept any rectangular 0–9 grid because the Racket rule can execute it. Rejected because training admission needs a narrower, documented grammar.
**Limit:** valid canonical inputs are accepted even when their absolute layout differs from the constructive zones.

## D10 — independent Python mirror is test support only

**Decision:** include a straightforward component/crop/pack mirror for canonical assertions, rival scoring, and visible tooling. Racket remains the label authority.
**Risk:** a shared bug between mirror and generator could mask an error. Mitigation is exact comparison against all canonical labels plus the battery's Racket rule smoke and authority checks.

## D11 — no selected-task counterexample directory added

All reproduced selected-task defects were distribution/contract omissions fixed by the new implementation and retained failing check receipts. The portable regression suite is the minimal reproducer. Audit-only counterexamples belong under `checks/audit/<TASK_ID>/` and did not modify those generators.
