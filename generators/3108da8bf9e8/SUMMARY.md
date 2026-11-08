# 3108da8bf9e8

Generate an 11×11 grid divided by all-zero rows and columns at indices 3 and 7 into nine 3×3 blocks. Every block uses only colors 1 and 2. The nine blocks have distinct color-1 counts selected from `0..9`, so exactly one count is omitted. The transformation sorts whole blocks by ascending color-1 count, places the three smallest left-to-right on the bottom macro-row, the next three on the middle row, and the three largest on the top row, while preserving separator cells and every block's internal texture exactly.

The exact input-distribution control is `omitted_count=0..9`. Difficulty changes rank displacement without introducing a different rule: easy moves exactly four blocks in a cycle spanning all three macro-rows and columns, medium displaces five to eight blocks, and hard is a full nine-block derangement. Every band rejects row-local sorting, column-local sorting, fixed macro-row reversal, and every layout solvable by partitioning the nine positions into three independent triples and sorting only inside those groups. Exact-count textures are sampled uniformly from all lawful 3×3 masks; only the vanishingly rare all-prefix joint draw is repaired so the count-only repainting rival cannot become indistinguishable.

The generator includes a Python rule mirror, strict canonical checks, exact override observation, six named semantic rivals/witnesses, and a reusable position-map/texture/locality/lesson shortcut census under `workspace/shortcut_census.py`.

Kind: `per_puzzle`. Reviewed version: `3.2.0`. Rule hash: `05977542b8d5`.

Review evidence: the final 12-stage battery is green; catalog approval remains a separate maintainer decision.

## Proposed native parametric family

`workspace/parametric/` adds `rank_basis=cells|components_then_cells`: the exact
canonical default or lexicographic four-connected component count/cell count.
Both settings preserve whole block textures and use matched 11×11 demonstrations.
The alternate extends queries through substantive 30×30 grids with nine 9×9 blocks.
Stable prefixes support 2–6 demonstrations and four novel sequential queries.

The current proposal passes 82 focused tests, a 326-evaluation protected Racket
audit against sixteen extra finite rivals, and native qualification on two seeds
per setting. Two protected causal witnesses independently replay with 24 and 244
changed output cells. Reusable audit/export tools and an incremental eight-neighbor
teaching-hole reproducer are included. These are bounded reviewer results;
owner exact-source acceptance and training admission remain separate.
