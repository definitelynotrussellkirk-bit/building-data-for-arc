# cf787ae40567

Treat every nonzero input cell as a seed. Grow each seed to the clipped orthogonal plus containing its center and four cardinal neighbors, take the **set union** of all grown cells, and output one row of color 8 whose width is the union cardinality.

The version 2.0.0 teaching distribution cycles through four observable profiles in every four-example window:

- `canonical`: public-like 7×7, 8×8, or 9×9 inputs with one to three separated interior color-2 seeds;
- `overlap`: interior plus masks overlap, forcing union/deduplication;
- `edge`: one or more seeds are clipped by the boundary, forcing clipping rather than five cells per seed;
- `mixed`: both clipping and overlap are present.

The ordinary sampler exhausts the finite 24-width teaching codomain `5..28`. The canonical Racket program was not changed; `RULE_HASH = "5d3366b26415"` pins the selected authority.

Kind: `per_puzzle`. Reviewed version: `2.0.0`. Final generator SHA-256: `a9c8dfbccf9b4603946e6f91d7a8722eb771f064a7d21cdcdb43ad39f16e05da`.
