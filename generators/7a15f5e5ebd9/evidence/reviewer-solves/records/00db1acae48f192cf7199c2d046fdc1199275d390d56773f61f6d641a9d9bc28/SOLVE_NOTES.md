# Solve notes

This is the required post-repair exposed solve. I had already inspected the task
family while repairing its generator, so this is **not blind**; I did not consult
the Racket source, generator source, private labels, or reference explanations
after `solve_episode.py prepare`.

## Visible-example derivation

- Each input has one maroon `9`, several yellow `4` cells around it, and one or
  more red `2` cells elsewhere.
- Measuring yellow coordinates relative to the `9` gives a template. In each
  visible output, the source scene disappears and that same relative template is
  translated to every `2` coordinate.
- The long/disconnected second and fourth examples rule out copying only a local
  component or a fixed shape.
- Cells translated outside the grid are simply absent; in-bounds cells remain.
- Red anchors are preserved in the output, so I stamp yellow copies and repaint
  every anchor red last.

Revision 1 implements that rule directly with bounds checks and no assumptions
about template connectivity, anchor count, direction, or grid dimensions.
