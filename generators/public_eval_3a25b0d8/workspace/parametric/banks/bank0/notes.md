# Public parent 3a25b0d8: deformed enclosed-region correspondence

The general rule finds two eight-connected non-background figures. Exactly one
contains only the shared outline color; it is the target. The other is the
colored guide. Isolate the component cells BEFORE cropping: original train[0]
has overlapping figure bounding boxes. Within each isolated crop, find the
four-connected enclosed non-outline cavities and order them by bounding-box
center row, then center column (integer doubled coordinates). Transfer each
guide cavity's color to the corresponding target cavity; preserve the target
outline and exterior. All two original demonstrations and BOTH supplied test
answers have been reproduced by protected Racket, not a stored-grid lookup.

`transfer_scope=all` is byte-identical to reference.rkt. `expanded_only` first
computes the same ordered correspondence records, including source color and
occupied area, and fills only target cavities whose occupied-cell area is
strictly greater than their matched guide cavity. Equal-area cavities stay blank.
A reversed guide-record list is the protected wrong-intermediate causal foil.

The admitted synthetic grammar preserves this spatial correspondence, not an
arbitrary topological graph-matching claim. It varies background/outline colors,
seven-to-nine enclosed regions, repeated and distinct guide colors, one/two/three
regions per band, irregular notched cavities, independently deformed dimensions,
stepped exterior silhouettes, palette order, figure positions and orientations.
The minimum two demos deliberately expose different pixel-scan orders on the
guide and target. Initial tests found that target scan order could survive both
lessons; the first demo was repaired to have centered tall/short target regions.
Both independent scan shortcuts and simultaneous scanning now fail the lessons.

Every request has 2–6 demos and exactly four novel queries, with a query bank
independent of demo count. The final 30x30 source profile has distributed content,
boundary contact, and an exterior connected whisker causing figure bounding boxes
to overlap without joining the components. Its crop must still exclude the other
figure. Presentation shuffles the whole four-query bank before any prefix is
selected. One-query views strip all private fields and future queries.

The finite audit covers twelve declared policies, seeds 0..31 and counts 2/3/6.
Three area-condition rivals are exactly equivalent under `all`; their harmless
survival is reported rather than called unique identification. The Racket audit
also executes scan-order foils on the distinguishing demonstrations. This is
finite evidence, not universal uniqueness or measured training benefit.

Source is an unapproved public-evaluation-origin authoring build. Parent linkage
and all gold labels remain private. Owner registration, source review, native
qualification and separate acceptance are still required; training admission is
false. No shared catalog, canonical ledger, approval or runtime was edited.

Final portability review moved the geometry sampler into standalone generator.py.
A regression executes a relocated flat base module with no adjacent workspace;
the native layer resolves that base through reviewer_support and carries its
canonical Racket resource explicitly. No predecessor filesystem dependency.
