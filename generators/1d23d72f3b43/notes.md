# Working notes: 1d23d72f3b43

## Current rule and authority

For every nonzero color appearing exactly twice, treat the two cells as opposite diagonal corners and fill that color's inclusive axis-aligned bounding rectangle. The selected Racket authority was not changed; `RULE_HASH = 013675ae7255`, and canonical, selected, and archival sources are exact-synchronized.

## Review review-22a490cfba52a80a

Prior return `review-f5516c8562917503:v0001` (ZIP SHA-256 `be626451754711944d45fbb37a3ac94a504ec2168a8074393e0f922cc2bd587f`) was used only as a lead. Its probes correctly identified ignored controls and an out-of-range dimension claim against baseline generator SHA-256 `8f5c0b406bafce1b0d8b9f6f9644320d3bcd71caa51190ea52463b731ec0261d`.

The baseline v2.1.1 had no pinned rule hash; advertised controls that were ignored, overlapping, or contradictory; accepted unknown override keys; generated only rectangles at least 3×3; did not deliberately include both diagonal orientations; and had a self-check that admitted collinear pairs and overlapping boxes. The baseline battery was interrupted after recording lint and defect-lint failures; that incomplete result is retained under `checks/before/`.

Version 3.1.0 now:

- advertises only exact observable axes: `grid_h` 8..12, `grid_w` 8..12, and `n_pairs` 2..4;
- rejects unknown, non-integer, and out-of-range overrides;
- samples 2–4 disjoint rectangles in independently shuffled slots, including horizontal and vertical two-cell-thick cases;
- places at least one main-diagonal and one anti-diagonal pair in every ordinary draw;
- validates rectangular ARC grids, dimensions, pair counts, diagonal separation, and non-overlapping inclusive boxes;
- exposes `strict_canonical_like`, exact override observation, an anti-diagonal witness, the canonical-fitting `main_diagonal_only` rival, and a lesson-identifiability hook;
- keeps each difficulty band anchored to at least one exact canonical profile in the pinned 20-draw profile census. The hard band still favors larger canvases and denser pair counts, but no longer abandons the canonical two-pair scale.

A minimal Racket-labelled counterexample is retained at `counterexamples/main_diagonal_only.json`. The rival fits all five canonical pairs but differs from the intended rule on seven cells of the anti-diagonal rectangle.

## Known limits

The generator intentionally restricts lessons to 8–12 by 8–12 grids, 2–4 colors, exactly two cells per color, and non-overlapping rectangles. It does not test overlapping or same-row/same-column pairs because those are outside the documented task domain. The semantic evidence is finite and checks the declared `main_diagonal_only` rival; it is not a proof against every imaginable induction rule.
## Current reviewer considerations

Source SHA-256: `36a6069b7fa9fc4438410b6321dbe760ef493008780c86328ad4fca686d2461b`.

# Decisions for 1d23d72f3b43

Final generator SHA-256: `36a6069b7fa9fc4438410b6321dbe760ef493008780c86328ad4fca686d2461b`. The selected Racket authority was unchanged (`013675ae7255`). The original task notes contained no rationale, so baseline intentions not inferable from source are marked unknown.

## D1 — Retire dishonest controls instead of preserving compatibility

**Prior choice:** v2.1.1 advertised `palette_kind`, `palette_size`, `n_distinct_colors`, `position_bias`, `density`, and overlapping `texture` values, but several did not affect output; unknown keys were accepted. Original rationale: unknown.

**New choice:** expose only `grid_h`, `grid_w`, and `n_pairs`, each observable from the returned grid and exact across all bands. Unknown or mistyped keys fail loudly.

**Alternatives rejected:** keeping aliases for obsolete controls would preserve an unfalsifiable contract; mapping `palette_size` and `n_distinct_colors` to one hidden axis would retain contradictory names. The final override checker exercised 71 cases × 30 seeds × 3 bands = 6,390 accepted draws with zero findings.

**Limit:** callers using retired undocumented controls must update rather than receiving silently ignored behavior.

## D2 — Use disjoint randomized slots for rectangle placement

**Prior choice:** rectangles were placed through a narrower layout with weak validation. Original rationale: unknown.

**New choice:** split the canvas into four independently shuffled slots, each at least 3×3, and place up to four rectangles inside distinct slots. This makes non-overlap constructive and preserves positional diversity.

**Alternatives rejected:** rejection-sampling arbitrary rectangles was simpler but could become slow or biased near four objects; fixed quadrants without random splits would create a stronger location shortcut.

