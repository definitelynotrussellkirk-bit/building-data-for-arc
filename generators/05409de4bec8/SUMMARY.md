# 05409de4bec8

A modal black field contains four structured cells of one target color and two dense distractor colors. Rows and columns containing exactly two target cells become full target-colored lines; for a four-corner rectangle, only the longer rectangle axis is extended.

Kind: `per_puzzle`. Selected version: `5.0.0`. Canonical Racket rule hash: `dfbf6efa8173` (unchanged).

The default five-slot curriculum is `rectangle_a → multi_row → rectangle_b → multi_col → cross_anchor`. Lessons use four consecutive demonstrations and one query. Every four-slot window contains a rectangle witness and a multiple-parallel-line witness, refuting the declared `all_pair_lines` and canonical-fitting `single_pair_per_axis` shortcuts for every query rotation.

Final source-bound evidence: 12/12 battery stages green; 300/300 production lessons and 1,500/1,500 held-out query rotations unambiguous against declared rivals; all 15 fixed-seed schedule starts and all 75 rotations unambiguous; one four-demo/four-query production episode had four distinct Racket-labelled queries and passed the lesson hook. The separate `workspace/parametric/` prototype assesses `rectangle_policy = longer | both` and is not part of selected execution or approval.

Return status is blocked only by the inherited frozen task fixture's nonportable canonical-data path. New task-local tests pass independently; the frozen fixture is intentionally unchanged for maintainer migration.
