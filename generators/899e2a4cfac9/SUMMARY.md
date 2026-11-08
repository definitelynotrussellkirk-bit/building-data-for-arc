# 899e2a4cfac9 — keep only interior objects

Version **2.1.0**, kind `per_puzzle`.

Remove each same-color, four-connected nonzero component that touches any grid edge. Preserve every fully interior component at its original position and color. Background is fixed zero. The unchanged Racket authority supplies all labels; rule hash `50ed982b7d21`.

Default generation alternates with period two. Even indices produce a canonical-support scene with two border dominoes and one interior L/square/T. Odd indices produce seven varied components: four border objects, two larger interior survivors, and a mandatory surviving singleton. Rich scenes distinguish size rules, global color deletion, four/eight connectivity, same-color/all-nonzero segmentation, border-cell-only erasure, singleton deletion, largest-interior-only filtering, and each edge omission. Twelve named rivals are checked against actual labeled lessons.

Exact controls are `grid_h=6..12`, `grid_w=7..14`, `n_blobs=3..7`, and `n_distinct_colors=3..6`, with the color count **including zero**. Foreground colors come from 1..9. Requests for five/six total colors are incompatible with three/four components; six total colors is also incompatible with five components. Unknown legacy texture/palette controls are rejected. Overrides can alter the curriculum; reduced component counts do not promise all rich witnesses.

Final generator SHA256: `0fe1fd03f31b285873c464d28ad3e0356299f3f6709fb75c1af57c5dd68a7ce5`. Final copied-runtime evidence reports 12/12 battery stages green and 19/19 task tests passed. The final production census found no declared-rival ambiguity over 300 lessons and 1,200 query rotations; separate fixed-seed schedule enumeration checked both residues across three bands. These are finite source-bound checks. The broad strict predicate describes lawful mixed erased/retained scenes, not exact canonical morphology. Approval is derived by the catalog from exact current source and retained evidence.

See [notes.md](notes.md) for contracts, history, evidence paths, and limitations; [retained counterexamples](counterexamples/border-filtering-rivals/README.md) for exact Racket-verified size, connectivity, and global-color disagreements, and [an emitted rich witness](counterexamples/generated-rich-witness/README.md) that refutes all twelve declared competitors.
