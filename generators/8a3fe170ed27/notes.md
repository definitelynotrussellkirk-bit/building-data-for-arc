# 8a3fe170ed27 — current generator contract (v3.0.0)

## Intended task and authority

Generate only an input grid. The unchanged canonical Racket authority (`RULE_HASH = a5b527116538`) translates each occupied row horizontally by `(0, -1, 0, +1)[distance_above_last_nonempty_row % 4]`. The bottom active row stays still; the row immediately above shifts left. Preserve every occupied cell and every hole. Cells leaving the canvas are clipped. Python rival functions are diagnostics, not sources of training labels.

The input contains one connected foreground object of one color on zero background. Active rows are contiguous and have top and bottom background margins. Ordinary shapes contain sparse rails connected by full bars. The structured cohort uses full top and bottom bars, outer rails and optional internal bars/rails. The irregular cohort has a partial attached rail detail and a sparse tail below the last widest row.

## Exact controls

`grid_h` and `grid_w` are native integers from 5 to 20. `n_rows` is the exact number of active rows, from 2 to 18. `n_cells_per_row` is the maximum occupied-cell count in a row, from 1 to 18, realized by the full bars; sparse rows can contain fewer cells. `color` is a native integer from 1 to 9. Pattern choices are `solid`, `frame`, `lattice`, and `irregular`; edge choices are `interior`, `left`, and `right`.

Every supplied control is validated before sampling and is recoverable from `observe_overrides`. Exact counts are never clamped or silently resampled. Unpinned dimensions and placement adapt to feasible requests; otherwise a ValueError names the incompatible axes. Interior placement leaves both horizontal margins; left/right placement leaves at least one background column on the opposite side. A tight 5×5, three-row, span-four frame is feasible at either edge, including when placement is unpinned. Tight explicit controls may use a feasible odd height even though ordinary teaching examples prefer even heights.

The retired controls `palette_size`, `palette_kind`, `anchor_corner`, `texture`, and `position_bias` now raise named errors. Their earlier silent or ambiguous behavior is not part of the v3 contract. Pattern and edge mode provide observable structural controls. `seed` must be an integer; `sample_index` a nonnegative integer. Difficulty accepts `easy`, `medium`, `hard`, or None. Boolean cells, noninteger cells, malformed grids, disconnected components and multiple foreground colors are outside the input domain.

## Ordinary curriculum

`EXAMPLES_NEEDED = 4`; materialize four demonstrations plus one query from consecutive sample indices. `LESSON_SCHEDULE_PERIOD = 4` and `schedule_profile` returns the source index modulo four.

| Profile | Structure | Placement | Bottom margin | Sparse tail phase |
|---|---|---|---:|---:|
| 0 | Frame/lattice | Interior | 1 | Bottom is a full bar. |
| 1 | Irregular | Left edge | 2 | 1 modulo 4 |
| 2 | Irregular | Interior | 3 | 2 modulo 4 |
| 3 | Irregular | Right edge | 4 | 3 modulo 4 |

Ordinary irregular inputs have at least ten active rows and even height. Their tails have at least five sparse rows, with lengths selected in complete four-row increments when feasible. The long tails retain isolated edge cells at the left- and right-shifting phases. A partial cell near the top distinguishes exact row translation from reconstruction using the intersection of all rails.

Any five consecutive pairs contain all three irregular tail phases. After any single query holdout, the demonstrations retain at least two distinct phases and at least one edge example. This supports arbitrary single-query rotations against the 13 declared rivals. It does not establish identifiability against every conceivable hypothesis. Explicit small, solid or otherwise constrained research overrides are lawful when self-check accepts them, but do not carry this ordinary-lesson guarantee.

## Canonical support and diagnostics

Default dimension choices favor the observed 15×15, 15×14 and 13×14 profiles while retaining other feasible sizes to 20×20. Color and motif details are generated independently; canonical arrays are not copied into the sampler. `strict_canonical_like` requires an interior frame or lattice with holes and full top/bottom bars. The ordinary schedule supplies one such profile per four positions; lawful clipping and irregular extensions are not mislabeled as exact family matches.

Seven declared canonical shortcuts fit all five usable canonical pairs: last-widest-row anchoring and its conditional offsets one/two/three, shared-rail reconstruction, wrapping, and clamping. Six other competitors test first-row anchoring, two canvas-bottom anchors, opposite phase, envelope filling, and identity. `lesson_identifiable` reports only actual demo-fit/query-disagreement cases from this finite registry. Missing or errored candidates are not a proof of unambiguous lessons.