**Failure modes checked:** 160 focused draws verified two diagonal corners per color and pairwise-disjoint inclusive boxes. The final diversity gate measured 300/300 unique inputs and 300/300 unique outputs across 21 shapes.

## D3 — Include skinny and solid rectangles

**Prior choice:** both rectangle dimensions were at least 3, although lawful canonical-style rectangles can be two cells thick.

**New choice:** every lesson includes a mix of a solid rectangle and horizontal/vertical two-cell-thick rectangles; four-pair cases can add a general 2+ by 2+ rectangle.

**Alternatives rejected:** all-solid rectangles invite “remove/fill only deep interiors” shape shortcuts; all-skinny rectangles under-teach larger fills.

**Limit:** one-cell-wide/one-cell-high pairs are excluded because the documented domain requires diagonal, not collinear, corners.

## D4 — Counterbalance diagonal orientation in every ordinary draw

**Prior choice:** the canonical examples and baseline generator did not establish anti-diagonal support. All five canonical pairs are compatible with the `main_diagonal_only` rival.

**New choice:** every ordinary 2–4-pair input contains both main and anti orientations. The generator declares the rival, a witness, and a lesson hook. A Racket-bound minimal counterexample is retained under the task's `counterexamples/` directory.

**Alternatives rejected:** relying on random orientation independently could still yield complete lessons with no anti-diagonal witness; a deterministic alternation tied to sample index would create a schedule shortcut. The current per-draw constraint is local and seed-independent.

**Evidence:** semantic gate: 600/600 witness hits, 12/12 three-demo lessons identifiable, 0/48 ambiguous diagnostic rotations. Larger census: 300/300 lessons, 0/1,200 ambiguous production pairs, 0/1,200 ambiguous rotations.

## D5 — Strengthen `self_check` to match the documented domain

**Prior choice:** count checks allowed collinear same-row/same-column pairs and overlapping bounding boxes.

**New choice:** validate rectangular integer ARC grids, 8..12 dimensions, 2..4 nonzero colors, exactly two cells per color, non-collinearity, and non-overlapping inclusive boxes.

**Alternatives rejected:** merely validating generated outputs would not protect authored counterexamples or downstream mutations. Requiring a specific orientation mix in `self_check` was rejected because canonical inputs are lawful even though they contain only main-diagonal pairs.

**Limit:** `self_check` is a domain validator, not a proof that every accepted input is pedagogically sufficient; `lesson_identifiable` handles the teaching condition separately.

## D6 — Preserve canonical scale in every difficulty band

**Intermediate failure:** the first v3.0.0 repair favored sizes 11–12 and 3–4 pairs in hard mode. The strict profile floor found 0 exact canonical-profile hits in 20 hard draws, despite easy/medium support.

**New choice:** hard mode favors sizes 9–12 and pair counts 2–4. It remains larger/denser on average than medium, while preserving the canonical two-pair scale. A pinned-census regression test was written before the change.

**Evidence:** final exact canonical-profile hits are easy 6/20, medium 2/20, hard 2/20; 5/5 canonical inputs are accepted. The failed intermediate report is retained at `checks/stage-profile_floor/` and the passing final report at `checks/after/checks/1d23d72f3b43_after_profile_floor.json`.

## D7 — Do not change the Racket authority

The selected rule already matches all 4 training and 1 test canonical pairs. Authority sync reports one exact source group across canonical, selected, and archival copies, with execution parity passing. The repair therefore changes only generation, validation, tests, notes, and counterexample evidence.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-437a5710898452e9:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `36a6069b7fa9fc4438410b6321dbe760ef493008780c86328ad4fca686d2461b`. At disposition, audited bytes match the current source.

### Current decision

Reported33tests and strict semantic gate pass; inspected main_diagonal_only witness and both-orientation ordinary domain. Finite assessment of exact36a606source only. Explicit finite reviewer-reported assessment of these exact audited bytes; no blanket correctness or closure of other findings.

### Assessment or prior finding

## 1d23d72f3b43

**No issue found.** Audited generator SHA-256: `36a6069b7fa9fc4438410b6321dbe760ef493008780c86328ad4fca686d2461b`.

I checked the existing task-local suite and strict semantic contract with the combined audit preset. All **33 tests passed**, and the semantic gate passed: `checks/audit/1d23d72f3b43-combined/`. I also inspected the retained `main_diagonal_only` shortcut counterexample and the current design: every ordinary draw deliberately contains both diagonal orientations, boxes are disjoint, exact controls are limited to observable dimensions/pair count, and the notes state the finite domain limits. I found no concrete new counterexample or undeclared shortcut beyond those already addressed.

No files for this audit target were changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
