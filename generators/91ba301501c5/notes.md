# Working notes: 91ba301501c5

## Accepted rule

A full gray row divides the canvas. Blue extends vertically away from the row; red extends vertically toward it. Rays advance only through cells that were zero in the input. A blue mark on its away-facing canvas boundary has a lawful zero-length ray.

Selected normalized rule hash: `c850a30c9e63`.

## 2026-09-28 repair

- Replaced the v1.2 ad-hoc axis surface with five exact observable axes.
- Every ordinary draw contains all four color/side branches.
- Canonical 10x10 profiles occur at a one-third prior; canonical divider rows 3, 4, and 5 are exact override values.
- Boundary-blue examples are paired with positive blue evidence on both sides.
- Same-side columns are distinct; one red/blue pair shares a column across the divider.
- Added structural checking, exact override observation, semantic witnesses, executable rival rules, and two-demo lesson identifiability.
- Synchronized selected base `target_code` to canonical source while retaining archival `raw_code`.

Final evidence: `checks/after/` in return `review-bc4e2bfc9e851ee7` is 12/12 green. Focused tests live in `tests/test_generator_91ba301501c5.py`.

## Known limits / next probes

- Current shapes are 10x10, 10x14, and 14x10 only.
- Same-side ray blockers are excluded; add a dedicated collision profile only after deciding whether blocker interactions belong in the intended training domain.
- Current rivals target the two dominant direction shortcuts. Add rivals based on actual model-error traces rather than speculative breadth.
## Current reviewer considerations

Source SHA-256: `e40bb84f5b027b6406e27122aa3a3f18828f5c9fc705c2fbbd632aabdfede4dd`.

# Input and review decisions for 91ba301501c5

## Design objective

Teach the relative-direction rule directly and repeatedly without manufacturing invalid negative fixtures, while retaining canonical scale, canonical boundary behavior, and exact control over every declared axis.

## Decision ledger

| Choice | Baseline / original rationale | Decision and evidence | Alternatives considered | Failure mode / limitation |
|---|---|---|---|---|
| Canonical rule | The original docstring stated blue-away/red-toward, but did not pin the source. | Pin normalized canonical source as `RULE_HASH=c850a30c9e63`; use the original-input zero test in both canonical Racket and Python rivals. | Rewrite Racket, or pin the compact archival spelling. | No semantic Racket rewrite was justified; only active source synchronization was needed. |
| Canvas profiles | Baseline sampled broad height/width ranges by difficulty. It produced 0/60 canonical-profile draws. | Use three exact profiles: 10x10, 10x14, 14x10. Canonical is one third of the prior; pinned result is 21/60. | Keep five profiles; add a separate weighted anchor bit; use only 10x10. | Three profiles are intentionally narrower than arbitrary scale variation. |
| Divider rows | Baseline had center/upper/lower/rng, but its combined surface was not exactly observable. | Use `upper`, `mid`, `center`; on 10x10 these are rows 3, 4, 5, exactly covering all public divider rows. | Two rows only; proportional quartiles; unrestricted integer row. | Tall profiles map to rows 3, 6, 7 rather than reproducing every possible relative location. |
| Mark counts | Baseline declared 2..6 but difficulty-specific ranges rejected many declared overrides. | Use exact difficulty-aware keyed draws: blue 3..5, red 2..5. Counts cover the canonical range while guaranteeing branch evidence. | Preserve 2..6; expose per-side counts. | Does not generate very dense mark fields. |
| Side balance | Baseline included `above_only`, `below_only`, and `skewed`, allowing lessons to omit half the rule. | Remove side balance as an axis. Every grid contains both colors above and below. | Schedule single-branch lessons across an episode. | Individual grids are deliberately information-dense rather than staged from simple to complex. |
| Boundary blue | Baseline treated any zero-length blue ray as invalid, rejecting all canonical inputs. | Add `edge_blue` as an exact boolean axis. When true, add one blue mark at its away-facing boundary, while retaining positive blue witnesses on both sides. | Ban zero rays; allow arbitrary blocked zero rays. | The boundary mark itself does not change the output, so positive companions are mandatory. |
| Mark columns | Baseline used reservation logic but had no exact observable contract. | Require distinct columns among marks on the same side, and force one opposite-side red/blue pair to share a column. | Allow arbitrary same-side collisions; require all columns unique. | Same-side ray-blocking behavior is not taught. Cross-divider sharing prevents a global-uniqueness shortcut. |
| Palette | Baseline exposed a fake singleton `palette_kind=fixed`. | Remove the axis. Palette roles 0/1/2/5 are task semantics, not a variable. | Relabel colors. | Color-relabeled generalization is outside this task's selected rule and public examples. |
| Degenerate textures | Baseline placed `no_line`, `no_marks`, and `full_grid` in the valid texture domain. | Remove them from generation. Negative fixtures belong in tests, not training draws. | Keep them under a separately declared diagnostic-only API. | The generator itself no longer emits malformed examples for checker testing; focused tests cover failures instead. |
| Unknown overrides | Baseline silently accepted typos. | Reject any key not present in `AXES`. | Let `gen_ctx` ignore unknown keys. | None; loud failure is preferable to false reproducibility. |
| Override observability | Baseline had ignored and aliased axes and no reliable observer. | Implement `observe_overrides()` for all five axes. Final gate accepts 9,450/9,450 draws. | Use metadata rather than infer from cells. | Observer supports only returned grids in this declared grammar, which is the intended contract. |
| Structural checker | Baseline checker rejected lawful canonical edge cases while allowing a problematic ordinary surface. | Validate the actual task grammar, accept boundary zero rays only at the correct edge, and demand positive directional evidence. | Minimal shape/palette checker; exact public-template matcher. | The checker is stricter than the full Racket domain because it defines the training grammar, not every executable input. |
| Semantic contract | None existed. | Declare strict predicate, four witnesses, two rivals, witness-to-rival claims, canonical shortcuts, lesson competitors, and a two-demo identifiability hook. | Rely on rule smoke and marginal diversity. | Rival coverage is targeted, not exhaustive. |
| Lesson size | Unknown. | `EXAMPLES_NEEDED=2`; every generated demonstration individually contains all four branches, and the gate verifies 12/12 two-demo lessons. | One demo; three or more demos. | Two demos are sufficient for the declared rivals, not a proof against all hypotheses. |
| Base authorities | Two selected `target_code` values used a compact equivalent source. | Copy canonical `program_solution` exactly into both selected targets; preserve compact `raw_code` as archival. | Rewrite canonical to compact form; delete archival text. | Final report still labels the two archival texts divergent, but selected authorities are synchronized. |

