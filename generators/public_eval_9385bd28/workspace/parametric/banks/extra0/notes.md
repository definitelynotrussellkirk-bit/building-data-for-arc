# Current authoring work — 9385bd28

Unapproved public-evaluation family. Owner registration, approval, native
qualification and acceptance are not claimed.

## Design / implementation plan

Read the isolated vertical two-column legend as an ordered mapping from source
marker color to fill color; a background-valued entry is meaningful. Recover
rectangles from opposite, same-color three-cell L corners. Solid rectangles
instead recolor entirely. Process legend rows bottom-to-top so earlier rows
have higher painting priority. Own L markers are retained when their rectangle
is painted, but later higher-priority rectangles may overwrite them. Unmapped
objects and the legend itself remain as input. The alternative reverses the
priority without changing the input grammar or color interpretation.

A is legend/rectangle extraction; its intermediate contains ordered key/fill,
bounds and corner-marker cells. B composites those measured layers. A wrong
fill-code intermediate must change protected-Racket output.

Implementation sequence: independent literal-label tests first; general Python
and Racket rules; setting-blind constructive overlapping scenes and native
adapter; finite rivals and boundary repair if found; protected preflight,
source-bound causal replay, private/public exports, staged tests and relocation.
Only this assigned home is edited. Shared runtime/catalog remain untouched.

Review focus: nonblack background and black foreground; entries mapping to the
background; foreground priority that erases another object's markers; solid
blocks without L markers; unused mappings and unmapped objects.

## Zero-code correction from official labels

The nonblack-background training example distinguishes a literal black fill
from the scene background: two exposed cells must remain color 3, not 0. The
canonical decoder therefore interprets legend fill code 0 as the scene's
background. The original black-background inner rectangle must still erase a
lower painted layer, so zero cannot mean transparent compositing. The literal
zero is retained in the legend. This behavior has a focused failing-then-passing
regression in addition to the complete official-pair checks.

## Thin-rectangle curriculum repair

A protected rival that ignored bracketed rectangles only two cells thick fit
both old demonstrations but failed a novel 30x30 query with horizontal and
vertical thin strips: [true, true, false]. The second demonstration now includes
both kinds of thin rectangle; its horizontal strip has a visible nonbackground
fill outside other bounding boxes. Both source directions remain visible, and
the minimum stays two demos. See the retained teaching-gap-before.json and
test_minimum_lesson_teaches_thin_rectangles_before_queries.

The sampler also teaches zero-coded erasure of an unmapped interior block while
leaving another unmapped block outside the rectangles unchanged. It varies
backgrounds including nonblack, key colors including black where lawful, unused
legend entries, opposite corner diagonals, solid recoloring and row priorities.
The first two table orders oppose color-sorted shortcuts. Every four-query bank
is shuffled independently before selecting a shorter prefix.

Grammar limits: one opposite L pair per mapped color, or solid rectangular
components, an isolated vertical two-column legend with distinct keys, and a
unique modal background. Extra ambiguous legends and malformed Python inputs
are rejected. Racket is required total on the admitted grammar, not on all
arbitrary grids. Fill code zero means scene background; alternative priority is
a generative extension, not an additional claim about original labels.

Sampler diversity repair: a regression showed that colors varied but the first
lesson's legend position and rectangle geometry did not. The current sampler
independently varies legend row/column placement, rectangle spans and thin-strip
positions while preserving non-colliding glyphs and visible priority overlaps.
An initial broad audit process hit its 90-second tool bound without a receipt;
a fresh bounded run was completed. Timed-out work is not counted as evidence.

Final 32-seed sweep caught a further priority alias at seed 25 after geometry jitter: A and B both decoded to background, so numeric-key sorting fit both minimum demonstrations. The original `[true,true,false]` protected-Racket counterexample is retained in `checks/public_eval_9385bd28/priority-alias-before.json`. A now chooses only nonzero, nonbackground fill codes while B remains background-valued. A literal decoded-fill regression and the full 32-seed rival regression failed before the repair. The illustrative legend order is now visibly consequential rather than merely different metadata.
