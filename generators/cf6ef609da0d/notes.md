# Current notes: cf6ef609da0d

## Intended rule

For each 4-connected color-6 component, inspect its occupied cells. Keep and recolor the whole component to color 2 exactly when at least one occupied cell lies on the main diagonal (`row == column`); erase every other component to 0. Bounding-box intersection is not sufficient, and no component is selected merely for being nearest to the diagonal.

## Current generator decision

Version `2.3.0` constructs 8..14 grids with exactly 2..5 separated components and component sizes 1..4. Exact `grid_h`, `grid_w`, `n_components`, and `scene_pattern` overrides are authoritative in every difficulty band. Defaults are band-shaped, with a deterministic 9×9/10×10 canonical-size anchor every fifth sample.

The five-slot lesson schedule is:

`mixed_bbox, none_on_diagonal, mixed_bbox, none_on_diagonal, mixed_bbox`

A lesson uses four demonstrations. `mixed_bbox` contains both a true occupied-cell touch and an off-diagonal bounding-box trap. `none_on_diagonal` contains a bounding-box trap but no true touch, so the lawful output is all zero. The two declared competitors are `bbox_diagonal` and `nearest_diagonal`.

## Reversed prior choices

- **Prior:** `n_components` was advertised but ignored; ordinary scenes sampled only two or three components. **Now:** exact 2..5, observable from the grid. Lead: `review-e2abefff557013a3:v0001`; verified by final override gate and tests.
- **Prior:** only 3- and 4-cell shapes were constructed. **Now:** connected sizes 1..4, matching canonical morphology. Verified by task-local coverage.
- **Prior:** ordinary support always contained a true diagonal touch and often omitted a bounding-box trap. **Now:** every lesson contains explicit positive, bbox-only, and no-touch evidence through the schedule. Lead: `review-6b823d984696fe37:v0001`; verified by the semantic gate and 300-lesson census.
- **Prior:** difficulty-local ranges rejected public axis endpoints. **Now:** full exact domain in every band, while defaults remain difficulty-shaped.

## Evidence and limits

Final generator SHA-256: `7269a42b137ca302a7f9081eb8017ae195ec6863afed2f855f2e1dd5c6f2814c`. The required-rotation battery is 12/12 green and task tests are 50/50. The 300-lesson source-bound census found 0 production or rotated ambiguities against the two declared rivals across 1,500 unique inputs.

Minimal retained witnesses are in `counterexamples/review-3400f37203458cb4/semantic-shortcuts.json`. These finite checks do not establish universal rule uniqueness. The canonical Racket authority was not changed, and this review does not itself admit the generator for training.
## Current reviewer considerations

Source SHA-256: `7269a42b137ca302a7f9081eb8017ae195ec6863afed2f855f2e1dd5c6f2814c`.

# Decisions: cf6ef609da0d

## D1 — Component count and morphology

**Prior choice:** the pinned source sampled two or three components and used only a small hand-written set of 3- and 4-cell shapes; the declared `n_components` control was not consumed. The original rationale is unknown. The source-matched audit `review-e2abefff557013a3:v0001` was used as the repair lead, not as a current-source measurement.

**New choice:** expose an exact `n_components=2..5` axis and construct connected polyominoes of sizes 1..4. Component sizes follow a deterministic cycle within each sample, while placement remains seeded and spatially varied.

**Alternatives rejected:** silently narrow the declared axis to the old 2..3 support; or retain only 3/4-cell objects and claim canonical coverage through labels alone. Both would preserve the construction gap rather than teach singleton/domino behavior.

**Probe and evidence:** exact override tests run every profile in every band; 32 medium defaults cover sizes `{1,2,3,4}`. Final `override`, `selfcheck`, and task-test receipts are green.

**Failure modes / limit:** the placement solver has a finite 200,000-node budget. The full advertised joint endpoints, all battery draws, and production census completed, but this is not an exhaustive proof over all integer seeds.

## D2 — Dimensions and difficulty

**Prior choice:** dimension overrides were checked against difficulty-local ranges, so declared endpoints such as 8 and 14 could fail on medium. Default difficulty did not reliably alter the observable distribution.

