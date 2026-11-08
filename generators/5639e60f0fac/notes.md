# Current decisions — 5639e60f0fac

## Intended rule and authority

A green3 object's tight binary crop is transferred without transformation to a same-size solid cyan8 canvas. Green remains; canvas holes become background0. The role colors are semantic constants in canonical Racket rule `c4cb7e8eec6d`. Do not permute them as nuisance colors.

Review `review-b24d187658115e8e` started from v2.0.2, generator SHA256 `278461bca5d2089a3ec04609ff2c8dca3b51e9198efe1e154940d641b0f6211c`. There were no prior task-local tests, decisions or review-index findings. The original distribution rationale is unknown beyond the old 3×3/asymmetry/isolation comments.

The selected base solution's `racket_target.target_code` differed from canonical only by a comment. The recorded authority check passed both executable texts on all 3 labeled canonical pairs. This review synchronizes that selected field to unchanged canonical text; `raw_code` and all other JSON fields are preserved. No rule behavior is changed.

## Reversed choices and their evidence

- **G1: Canonical footprint.** Old code required exactly 3×3 and rejected canonical train1/test0 (both 3×4). v3.0.0 supports both canonical footprints and cycles through all three canonical grid dimensions, 10×14, 11×15, 12×16. `counterexamples/baseline_regressions.json` retains exact failures.
- **G2: Position.** Old ordinary templates were always left of canvases. Both left-first and top-first rivals fit all three canonical pairs. Racket-labelled reversed placements refute them. Ordinary generation now cycles through all four relative quadrants; `counterexamples/role_reversal.json` retains an actual-authority witness.
- **G3: Controls.** Helpful mask-family/texture requests were ignored and advertised global dimension bounds rejected. Every retained exact axis is now consumed and recovered from the grid; matching alias requests agree and conflicting aliases are declared incompatible. Old `position_bias=spread` is replaced by four concrete quadrant tokens and is rejected. Invalid missing/mismatched-object textures are rejected rather than emitted as ordinary data. Fixed color counts and matching canvas are diagnostic invariant checks, not diversity knobs.
- **G4: Validator.** Reject bool/float/nonscalar cells safely before component extraction, enforce connected tight templates, matching solid canvases and an empty bbox gap. Self-check accepts all 3 canonical inputs. Strict domain is the same bounded canonical-style manifold, not all grids Racket can evaluate.
- **G5: Teaching support.** Eight executable rivals cover identity, erasing the template, three transformed stamps, two positional assignments, and clipping to width3. Only the two positional rivals are declared canonical-fitting shortcuts. Witness declarations are checked against authority labels; retained Python mirrors are clearly distinguished from Racket evidence.

## Lesson assembly

Use three demonstrations and one query. Every four consecutive raw slots cover four role quadrants and four mask families; footprint alternates 3×3/3×4. Holding out any slot still leaves both a role-right and role-below witness, a nonsquare witness, and an L/default mask asymmetric under LR/UD/180. Position, family and footprint phase shifts are seed-dependent; canonical dimension cycle makes the combined schedule period12. Production materialization and all query rotations are verified by the returned census, including all12 starts at a fixed seed. The finite competitor set does not prove universal identifiability.

Exact overrides may bypass the curriculum. `palette_kind` is a historical mask-geometry name, with `texture` as alias; colors always stay3/8. Ordinary masks are drawn from canonical, L, T and Z pools. Easy uses base orientations, medium the first two variants, hard all reflected variants and both nonsquare canonical masks. This is a concrete orientation-support difference, not a measured difficulty ranking.

## Limits and reusable evidence

Three-row template height is a deliberate bounded support choice; taller Racket-lawful templates are untested. Ordinary placements separate bboxes in both axes even though the validator accepts a gap in either axis. Diagonal adjacency, overlap, distractors, multiple canvases and color permutations are outside this generator domain. No claims about Qwen3.5-9B learning gains or catalog approval follow from a passing review.

Portable tests live in `tests/`. `workspace/probe_role_positions.py` prepares fixed-color counterfactuals, checks stored public Racket receipts against source/rule/input identities, and optionally measures ordinary role coverage. It is opt-in for this task; position-semantic tasks need a different adapter. Full before/intermediate/final commands and retained failures belong to the source-bound return's `RESULTS.json` and `checks/`, not duplicated here.
## Current reviewer considerations

Source SHA-256: `9e77fa42b117a86ba45e717018b1fbb8996b2ad2b3b7c8adf2b6b2124a935dd7`.

# Decisions — stencil transfer repair

## Scope and source authority

This is the second separately randomized review, assignment review-b24d187658115e8e, drawn once from a verified new extraction of the original packet. The previous round's return is preserved and was not used as this generator baseline. Original rationale is marked unknown where the old code gives no explanation. The reference is the selected canonical Racket rule c4cb7e8eec6d; only one redundant comment in selected base target_code was removed to align exact text. Recorded execution parity on all 3 canonical labels preceded that edit, and raw_code/canonical/all other JSON fields stay unchanged.

## Distribution decisions

