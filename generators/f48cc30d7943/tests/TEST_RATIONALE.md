# Focused regression scope

These tests were authored before changing the selected generator, against source
SHA-256 `31b6a227823454591901f3f019f3e47e1d71f020b2a6ccd03140a14cabda584d`.
They are task-local tests, and use no sibling source or private runner API.
`reviewer_support.find_root(__file__)` binds the exact canonical data to the
current library or staged runtime. The generator is imported under a unique
module name; no test uses a relative import that depends on pytest's import mode.

## Independent expectations

The reference fixture contains 36 exact labels from the current public Racket
execution evidence: 30 miniature semantic cases and six baseline generated
inputs. Its source report hashes are embedded in the fixture. All five canonical
pairs are read separately through `reviewer_support.canonical_pairs`. The local
flood-fill oracle is checked against all 41 labels; labels for generated lesson
tests then come from that independently validated oracle, not from the subject's
own transformation helper. This finite cross-check does not claim a formal proof
of reference equivalence or a fresh Racket run for every generated test grid.

The reference cases establish finite-grid four-connectivity through every color
except 5; individual red-cell counting; exact equality to two; replacement of
original zeros only; and preservation of every original nonzero color, including
8. They include diagonal contacts, articulation bridges, bent chambers, foreign
red/zero cells inside a chamber's bounding box, adjacent red cells, high-count
negatives, a long corridor, open regions, and lawful inputs with no visible edit.

The rule validator and teaching self-check deliberately have different tests.
The rule validator accepts rectangular list-of-list grids of exact integer
digits, each dimension 1 through 30. Teaching examples additionally require at
least two non-5 components, a component with exactly two red cells and an original
zero, and a component with a different red count and an original zero. No test
requires teaching chambers to be rectangular or fully enclosed, restricts their
palette to 0/2/5, or caps negative red counts at three.

## Controls and distribution

The public controls are exactly `grid_h` (7..26) and `grid_w` (7..28). The exhaustive
joint loop performs 20 × 22 × 4 = **1,760 draws**, one for each legal size pair in
each accepted difficulty band (`None`, easy, medium, hard). Its sample index
varies across all three schedule residues. It accumulates failures and completes
every combination within each band, rather than stopping at the first mismatch.
A separate loop covers eight endpoint/interior size pairs in every residue and
band, adding 8 × 3 × 4 = **96 draws**. Small explicitly sized grids carry no
universal diagnostic-witness requirement.

Other control tests reject booleans, floating-point and string coercions,
out-of-range values, unknown controls including unknown `None`, and unsupported
difficulties. Known dimension controls set to `None` must act as omission.
Repeated seeds/indices, global random state, row independence, control-dictionary
preservation, and returned-grid mutation isolation are tested directly.

The period-three distribution checks distinguish framed room samples at residue
zero from rich topology at residues one and two. Framed samples have dimensions
10..12, complete gray frames, 2..9 rectangular rooms, and 0..3 red cells per room;
a finite sample must include strict canonical support. The strict hook must
accept all five canonical inputs and reject tested departures from the framed
four-room canonical grammar. Rich defaults have dimensions at least 12 in both
directions, visible one/four/five-red negatives, an open positive chamber, an
enclosed nonrectangular positive chamber, adjacent red seeds, an original cyan
cell, an observable non-cyan articulation bridge, bbox decoys, and a zero more
than eight Manhattan steps from either red seed.

## Rival and lesson assertions

Independent literal alternatives cover full-line partitions, bounding-box
painting/counting, eight-connectivity, zero/red-only traversal, every-mark seed
counting, painting nonwall nonred cells, rectangles-only filling, positive-even
counts, two modulo three, two-or-at-least-four, radius-eight filling, enclosure,
eight-as-wall, and counting red plus cyan. Secondary alternatives count red
objects, accept at least two reds, or accept one or two reds.

Inventory checks compare actual callable predictions, not a frozen list of
declaration names or source text. Every declared canonical shortcut must fit all
five exact canonical pairs. Rich default samples must independently refute both
the literal alternatives and every rival currently declared in any of the three
registries. Thus additional declared rivals are automatically exercised.
Witness firings are checked against their named rival predictions on the supplied
grid; a witness name alone is never treated as evidence.

Every single-query holdout of every four-draw window in a finite census is
checked. The census uses 3 seeds × 4 bands × 9 starts × 4 holdouts = **432 labeled
lesson checks**. It scores actual rival outputs against the supplied labels and
checks the lesson hook separately. An additional relabeling test supplies
rival-consistent demonstration outputs and a contradicting query label, then
an identical query pair; it detects hooks that silently relabel their inputs.
These tests are finite evidence against declared alternatives, not a proof of
universal identifiability.

The independent review subsequently found a generated lesson admitting the
nearby-red-pair alternative (Manhattan separation <=8). The final test revision
adds literal nearby-pair, boundary-activation, and rectangle/otherwise-open-or-
thick shape alternatives, plus positive widely separated reds and negative open
and thick nonrectangular geometry. This strengthened suite retained the same
199 collected cases: it gave 186 passes and 13 real failures on intermediate
source 18bd71cc3610ac4e5b34966295780d68fd89d75e36eebb6eda36a468a14fb29f,
then 199 passes on the final source. The original baseline RED result was 45 passes
and 154 failures. Both RED results had zero collection errors or skips.

## Expected red behavior

The baseline advertises several ignored controls and does not honor exact size
overrides. It accepts unsupported difficulty values and restricts its self-check
to rectangular rooms, the 0/2/5 palette, and counts at most three. It lacks the
rule-grid, observer, canonical-profile, rival, witness, and lesson APIs. Focused
tests are expected to fail on those behaviors before implementation. Missing
APIs are assertion failures inside collected tests, not import-time failures.

The final source defines **22 unique test functions** and **200 parametrized
test cases**, including the exact seed-31 lesson regression added after the
199-case strengthening run. There are no additional collected frozen fixtures. The public stage's
JUnit receipt is the authority for observed collection/pass/failure/error/skip
counts. Loop draws and lesson checks above are internal cases, not additional
pytest test functions or JUnit test cases.
