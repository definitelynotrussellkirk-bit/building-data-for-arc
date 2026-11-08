# Current notes: 874aa60956cc

## Review review-0316de823b2ad46b: native touch-count relay

The production generator and canonical setting remain byte-for-byte unchanged at
source SHA-256 `b232198350b8e25c99c3ab5cd784c3c2c4c8c7908f1677c44eec095f801ae2ac`
and canonical program SHA-256
`8f9f3652469e05e73c4a095884b3a1b5163f29024419113ca41845a136db317c`.
A task-local native adapter now exposes `border_mode=all` and the opt-in
`border_mode=touch_count_relay`. The relay first paints the controller pair's
border, counts distinct later paired colors with a clue on that derived border,
and uses that count (1, 2, or 3) to select the later border to paint. Inputs are
matched across settings; demonstrations and queries are independently selectable
in 2..6 and 1..4, with four prefix-stable private queries and a 30x30 fourth query.

The native qualifier bound the exact adapter/resources and qualified four jobs:
two settings crossed with seeds 0 and 17, each with two demonstrations and four
queries, for 32 protected-Racket evaluations. The finite authoring audit covered
64 seeds per setting (128 jobs), ten declared shortcut families, and 22 additional
protected-Racket evaluations; none of the named wrong rules both fit the visible
demonstrations and changed a query in that tested scope. The retained 30x30
counterfactual has touch count 3; forcing count 1 selects a different border and
changes 102 cells. The repository's protected witness checker independently
replayed both programs and reported `reviewer_replayed`.

Evidence: `checks/874aa60956cc-tests/result.json`,
`checks/874aa60956cc/self-audit/report.json`,
`checks/874aa60956cc/qualification/qualification.json`, and
`checks/874aa60956cc/causal/replay.json`. The source inventory is
`workspace/parametric/evidence/manifest.json` (SHA-256
`ba6e9604ab05e3bf1c8e972947cd02b3246f197d187c38de72f11a02e233ba6a`).
These are bounded reviewer checks, not universal uniqueness, owner acceptance, or
training admission. The next useful action is exact-source owner integration,
canonical approval of the opt-in rule, then fresh native acceptance replay.

## Intended rule

Original nonzero colors are processed in first row-major appearance order. Exactly two coordinates define an axis-aligned bounding border. Each border is painted into the accumulating output; later colors can overwrite earlier paint and original clues. Other multiplicities do not expand. Canonical Racket unchanged; RULE_HASH 8f9f3652469e.

## Current input sampler and controls

Version 2.0.0; source SHA-256 `b232198350b8e25c99c3ab5cd784c3c2c4c8c7908f1677c44eec095f801ae2ac`. Five independent exact integer controls: grid_h/grid_w 5..18; rectangles 1..6; singletons/triples each 0..1. Counts are measured directly from pixels by observe_overrides. Default draws favor a 9x10 canonical profile, with different size/count weights by difficulty and full explicit domains in every band. Random colors 1..9 are assigned to geometric roles.

The prior separated-region rule was reversed because canonical examples already overlap. A random-position three-pair crossing scaffold now teaches anti-diagonal bounds, two-cell sides, paint order and overwritten clues. More pairs may be added. Odd default sample indices add an inert singleton and triple; even indices retain paired-only scenes. The period is two. Three demonstrations plus one query and all its query rotations were checked against five declared rivals. Explicit controls bypass teaching filtering and expose structural inputs only.

The prior palette_kind/texture controls were ignored; palette_size/n_distinct_colors were redundant with the intended pair count, and density/position_bias were constant decorations. These six old names now raise an explicit unknown-or-retired control error. The old standalone no_pairs/single_corner/collinear textures are retired from normal sampling, not declared illegal under the Racket function.

## Validated evidence

Final battery: 12/12 green; 37 portable cases passed, 0 skips; 49,050 shared override draws and 14,112 full-Cartesian control cases passed. Canonical inputs: 5/5 accepted; exact profile hits: 3/20 easy, 9/20 medium, 5/20 hard; strict domain: 600/600. 300 lessons/1,200 distinct input pairs and 1,200 query rotations: 0 declared-rival ambiguities. Both period starts at seed 0: 6 lessons/24 rotations, 12 unique inputs, 0 ambiguities. The Python probe's 300 draws contain 213 pooled unique inputs; it is not label authority.

## Current limits and open work

The default geometry is deliberately biased toward a recurring crossing scaffold. It does not sample every lawful arrangement, and full control support is not full pixel-layout support. Empty scenes, collinear pairs, more than one singleton/triple, and multiplicities above three are outside the validator's normal sampler domain. Five named rivals and finite seeds do not establish universal identifiability. Approval and training admission require owner integration. No unresolved inherited task audit was present in the packet.

Minimal inputs are in counterexamples/. Portable focused tests and workspace/probe_semantics.py plus workspace/probe_controls.py retain reusable checks. The return's REVIEW.md/DECISIONS.md contain exact evidence paths and the repaired intermediate dead-bands failure; do not copy its narrative history back into these notes.
## Current reviewer considerations

Source SHA-256: `b232198350b8e25c99c3ab5cd784c3c2c4c8c7908f1677c44eec095f801ae2ac`.

# Decisions: 874aa60956cc

