# 7b6758552009 — one palette entry per component

A zero-background input contains separated, monochromatic, 4-connected blobs.
The output is one row: one color per component, sorted by minimum column and
then minimum row. Disconnected components of the same color remain separate
output entries. Production labels come from the unchanged canonical Racket
program, rule hash `8afe6f5b77dd`.

Selected generator version: **3.0.0** (reviewed from 2.1.1). Ordinary sampling
uses 2–5 components, 1–5 cells per blob, height 6–12 and width 10–18. Every four
consecutive indices at a fixed seed cover randomized canonical-scale scenes,
repeated colors, same-left-column ties and crossing horizontal spans. Use four
training demonstrations for the tested lesson contract. Explicit overrides can
replace scheduled choices and therefore do not inherit that contract.

Supported axes: `grid_h`, `grid_w`, `components`, `color_policy`, `layout`.
Only advertised values are accepted; formerly ignored axes now raise errors.
See `workspace/README.md` for exact bounds, tests and replay commands.

Approval is derived by the catalog from current code and retained evidence.
This review does not grant approval: generated research examples retain
`approved=false` and `train_safety=unverified`.