Run the source-bound probe and portable regression commands in `workspace/README.md`. `counterexamples/declared_rivals.json` contains shared input witnesses, public Racket outputs and first rival predictions. The return's final measurements are in `WORK/checks/verified/`: task tests, full battery, fixed-seed period census, and 100 lessons per band with query rotation. Consult their exact generator/rule hashes, sample denominators and unique-input counts. Passing diagnostics do not themselves grant training approval.
## Current reviewer considerations

Source SHA-256: `986186e74cb6380d42eef591b513c2a7773006196d0f2530dbea8c31f676787c`.

# Repair decisions: 8a3fe170ed27

## Scope and authority

The selected task is the row-wave problem imported as `1c56ad9f`. The pinned input generator is v2.2.0. The review changes that task's selected implementation, current notes, summary, tests, workspace probe and counterexamples. The two drawn audit targets are findings-only. No canonical ledger bytes, audit source, audit notes, frozen fixture or shared implementation are changed.

The canonical Racket rule is unchanged: the last nonempty row is the anchor and distance above it selects `(0, -1, 0, +1)` modulo four. Rows keep their exact occupied cells and holes, with horizontal clipping. The old Python phase helper and prose disagreed with those signs; Racket-generated labels were not relabeled to match the erroneous helper. The selected base authority's `racket_target.target_code` is synchronized to the existing canonical text, while archival `raw_code` is preserved. The conservative `authority-sync --selected-only` proposal refused the token-level changes automatically; manual comparison and already-recorded execution parity justified the selected-string update. `checks/authority-manual-review.json` distinguishes that synchronization from a semantic rule change.

## D1: Restore the structures that the task requires

The baseline produces connected solid rectangles with identical full support in each active row. The canonical examples contain rails, bars and holes. Keeping the rectangle generator and merely increasing its size or palette would not teach preservation of holes: envelope filling would continue to fit the generated population. The repaired generator makes a structured frame or lattice in one schedule position and irregular rail/bar shapes in the other three. Full bars keep one connected object; sparse rows preserve meaningful structure.

Frames/lattices use full top and bottom bars, outer rails, and optional internal bars or rails while reserving a real hole. Irregular objects add an attached detail that is not a complete rail and place several sparse rows below the last full bar. This distinguishes moving each exact row from rebuilding the object from a shared rail intersection or using the widest row as the anchor. Solid shapes remain available only as explicit research controls. They are lawful inputs, but they do not count as strict canonical-like samples.

## D2: Separate ordinary lesson support from exact research controls

The new public contract has seven explicit controls. Inputs use a zero background and one foreground color; all values must be native integers where integers are advertised. Unknown keys and the retired generic controls fail with their names instead of being ignored. This is an intentional v3 contract cleanup.

| Control | Exact meaning and domain |
|---|---|
| `grid_h`, `grid_w` | Canvas dimensions, each 5–20. |
| `n_rows` | Number of contiguous active rows, 2–18. Top and bottom background margins are required. |
| `n_cells_per_row` | Maximum occupied-cell count in any row, 1–18; full bars realize it, sparse rows can contain fewer cells. |
| `color` | The single nonzero object color, 1–9. |
| `pattern` | `solid`, `frame`, `lattice`, or `irregular`, realized observably in the pixels. |
| `edge_mode` | `interior`, `left`, or `right`; an edge layout keeps at least one background column on the opposite side. |

Retired controls are `palette_size`, `palette_kind`, `anchor_corner`, `texture`, and `position_bias`. Palette and corner controls were ignored or contradicted the single-object domain; generic texture settings did not describe the canonical structural distinction. Pattern and edge controls supply explicit observable alternatives. Passing an old control is now an actionable error, not a silently changed distribution.

Pinned counts are exact. Unpinned dimensions and placement may adapt to make them fit. Interior placement needs two horizontal margins; a one-sided edge needs one. A 5×5 canvas with a three-row, four-cell-wide frame is a retained regression for both explicit edge choices and an unpinned edge. Explicit interior placement for that same width remains incompatible. Ordinary even-height preferences must not empty the set of feasible rows under a small explicit size constraint. Research overrides can request small or simple motifs without inheriting the ordinary lesson guarantee.

## D3: Keep canonical size support without copying examples

The default dimension draws favor the three observed shape profiles (15×15, 15×14 and 13×14) while retaining other feasible sizes up to 20×20. Color is still sampled independently from 1–9, and geometry and placement are generated rather than copied from canonical arrays. Ordinary irregular heights must accommodate their sparse tail and scheduled vertical margin, so their feasible lower bounds depend on schedule position. The final profile report gives the actual pooled and per-band denominators; a favorable pooled result is not used to conceal a missing band.

