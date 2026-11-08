# Native endpoint connection family — 539d4ac45311

`connection_mode` is episode-fixed:

- `horizontal` is the exact selected canonical rule.
- `vertical` applies the same endpoint test within columns.
- `cascade` first performs the canonical horizontal pass, then performs the
  vertical pass on that completed intermediate grid.

The constructive two-demo minimum contains boundary-touching cascade rectangles
and a non-commuting crossing. The crossing makes horizontal→vertical differ from
vertical→horizontal: the first pass paints the crossing cell and blocks the
other axis. Four query profiles include 30×30 with six distributed cascade
blocks and a crossing, touching every boundary. Inputs match across settings;
2–6 demonstrations and 1–4 queries are independent prefixes of fixed banks.

Sequential dependency: A derives and paints every lawful horizontal span. The
intermediate is the resulting grid plus the set of newly painted cells. B scans
that exact grid for vertical endpoint spans; cells created by A can become B's
endpoints, while other cells created by A can block B. Skipping A changes the
qualified cascade label.
