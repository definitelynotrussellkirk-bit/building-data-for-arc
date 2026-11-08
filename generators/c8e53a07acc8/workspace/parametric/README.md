# Anchor-size parametric connector prototype

**Status:** proposed, source-bound authoring artifact; not owner-accepted or training-admitted.

The episode-fixed `anchor_size_relation` is either `same_count` (the exact
canonical default) or `one_extra`. Both preserve the original task's complete
8-connected component discovery, multi-template iteration, anchor-pattern
alignment, fragment stamping, and unique-source-cell erasure. Every input
contains both a same-count and a one-cell-larger same-color standalone object
for every template. The hidden setting therefore selects which candidate
receives the fragment without leaking through input construction.

Demonstration counts 2 through 6 are supported. Every episode has exactly four
distinct controller-side queries; the fourth is a 30×30 boundary-touching,
three-template case. `public_turn()` exposes demonstrations and only the current
query input. The CLI validates every retained label with protected Racket before
writing first-turn public bytes and controller-private episodes.