## Rule and authority

The source rule scans original nonzero colors in row-major first-appearance order. Exactly two coordinates define a bounding rectangle; its border is painted into the accumulating output. Groups of any other cardinality cause no expansion. Later borders may overwrite earlier output or original clues. The canonical Racket row is unchanged and pinned to 8f9f3652469e. Python predictions in the generator and probes are authoring diagnostics; Racket supplies dataset and counterexample labels.

## Choices and reversals

| Choice | Prior choice/rationale | Decision and evidence |
|---|---|---|
| Overlap | Guarded separated regions; original rationale unknown, and inconsistent with canonical overlaps | Permit crossings and occlusion; retain first-appearance and overwritten-clue witnesses confirmed by Racket |
| Pair count | Capped placement could return fewer pairs; likely collision avoidance | Construct all requested groups from unused coordinates; fail explicitly instead of returning a short draw |
| Dimensions | AXES said 5..18 but per-band draw ranges rejected legal controls | Full 5..18 range on both axes in every band; independent Cartesian verification includes 5x5 with six pairs and both distractor kinds |
| Palette controls | palette_kind/texture ignored; palette_size/n_distinct_colors redundant aliases; density/position_bias constant | Retire those six names explicitly with ValueError; keep grid_h/grid_w/rectangles and add independent singletons/triples. Random sample of 1..9 assigns color roles without rank coupling |
| Validator | Early return on singleton/collinear group skipped remaining errors; cell types unchecked | Validate shape and ARC integers, then every group; accept 1..6 noncollinear pairs plus at most one singleton and one triple |
| Default distribution | Small disjoint 3..4 by 3..5 rectangles with weak shape coverage | Three-pair crossing scaffold with random increasing coordinates and color roles, optional extra pairs, two-cell-side witness and horizontal reflection |
| Canonical profile | Baseline zero-support bands | Favor 9x10 but retain all dimensions as random possibilities; observed exact profile hits 3/20, 9/20, 5/20 |
| Difficulty | First repair accidentally identical across bands | Different default dimension/count weights; preserved dead-bands failure and regression before changing weights |
| Multiplicity teaching | Singleton/no-pair/collinear textures were fixed diagnostic grids | Even indices use paired colors; odd indices add singleton and triple groups. The reference ignores their expansion; actual clue cells may still be overwritten |
| Label source | Racket authority already selected | Preserve Racket source. Python mirrors filter candidate inputs and implement explicitly named rivals; never return their predictions as labels |

The old `texture` degenerate requests are retired alongside the dead palette alias. The reference can still be applied to such grids directly. This sampler deliberately requires at least one noncollinear paired color and an informative normal domain. This boundary is narrower than the whole reference function, not a claim that other reference inputs are unlawful.

## Lesson assembly

The measured intended policy is three demonstrations and one query, using consecutive accepted samples. Default sample indices alternate between paired and multiplicity scenes, period two. Four consecutive inputs contain two multiplicity scenes; holding out any one leaves a multiplicity witness in the demonstrations. Every default draw additionally distinguishes positive-diagonal-only, minimum-side-three, pair-completion order, and restoration of original clues. A candidate may be resampled internally to retain those differences; no accepted sample is silently shortened.

The shared census recorded actual accepted indices and rejected samples. Production and query-rotation results are both zero ambiguities among the five declared rivals: 300 lessons/1,200 rotations, plus both starts at one fixed seed across all bands (6 lessons/24 rotations). These are finite measurements. The period enumeration overlaps inputs and is not another 24 unique-input sample. User-requested overrides bypass the teaching filter to expose the wider structural domain; arbitrary override mixtures, fewer demonstrations, skipped draws and undeclared competitors are not certified by these results. MIN_TRAIN_PAIRS is descriptive task metadata; the public runtime currently uses its default floor of three, as shown in solve provenance.

## Alternatives and residual shortcuts

Uniform free corner placement would give broader geometry but can omit the necessary witnesses in a short lesson. A larger cyclic menu with one subtle feature per grid would require more demonstrations and more complicated rotation requirements. The chosen rich scaffold makes the crucial ordering/geometry distinctions present in each ordinary input, while the multiplicity alternation supplies the remaining distinction. It is a teaching-biased distribution: three core pairs, shared coordinate relationships, and guaranteed crossings remain recognizable. The override domain is broader, but that alone does not imply broad default layout support. A future change could mix additional independently verified witness layouts and rerun the exact lesson census.

No claim is made that five rivals exhaust plausible rules. Collinear pairs, arbitrary larger multiplicities, color-free scenes, and a general all-seed proof were not added. No additional rules were composed merely to claim ARC composition coverage.

## Reproducers and tools

`workspace/probe_semantics.py` reads all usable canonical pairs, discovers the live rival dictionaries, reports cross-band uniqueness and preserves provisional generated witnesses. `workspace/probe_controls.py` independently counts pixel groups while enumerating every joint control tuple. The 5x5 `counterexamples/overlap-order.json` is emitted at seed 20261008/index 909 with controls grid_h=5, grid_w=5, rectangles=3, singletons=0, triples=0; `checks/overlap-racket.json` confirms its output. The inert-group counterexample is independently Racket-verified. Neither tool should be opened during a visible-only solve.
