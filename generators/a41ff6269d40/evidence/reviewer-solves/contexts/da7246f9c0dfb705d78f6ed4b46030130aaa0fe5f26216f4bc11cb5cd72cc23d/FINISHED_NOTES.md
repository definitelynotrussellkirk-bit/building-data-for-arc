# Solve notes

This is a human-readable work log, not a hidden model trace.  I had already seen
the selected rule while repairing the generator, so this is an exposed
post-repair solve; I did not consult the generator, Racket source, reference
answers, or private labels after `solve prepare`.

Visible-example hypothesis:

1. The connected color-4 object is the source template; normalize it to its
   top-left bounding-box corner.
2. Colors 1, 2, and 3 are top-left stamp origins.
3. Color 1 stamps the normalized template unchanged.
4. Color 2 stamps its left-right reflection.
5. Color 3 stamps its up-down reflection.
6. Start from a blank grid of the input dimensions; remove the source and anchor
   cells, retaining only the color-4 copies.

Cross-checks from the visible examples:

- Train 0's source has offsets `(0,1),(1,1),(2,0),(2,1)`.  At the color-1
  origin `(7,10)`, those exact offsets reproduce the lower-right output copy.
- Reflecting those offsets left-right at color 2 `(3,8)` reproduces the middle
  copy, while reflecting them up-down at color 3 `(0,2)` reproduces the top
  copy.
- Train 1 has two color-2 origins; both receive the same horizontal reflection,
  while its color-1 and color-3 copies distinguish the other mappings.
- Train 2 uses a different asymmetric template and again distinguishes all
  three transforms.

Implementation normalizes the source template once, constructs the three
transforms, and stamps each anchor on a blank output.  A bounds guard is retained
although every visible generated stamp appears to fit.
