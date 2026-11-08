# bf45cf4b native family

`pocket_policy=repeat|largest_enclosed`. The default source is byte-identical
between this folder's `canonical.rkt` and the task's `reference.rkt`. The native
folder can be relocated without its parent. Generation reads no official data.

Canonical: infer the unique modal background; distinguish the monochrome mask
from the multicolor tile by their palettes; crop both and substitute the tile for
each marked mask cell. Background mask cells become blank tile-sized blocks.
The generated mask and tile are separate 8-connected nonbackground objects.
The product of their respective dimensions never exceeds 30x30.

Alternative: derive the assembled mosaic's 4-connected background regions,
reject every boundary-connected region, and fill only the unique largest pocket
with the original mask color. The original background is retained throughout;
its frequency in the output need not be modal.

The tile's one-sided openings join neighboring blank macro cells. In the 30x30
stress case, equal two-cell mask holes produce 62- and 74-cell pockets, because
they join one versus two 12-cell channels. The first lesson has three equal-area
mask holes with a middle, uniquely larger assembled pocket. The second has
macro-hole areas 1, 2 and 3. Remaining slots vary mask holes, tile dimensions,
colors, placements and D4 orientation. This is a constructive subgrammar, not an
exhaustive sampler of every possible mask or tile topology. Shared/missing
objects and nonunique modal backgrounds are not generated.

2–6 demonstrations and 1–4 queries are independent. All four query slots are
privately shuffled before taking a prefix. Public turns whitelist demonstration
input/output and only the current query input; no parameters, total count,
future inputs, code or answers appear.

From the packet WORK directory, with a new output path:

```
python run_with_racket.py python generators/public_eval_bf45cf4b/workspace/parametric/audit.py --seeds 20 --out ../checks/public_eval_bf45cf4b/new-audit
```

The audit runs exact Racket hypotheses against an independent Python predictor,
checks all request-count prefixes, matched inputs and public masking, and writes
content-addressed public views in hash order. Source-bound preflight and causal
replay remain authoring evidence. Owner registration, native qualification and
fresh acceptance are separate; training_admitted=false.