## Probe sequence

1. Immutable before battery established the six blocking failure classes.
2. Focused tests were written and observed failing before implementation.
3. A first repaired battery exposed an 18.3% canonical-profile rate, below the 25% clean threshold.
4. A pinned-seed regression reproduced 11/60 before the profile prior was narrowed; it then passed.
5. Exact row-4 coverage and lesson-identifiability tests were added and observed failing before their implementation.
6. Final focused tests and the full 12-stage battery passed.

## Deferred experiments

- Add a separately named collision profile only after checking whether same-column blockers are intended data or accidental ambiguity.
- Expand the rival library with fixed absolute-direction and line-ignored programs if model-error traces show those hypotheses surviving.
- Measure small-model accuracy with and without the boundary-blue axis; it is semantically correct but may have different curriculum value by model size.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/91ba301501c5/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current native parametric candidate

Production source and canonical program remain unchanged. The separate
`workspace/parametric/` family exposes `region_policy=rays_only|largest_region`.
The second setting completes the canonical rays, recomputes zero-region topology,
then paints the unique largest resulting region 8. Its input-dependent region
membership and size are the intermediate; selecting on the original input gives
a different protected-Racket output on retained witnesses.

The adapter supports independent 2–6 demos and 1–4 prefix-stable queries; four
queries include a substantive 30x30 scene in seed-shuffled position. Inputs are
matched across settings. Two-demo teaching checks cover the finite documented
rival bank. `workspace/parametric/evidence/current/audit.json` records 800 sampled
episodes, 5,200 pairs, 400 matched-input comparisons, 2,000 single-query public
projections and 56 protected-Racket evaluations, with zero final failures.
The whole changed task test suite passed 32 tests (24 new, 8 existing).

The initial bbox-zero-fill rival was non-distinguishing on the admitted scenes;
it is not represented as eliminated. See the workspace README for that repaired
sampler assumption, current grammar and reproduction. The legacy fractional
production-override finding remains outside this separate adapter's scope;
new native count/seed/settings boundaries reject invalid values strictly.
Reviewer qualification is not owner exact-source acceptance; no training admission.
