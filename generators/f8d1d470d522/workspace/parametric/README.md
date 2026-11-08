# Native `turn_preference` route family

This task-local family preserves the selected production generator and the exact
canonical Racket rule. It varies one episode-fixed decision only:

- `turn_preference = "fewest"` — canonical/default. Among legal shortest paths,
  choose the route with the fewest direction changes.
- `turn_preference = "most"` — alternative. Among legal shortest paths, choose
  the route with the most direction changes.

Both settings retain the original two color-9 endpoints, color-8 route network,
and the law that a color-8 cell cardinally adjacent to color 7 is disabled. The
selected path is then painted color 9. The default source in
`rules/turn_fewest.rkt` is byte-for-byte the catalog authority; the alternative
is one standalone `rule!` expression in `rules/turn_most.rkt`.

`adapter.py` supports 2–6 demonstrations and exactly four private queries. Input
sampling is setting-neutral and every ordinary demonstration is constructed so
the two settings produce different labels. The fourth query is a substantive
30×30 induced two-route corridor: both routes have equal length, while their turn
counts differ. Inputs are distinct and deterministic for a fixed request.

The required sequential dependency is:

1. **A:** enumerate legal shortest routes and apply the episode's turn objective.
2. **Intermediate:** the ordered input-derived path selected by A.
3. **B:** paint exactly the cells of that selected path color 9.

B cannot know which cells to paint without A. The qualification-bound witness
uses the opposite qualified turn objective as a wrong-intermediate ablation.

`self_audit.py` is a replayable bounded audit. It executes both retained programs
through protected Racket for settings `fewest`/`most`, seeds 0/17, demo counts
2/6, and all four queries; checks exact default identity, matched inputs,
determinism, setting identification, public redaction, 30×30 content, and five
cheap bypasses; and performs an additional 24-seed generation sweep. Its result
is retained under `evidence/current/` and inventoried by `evidence/manifest.json`.
Finite checks do not prove unique human induction or grant owner acceptance.