| Choice | Prior observed behavior / rationale | Adopted behavior and reason | Alternative and practical limit |
|---|---|---|---|
| Footprint | Fixed 3×3; old summary said 3×3, broader rationale unknown | Both 3×3 and 3×4, because two of three labeled canonical inputs are 3×4 | Taller/larger masks are Racket-lawful but add untested support; keep this repair bounded |
| Grid dimensions | Advertised 8..14/10..18 but per-band draws rejected many endpoints | Ordinary cycle 10×14,11×15,12×16; full integer override ranges in every band | Random full-range defaults would dilute canonical profile frequency; exact overrides still cover all supported dimensions |
| Colors | Fixed 3 template/8 canvas | Preserve these semantic symbols and 0 background | Arbitrary color permutation would violate the actual rule |
| Position | Green always left, canvas right; rationale unknown | Four cyclic relative quadrants, with seed-dependent phase | IID positions can omit a decisive counterexample in a short lesson; curriculum supplies witnesses in every4-slot window |
| Isolation | Old code tried to buffer placements, validator did not enforce it | Construct disjoint row and column intervals, at least one empty separator; validator permits a gap in either axis | Bbox overlap, touching objects or distractors need new authority/domain work; ordinary support remains conservative |
| Mask geometry | Four hard-coded3×3 masks, including symmetric plus despite asymmetric prose | Distinct observable canonical/L/T/Z families with connected tight bboxes and holes; reflected variants | Full arbitrary-mask support would be broader but harder to validate for every teaching window |
| Symmetry | Blanket asymmetry claim contradicted data | T/Z symmetry is permitted as lawful; default/L witness in every three-demo holdout resolves transform rivals | Requiring every single grid to refute all transformations would unnecessarily exclude lawful symmetry |
| Helpful controls | palette_kind/texture and auxiliary controls ignored | Each accepted exact value is consumed and observable; texture aliases palette_kind | Conflicting aliases are rejected through declared tuples; there is no silent precedence |
| Legacy position token | spread was the only advertised value and was ignored | Four exact quadrant values replace it; spread rejects explicitly | Keeping an unobservable catch-all token would make exact override checking misleading |
| Invalid textures | Missing template/canvas and mismatched dimensions returned self-invalid inputs | Reject these production requests; retain minimal invalid counterexamples outside the ordinary domain | No shared checker bypass or fake lawful-degenerate declaration |
| Fixed counts | Two nonzero colors and matching canvas were singleton axes | Validate them as diagnostic invariants | Do not pretend singleton controls offer diversity; invalid values still fail |
| Difficulty | Initial repair inadvertently made all bands byte-identical | Easy base orientation, medium first two variants, hard full pools/both nonsquare canonical masks | Not calibrated against humans or models; canonical profile coverage remains available in all bands |

## Teaching contract and actual lesson assembly

Three demonstrations plus one query are the intended export shape. Four consecutive raw slots cover four quadrants and four families, plus two copies of each footprint size. Removing any one slot leaves a right-template and below-template witness, a nonsquare witness, and at least one all-transform-asymmetric L/default mask. The dimension cycle has period 3, giving a combined 12-slot curriculum. Every band shares those guarantees; each seed independently shifts position, family, shape and dimension phase. Exact overrides control individual lawful inputs and can bypass the curriculum.

Declared alternatives are identity, erasing the green template, LR/UD/180 stamp transforms, left-first/top-first role assignment, and truncating the mask at width3. Only left-first/top-first fit every usable canonical pair and are marked CANONICAL_SHORTCUTS. Executable witnesses bind these claims to actual Racket labels. The 300-lesson/1,200-rotation production census and all 12 starts at fixed seed 0 test the real sampler, not merely raw frequency. Saved records contain no rejections; exact inputs/hashes and overlapping-window counts are retained. Finite success does not certify undeclared hypotheses.

The post-repair solve helper separately prepares 3 demonstrations and 2 masked queries. It is an exposed execution record; it does not replace the 3+1 curriculum/rotation census. The blind task was independently solved first and kept separate.

## Reusable-tool decisions and review corrections

The role-position probe is explicitly task-local and authoring-only. Its movements preserve fixed colors, mask orientation/size, a connected template, matching solid canvas and separation; malformed or colliding scenes reject. A Python-mirror suitability check prevents known position-semantic behavior from being silently certified, and actual Racket output must agree. Wider invariance is unproved. The 288-draw coverage screen is labeled a Python proxy; the 17-input public batch is actual authority evidence.

Independent review reproduced two Important defects. The first version's metadata envelope failed the real public apply parser, and its scorer could accept wrong returned-input metadata. Six new tests failed before fixing these together: bare apply payload plus same-stem.meta.json, source/canonical/payload validation, exact returned-input equality/digests, output digest/validity and rule task identity. Full49-test checks and the actual pipeline then passed. No Critical or Minor reviewer findings remain; no second speculative code expansion was added.

## Explicit scope rulings and cost if wrong

1. Retain three-row 3×3/3×4 support. Cost: taller stencils accepted by reference semantics are not taught by this generator.
2. Keep fixed 3/8 colors and ordinary separation in both axes. Cost: broader positioning/distractor transfer is untested; arbitrary color permutations would be incorrect.
3. Let exact controls bypass the curriculum. Cost: downstream callers assembling overridden lessons must rerun identifiability checks.
4. Describe difficulty as orientation support. Cost: there is no established cognitive ranking or learning-uplift claim.
5. Treat finite rivals/counterfactuals as measured checks, not proof. Cost: undeclared shortcuts may remain; the two findings-only audits illustrate this limitation in other generators.
6. Require actual external command receipts for Racket provenance. Hash validation catches mismatches and corruption but cannot authenticate a manually fabricated record.
7. Keep all failure evidence in the return, with lossless compression and restoration hashes. Cost: full detailed review requires restoring large evidence files; summaries remain immediately readable.

## Decisions left to maintainers

Training approval/merge remains external to this return. Audit 4a9e2bc51201's count floor and audit c1fd38e5812b's coupled span uniformity are actionable findings, not patched source. The latter's stale declared rule pin is preserved as a separate low-severity provenance issue. Shared-tool integration of the opt-in role gate is proposed in F1; no shared checker or approval policy was changed.
