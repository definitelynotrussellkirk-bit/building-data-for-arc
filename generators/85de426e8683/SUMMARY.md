# 85de426e8683

Recolor the middle cell of every **whole gray (5), 8-connected object** that is
exactly three cells on a 45-degree diagonal. A diagonal run embedded in a
larger gray object is not a target; unrelated colored objects are unchanged.

Generator version: `2.0.0`  
Canonical Racket rule hash: `810181a298c8` (unchanged)

The default four-example curriculum cycles through:

1. two clean targets,
2. a target plus a five-cell diagonal near-miss,
3. two targets plus a branched gray near-miss, and
4. both target slopes plus horizontal/vertical gray decoys and a pre-existing
   yellow cell.

Default dimensions stay within the canonical envelope: heights `8..10`, widths
`9..11`. Exact axes are `grid_h`, `grid_w`, and `scene_profile`.

Review diagnostics include `observe_overrides`, `rule_mirror`,
`LESSON_COMPETITORS`, and `lesson_identifiable`; task-local regressions live in
`tests/test_generator_85de426e8683.py`.