This is an explicit distribution choice for a small model's curriculum. It restores support for the source task while retaining lawful generalization cases. A uniform dimension draw would waste many examples on sizes unrelated to the task and had already failed the packet's strict profile floor. Conversely, copying the five canonical grids would provide poor diversity and would not test the proposed rivals.

## D4: Make clipping teachable and retain the original authority

The canonical examples leave horizontal room, but the unchanged Racket operation clips cells that shift beyond a canvas edge. The generator now includes left and right edge examples as a lawful extension. Long sparse tails put isolated rail cells at the distance-one and distance-three phases, so wrapping and clamping create different observable outputs. Full edge rows alone would often conceal clamping through collisions, so they were not accepted as sufficient witnesses.

The strict canonical-like hook continues to identify the interior frame/lattice cohort separately. Input validity and resemblance to the original example family are different checks. The default schedule supplies one strict structured position out of four; all default positions remain lawful.

## D5: Four demonstrations are needed for the declared anchor family

The first repaired schedule used three demonstrations and two irregular examples per four-position cycle. Independent review found that its fixed two-row tail admitted `last_widest + 2` whenever the bottom was sparse. Random tail lengths could remove that population-wide shortcut yet still leave a lesson whose held-out query was its only differing tail. A third conditional offset would then fit all remaining demonstrations.

The final schedule uses four demonstrations and one query, with this period:

| Position modulo 4 | Pattern and placement | Sparse tail phase modulo 4 |
|---|---|---:|
| 0 | Frame/lattice, interior | 0: bottom full bar is the anchor. |
| 1 | Irregular, left edge | 1 |
| 2 | Irregular, interior | 2 |
| 3 | Irregular, right edge | 3 |

Ordinary irregular objects have even active heights of at least ten and sparse tails of at least five. Tail lengths can vary by complete four-row cycles when room permits, while retaining their scheduled phase. Every five consecutive inputs include all three irregular phases. Holding out any one pair leaves at least two distinct phases among the demonstrations, refuting every conditional constant-offset widest-row anchor in the declared family. At least one left/right example also remains, which refutes the shared wrapping and clamping rivals. This does not require both edge placements after every holdout.

The final registry contains 13 distinct rivals. Seven fit all five canonical pairs: widest-row anchoring with conditional offsets 0, 1, 2 and 3; shared-rail reconstruction; wrapping; and clamping. The other six test first-row anchoring, two grid-bottom anchors, opposite phase, envelope filling and identity. Canonical-fit status is measured, not asserted merely because a callable is named a shortcut.

## D6: Verification is bound to exact source bytes

The retained evidence distinguishes original, intermediate and final sources. Tests were first run against the defective version and again after each material repair. The small task-local probe obtains labels from the public Racket API and records each declared rival's first counterexample. The fixed-seed schedule census checks every period start in all three bands; the larger census checks 100 production lessons per band with every pair held out in turn. Unique inputs are reported separately from overlapping lesson windows.

These are finite checks against named competitors, not a proof that every possible rule is uniquely determined. Explicit research draws, untested seed populations, other lesson assemblers, multiple simultaneous holdouts and undeclared rivals are outside that guarantee. Passing checks do not themselves change training approval.

The original blind solve and the exposed post-repair solve remain separate. If a candidate changed after an episode was prepared, that entire real episode was retained under `checks/prior-solve/` and a new one was prepared after the final battery passed. Query answers remain masked; visible-example success is never presented as hidden-query correctness. The final handoff also applies the generated delta in an independently extracted packet and verifies every changed file before rerunning tests and the public Racket probe.

## Proposed parametric extension (review-dcc38d44a8195f95)

The review adds a prototype-only episode parameter under
`workspace/parametric/`: `wave_orientation ∈ {left_first, right_first}`. The
canonical/default `left_first` cycle is `(0,-1,0,+1)`; the proposed mirror is
`(0,+1,0,-1)`. Both retain the same anchor, distance-modulo-four, exact-row
translation, hole-preservation, and clipping semantics. The selected production
sampler supplies four demonstrations plus one query, with one setting fixed for
the entire episode; every demonstration must refute the opposite setting.

This extension does **not** modify `generator.py`, the canonical Racket text,
`RULE_HASH = a5b527116538`, catalogue authority, or production labels. Exact
standalone rules, public masked examples, focused tests, and source-bound
execution evidence are in `workspace/parametric/` and
`WORK/checks/parametric/`. The evidence is deliberately finite: two settings,
one retained episode seed, and one named alternative per setting; it is not
training approval or universal identifiability evidence.
