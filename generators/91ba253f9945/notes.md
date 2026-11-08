# Working notes: 91ba253f9945

## Current decision

The previous generator was unrelated to the canonical task: it emitted horizontal motif panels separated by color 9. It has been replaced with the actual two-frame domain. Ordinary inputs now contain one orthogonal 2/3/4 source tripod, one 5/6/7 target tripod, both source-local marker colors 8 and 9, varied frame orientations, irrelevant 8/9 decoys, and spatially spread color-1 distractors.

The native family exposes one episode-fixed parameter, `turn`:

- `counterclockwise` is the exact canonical Racket source, byte-for-byte.
- `clockwise` changes only the local map from `(u,v) -> (-v,u)` to `(u,v) -> (v,-u)`.

Inputs are matched across settings. The sampler supports 2–6 demonstrations and 1–4 returned queries, always constructs a four-query bank, and includes 11×15 and substantive 30×30 query boundaries.

## Causal structure

Step A identifies the 2/3/4 basis and creates an input-dependent sorted list of local `(u,v,color)` marker records, then applies the episode turn. Step B maps those records through the 5/6/7 target basis and paints the result. The retained protected-Racket witness replaces source-basis projection with raw row/column deltas on a qualified case; that wrong intermediate changes the final grid.

## Adversarial repair

The first audit implementation only aggregated shortcut rejection across episodes. A focused regression exposed that weakness before return, so the probe now checks each episode for a wrong rule that fits every visible demonstration yet changes a query. A later final review found a second, more serious bypass: the sampler recycled only six marker motifs and reused training motifs in the queries. That finite-template leak was removed; motifs are now sampled freshly per seed/split/index, every demonstration/query motif in an episode is distinct, and a retained `legacy_six_motif_lookup` rival directly guards the regression. The final bounded probe also covers opposite/absent/half turns, one-color and one-marker rules, raw-grid coordinates, ignored target orientation, nearest-only selection, and first-demo memorization. No named shortcut survived the retained seeds/count corners, but this is not a universal uniqueness proof.

## Evidence and limits

Task tests, sampler audit, authoring preflight, sequential projection, first-turn privacy, and causal replay all pass on the final source. The preflight uses protected Racket but is explicitly not owner qualification. Owner source review, native qualification/acceptance, and any training admission remain pending; no approval flag was edited.
