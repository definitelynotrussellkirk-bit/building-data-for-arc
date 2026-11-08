# Solve notes — exposed post-repair episode

I had already inspected the task rule while repairing the generator, so this is
not a blind solve. I did not consult the Racket source, generator, private
labels, or the archived earlier solve after preparing this final-hash episode.

From the visible pairs:

- Treat every 8-connected nonzero component independently, even when its color
  is not maroon and even when it is a singleton.
- Use the component bounding box. The green expansion radius is half of the
  longer bbox side, rounded down.
- Paint a blue vertical strip below the expanded box, with the original bbox
  width, beginning one row below the expanded halo.
- Paint the green expanded bbox ring after the stems, clipped to the canvas.
  Keep the bbox interior untouched, and do not paint green over cells that were
  maroon in the input.

Revision 1 implements that order directly. The non-maroon L-shape and singleton
examples are the key checks against color-only, rectangle-only, and
ignore-singleton interpretations.
