# Shape-specific frequency voting (public parent 67e490f4)

The reference selects the largest nonbackground connected object as the template. Each four-connected background hole is matched to external same-color eight-connected glyphs up to translation and all eight dihedral orientations, without scaling. Count **objects**, separately for each shape/color pair, not global color prevalence or pixels. Fill each hole with the most frequent matching color. Exact vote ties resolve to the smaller numeric color. All three supplied labelled pairs are reproduced by the general rule.

`vote_rule=most_frequent` is the exact authored default; `least_frequent` selects the rarest positive matching count instead. Shapes and input streams are identical across settings. A produces shape-conditioned color histograms; B selects and paints the output color. Replacing those histograms with global per-color counts changes the retained 30x30 query's answer, so the shape stage is causally necessary.

## Teaching repairs
The first random constructor let rotation-only and bounding-box-only rivals survive short lessons. Exact seed-3 and seed-5 pre-repair lessons were frozen and independently executed in protected Racket: each rival agrees with two demonstrations and differs by eight cells on its retained query. Frozen evidence includes programs and grids, so it remains replayable after sampler repair.

The repaired first demo contains plus and bent-L pentominoes with equal area/bbox but different unique vote winners, and chiral L-tetromino holes opposite every external exemplar's handedness. It therefore requires exact shape matching and reflection. Counts 3/1/2, 2/3/1, 1/2/3 avoid the initial shared-minority loophole. The second demo includes exact vote ties and different equal-area shapes. Two demos distinguish both settings and the declared harmful rivals without consulting query inputs or outputs. Harmless rival survivors are recorded, not called uniquely identified.

## Supported synthetic grammar
Three distinct shape classes, six template holes, three candidate colors per class; 18 or 15 separated external glyphs depending on the count profile. Shapes range from singletons/dominoes to chiral tetrominoes and pentominoes. Glyph colors are shared across classes, preventing a global-color shortcut. Random palettes include 0, random external placements and orientations, frame flips/transposition, and input sizes up to a distributed 30x30 boundary query. Template crop is 13x9 or 9x13; arbitrary hole counts/large glyphs are outside this constructor's admitted grammar even though the reference handles the supplied larger examples.

2–6 demos; exactly four distinct private queries, with query bank independent of demo count. Public presentation shuffles the complete query bank privately and reveals one query without total-count or future-input hints. Base generator is standalone and duplicated exactly as the adapter-local model to keep resource boundaries explicit.

## Status
Finite Python audit and protected Racket checks are separate evidence. Authoring preflight, task tests and causal replay do not constitute owner registration, native acceptance or training admission. No shared catalog or approval authority was edited.

## Current repeated-return reconciliation

Preserve exact most/least-frequent programs and canonical numeric-minimum vote ties. Port translation-only shape matching onto that parser and tie rule. Compatible incoming constructor banks are episode-level draws; incoming first-encounter/color-order tie behavior is explicitly excluded. Two visible lessons include targeted rarest-vote ties and separate the retained finite rivals. Original default bytes and labels remain unchanged. Evidence: `evidence/reconcile-15/`. Private native qualification, fresh native acceptance re-execution and bounded protected execution passed. Live publication and training admission remain separate.
