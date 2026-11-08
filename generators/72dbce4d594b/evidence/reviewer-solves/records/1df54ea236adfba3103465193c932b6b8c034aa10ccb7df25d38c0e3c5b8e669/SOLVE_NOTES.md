# Fresh visible-example solve work log

This is a concise reviewer work log, not a captured model conversation, private
reasoning transcript, token-level trace, or log-probability record.

## Exposure and boundary

Earlier rule exposure: **yes**. I read the canonical rule, generator, and prior
notes during the generator review. This is not a blind solve. After preparing
this episode I used only `solve/challenge.json`, fresh Python code, visible-demo
outputs, and the visible-only checker. I did not reopen the generator, prior
solutions/explanations, Racket rule, or private labels during this solve phase.

## Visible probes

`visible_probe.py` independently extracts blue four-connected components from
the five visible demonstrations and tries eight geometric transformations.
`VISIBLE_FIT.json` records the results. Ascending area rank agrees with all five
output areas; descending area and reading order do not. The green-count table
has exactly one compatible transformation for every command: identity,
clockwise quarter-turn, half-turn, and left-right reflection. Absolute placement
matches the cyan bounding-box anchor. The first two demos leave the target cell
blank in the output, ruling out an assumption that the target must be painted.

## Revision 1

Implemented standalone `solve(grid)` with no runtime or data-file imports. It
uses the visible-fit table and returns a fresh grid. Descending-rank and
reading-order candidates were probe alternatives, not submitted solution
revisions. No intentionally wrong solution was submitted and no accidental
failed program revision has been fabricated.

The actual checker result is retained in `attempts/001/report.json` (or the
checker-generated numbered path). Masked-query correctness is withheld; an
executed query is not a scored correct query. Stop after a visible-clean,
structurally valid revision; maintainer scoring remains necessary.
