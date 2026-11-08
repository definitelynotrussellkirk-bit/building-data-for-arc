# Parametric quarter-turn interpretation — `6c2353a2cdee`

This family preserves the source task's exact three-panel extraction, transform,
overlay, and overlap-count encoding while varying one episode-fixed code map:

- `clockwise` is the byte-exact canonical Racket rule: code 2 is clockwise and
  code 4 is counter-clockwise.
- `counterclockwise` swaps those two quarter-turn meanings while leaving identity,
  180-degree rotation, and count encoding unchanged.

Inputs are matched across settings and have independent stable prefixes for 2–6
teaching examples and 1–4 queries.  The fourth query is a genuine 30×30 stress
case: the authoritative 7×17 panel grammar remains in its fixed coordinates while
more than 120 colored decoy cells occupy all four outer boundaries, testing that
panel/code extraction is not replaced by whole-grid heuristics.

The causal chain is panel/code extraction → three input-dependent transformed
5×5 supports → overlap counting and `1→2, 2→4, 3→8` rendering.  Swapping the
quarter-turn interpretation changes that intermediate and the protected-Racket
final output.
