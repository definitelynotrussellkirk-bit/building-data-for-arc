# 779c7c31edc3 — solid rectangles to frames

Version `3.0.0`; canonical `RULE_HASH = 8f9e53b42241`. No Racket authority was changed.

The input has literal-zero background and 1–4 solid, monochrome rectangles, each
at least 3×3. A rectangle means a **monochrome 4-connected component**, not all
pixels of one color. Disconnected rectangles may share a color; different-color
rectangles may touch. The authoritative transform retains every component's
one-cell border and clears its interior.

Generation uses constructive, nonoverlapping slots, not a capped placement loop.
The only advertised exact controls are `grid_h` and `grid_w` (9–18), `rectangles`
(1–4), and `n_distinct_colors` (1–4). More colors than rectangles is an explicitly
declared incompatibility. Unknown and formerly inert controls now raise errors.
This is an intentional interface cleanup, not backward-compatible silent coercion.

Un-overridden sample indices cycle through three profiles: canonical-scale anchor,
repeated-color components, and broader scenes. The anchor uses a 12×12 canvas,
three distinct-color rectangles and a 5×3 component without replaying a stored
canonical grid. Other profiles provide varied counts, sizes, palettes, edge
contacts, and repeated colors. Difficulty changes the default size/count weights,
not the meaning or accepted range of explicit controls.

Executable rivals distinguish connectivity from color grouping, all rectangles
from only the largest, and full interior removal from erasing one center pixel.
`strict_canonical_like` checks the solid-rectangle rule domain; it is not a test
of exact canonical dimensions or literal-grid identity.

Evidence and runnable probes are described in `workspace/README.md`. The final
battery is all-green and extended lesson probes are retained in the review ZIP.
These finite tests do not confer training approval or prove universal induction.