**New choice:** exact overrides use the full public 8..14 domain in every band. Defaults are band-shaped (`8..9`, `10..11`, `12..14`) but every fifth sample is a deterministic 9×9 or 10×10 canonical-size anchor in all bands.

**Alternatives rejected:** make the public axis difficulty-conditional; or use only 9×9/10×10 grids. The first makes advertised exact controls misleading, while the second removes useful scale variation.

**Probe and evidence:** endpoint tests include an 8×14, five-component scene in every band/profile. The pinned 20-draw profile-floor gate passes easy, medium, and hard.

**Failure modes / limit:** canonical-size anchoring is deterministic by sample residue. This is useful for coverage but should not be interpreted as an estimate of a natural task distribution.

## D3 — Semantic scene profiles

**Prior choice:** ordinary support always included at least one component touching the main diagonal. A no-touch texture existed only outside ordinary support, and ordinary demonstrations often lacked a bounding-box-only component. The prior return `review-6b823d984696fe37:v0001` supplied the two concrete shortcut leads.

**New choice:** define two observable profiles:

- `mixed_bbox`: at least one true occupied-cell diagonal touch plus an off-diagonal component whose bounding box intersects the diagonal.
- `none_on_diagonal`: no component touches the diagonal, but a bounding-box trap remains.

**Alternatives rejected:** random rejection sampling until a witness happens to appear; or adding only a bounding-box trap. Rejection sampling makes lesson support opaque, and a bounding-box witness alone does not teach the exact-zero requirement against the nearest-component rival.

**Probe and evidence:** minimal source-bound counterexamples are saved under the selected generator and exercised by the 49th task test. The final semantic gate and 300-lesson census show both named rivals are refuted.

**Failure modes / limit:** only `bbox_diagonal` and `nearest_diagonal` are declared. Other hypotheses remain untested and must not be described as disproved.

## D4 — Lesson assembly

**Prior choice:** the old generator relied on ordinary stochastic draws and the default three-demonstration floor. A plausible rival could fit every demonstration and disagree on the query.

**New choice:** set `EXAMPLES_NEEDED=4` and use the five-slot schedule `(mixed, none, mixed, none, mixed)`. Any four demonstrations from a five-pair window contain both positive and negative branches, and every query rotation is required to be identifiable against both named rivals.

**Alternatives rejected:** three demonstrations with opportunistic resampling, or an even 2:2 repeating schedule. The former makes failure frequency-dependent; the latter caused the all-zero branch to occupy half the exported stream and tripped the strict distribution heuristic.

**Probe and evidence:** task tests enumerate all cyclic starts × all held-out positions. The Racket census materialized 300 lessons (100 per band), 1,500 pairs and 1,500 rotations with 0 ambiguities or errors.

**Failure modes / limit:** four demonstrations cost more tokens than three. The finite declared-rival pass is not a uniqueness proof over arbitrary programs.

## D5 — Validation and observability

**Prior choice:** `self_check` accepted empty, all-zero, ragged, oversized, and otherwise non-task inputs; axis values were not all recoverable from returned grids.

**New choice:** reject empty/ragged grids, non-literal colors, dimensions outside 8..14, component counts outside 2..5, and component sizes outside 1..4. `observe_overrides` recovers all four advertised controls from a valid grid.

**Alternatives rejected:** keep `self_check` structural-only and add a separate hidden validator. A single explicit contract is easier for the generator battery and future reviewers to reproduce.

**Probe and evidence:** malformed-grid parametrizations and exact-axis round trips are in `tests/test_generator.py`; final strict fraction is 1.0.

**Failure modes / limit:** the validator intentionally accepts any grid in the declared grammar, not only one of the two scheduled teaching profiles. Semantic profile enforcement belongs to generation and lesson checks, not generic canonical-input acceptance.

## D6 — Authority

**Choice:** leave the Racket rule and canonical row unchanged. The defect was in input support, axis contracts, and curriculum composition, not label authority.

**Evidence:** final rule smoke, authority sync, and execution parity are green; the selected canonical `RULE_HASH` is pinned as `5deda141503d`. Authority sync reports one archival bank copy as divergent, while the selected authority is synchronized; no archival file was edited.
