# Row recoloring and largest resulting component

This native reviewer prototype preserves the exact canonical `row` program and
adds `largest`: recolor row markers, then recompute components of the changed
grid and render the largest component alone. It is separate from the production
generator and its existing approval. Reviewer readiness is not owner acceptance
or training admission.

## Complete shared grammar

Both settings admit every built-in rectangular list of nonempty built-in lists
with axes in 1..30 and exact integer colors 0..9. Booleans and floating values are
rejected. No shape, marker, header, palette, count or uniqueness restrictions are
imposed. This includes all original canonical examples, empty foreground,
one-column grids, color-8 headers, ties, holes and arbitrary body clutter.

`row` replaces an 8 at column c>0 by its row's first-cell color when that header
is nonzero. All other cells, including the header and headerless 8s, stay intact.

`largest` executes that same operation first. On the resulting grid, find
same-color, nonzero, four-connected components and select greatest occupied
area. Size ties use the lexicographically smallest actual occupied coordinate
(topmost row, then leftmost occupied cell in that row), not the independently
minimal row and column of a bounding box. Render only the selected component in
its own color in a tight bounding box; other colors and disconnected same-color
cells inside that box become zero. Empty foreground produces `[[0]]`.

## Causal dependency

A materializes the row-recolored intermediate grid. B decomposes this changed
state, chooses its largest component, and renders that selected membership.
Changing 8s to their row colors can join previously disconnected cells; it can
also break a color-8 component when different row headers apply. Thus B cannot
reuse the original component partition. The first core changes the winning
component's color and size; the second breaks the original 8 component and
requires the explicit tie rule. A protected skip-A witness keeps B byte-identical
while supplying the original input as its intermediate. Executed stage and
selected-component values accompany the full-label replay.

The `row` program is copied byte-for-byte from the current public Catalog:
237 bytes, SHA256 `071b2a298d5c565c469357c6b6662d4fe94ec5e123bbe48fa36861d8e40691df`.
The production rule hash `1130750019d1` identifies the normalized authority; it
is a different hash convention. The alternative embeds the exact canonical
expression inside its stage binding. Production, shared code and authorities
remain separate.

## Episode construction and counts

Seeds are exact integers in 0..2**63-1. Independent exact count controls allow
2..6 demonstrations (ordinary default 3) and 1..4 queries (default 4). The native
contract's omitted ordinary demo count is 3; qualification explicitly uses the
smallest supported count, 2 demos and 4 queries. No long teaching tail is needed.

Settings are fixed per episode: `{"mode":"row"}` is the canonical default,
and `{"mode":"largest"}` is the composed alternative. An omitted setting
uses its own deterministic SHA256-derived stream. Explicit settings share
identical inputs. Separate demo/query streams build complete six/four banks
before slicing. Query roles are seed-shuffled before any requested prefix is
selected; the public exporter separately shuffles presentation order.

The first two demonstrations are constructive lesson cores, source-derived
from the current independent design probe. They do not rely on the production
five-step sample-index schedule or on rejection against query answers.

- Core 0 is 15x17: row recoloring merges a 23-cell component, overtaking the
  original 16-cell winner. A larger bounding-box foil, more frequent fragmented
  color, diagonal attachment, disconnected same-color cells, interior clutter,
  multiple markers and protected headerless markers distinguish nearby rules.
  Three non-8 colors and vertical orientation vary with the seed.
- Core 1 is 14x18: recoloring breaks a 21-cell 8 component. The resulting three
  maximal components have 16 cells each and colors below 8, 8 and 9. The 8 frame's
  occupied anchor wins, exposing headerless-marker preservation, tie order,
  numeric-color shortcuts, diagonal connectivity and clutter-preserving crops.
  The two low non-marker colors vary while the tie-order contrasts remain.

Additional demos are 1x1, 6x9, 21x26 and 30x30. Four queries cover 4x7, 14x19,
23x27 and 30x30 in a seed-dependent order. Their small scenes vary keys, markers,
clutter and connectivity. Larger scenes join a checkerboard of keys/markers into
a comb while a dense competing-color field remains fragmented. Tooth rows are
balanced across both vertical halves; a solid competing patch changes the
original winner. Both horizontal halves and all four quadrants contain real
content. The 30x30 demo/query have respectively 630/619 occupied input cells and
180/169 cells in the merged comb. Different tooth counts guarantee these two
same-size inputs are distinct; the remaining bank members have distinct sizes.

## Evidence and limits

The independent audit authors complete Python/Racket rivals for row-local
semantics, stage order, connectivity, component/color selection, tie handling
and rendering. It fits only the first two demos, freezes all survivors, then
scores each survivor on all four private queries. It also checks all six/four
intended labels at its finite seeds. Literal tests cover zero/one-column inputs,
occupied-anchor ties, scope and failure-ledger behavior. Exact source/runtime
closure, all executed candidate programs, and retained failed attempts accompany
the bounded report.

The native source manifest binds implementation, contract, audit, focused tests
and retained evidence. Qualification and causal replay use the protected current
Racket runtime; serialized preview checks add no new Racket claim. Public turns
contain demonstrations and one query, with programs, settings, answers, source
indices and future queries retained privately by the consumer.

Finite seeds and a finite rival set do not prove uniqueness against every
possible program or measure training gain. The original production schedule's
two inherited sharding findings remain `needs_triage`; this episode-level native
design does not silently close those separate production findings.
