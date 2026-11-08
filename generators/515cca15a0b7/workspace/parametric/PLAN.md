# Native recolor / connectivity / border filter

Goal: preserve the exact canonical border predicate and add an episode-fixed
`gray_to_blue` preprocessing setting. A recolors gray cells blue, merging some
previously separate blue components. B recomputes same-color 4-connectivity and
retains components touching both border axes. The changed intermediate component
structure is input-dependent; filtering before recoloring loses qualifying unions.

Alternatives: changing the border predicate alone does not demonstrate sequential
state dependence; propagating arbitrary contact colors adds unnecessary tie rules.
Use the small fixed recolor but preserve the nonlocal component recomputation.

Tasks:
- [x] Tests first: exact default, recolor-before-recompute fixture, diagonal rejection,
      strict request validation, matched/prefix-stable grids, density and privacy.
- [x] Construct 2–6-demo scenes with kept noncorner components, separated blue
      bridge pieces, ineffective bridges, same-color disconnected distractors,
      literal corners and diagonal-only neighbors. All four queries distinct.
- [x] Adversarial finite rival screen including reverse order, 8-connectivity,
      global-color grouping, all/any/literal border predicates and wrong recolors.
- [x] Full scoped tests, bounded audit with actual protected labels, manifest,
      native qualification, shuffled one-query export and causal witness.

No production or shared source edits. Only same-checkout adjacent resources.
Substantive 30x30 uses dense noncorner bodies and a large gray corner component,
not empty padding. Default native lesson is three demos, minimum two. No owner
acceptance/training admission is claimed; final review is author self-review.

Self-review: color-blind contact hole repaired with no demo-count increase. 55 full scoped tests passed; 160 bounded episodes, 32 audit executions; 4 native jobs / 40 executions. Causal witness reviewer_replayed. Owner acceptance pending.
