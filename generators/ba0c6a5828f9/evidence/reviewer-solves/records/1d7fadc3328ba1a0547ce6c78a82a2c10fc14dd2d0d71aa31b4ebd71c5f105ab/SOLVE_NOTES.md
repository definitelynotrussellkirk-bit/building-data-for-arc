# Post-repair visible-only solve notes

## Hypothesis

Across the three visible demonstrations, the lone red `2` is an anchor rather
than an object to transform. Each blue `1` is copied to the other quarter-turn
positions around that red cell. The first and third demonstrations use an
off-center red anchor, so using the geometric canvas center is ruled out. Some
rotated positions fall beyond rectangular borders; visible in-bounds copies are
still added, so clipping is per destination rather than rejecting the whole
orbit.

## Implementation

1. Locate the unique red pivot `(pr, pc)`.
2. Snapshot all blue source cells from the input.
3. For each displacement `(dr, dc)`, enumerate
   `(dr,dc), (dc,-dr), (-dr,-dc), (-dc,dr)`.
4. Paint each in-bounds destination blue on a fresh copy of the input.

This is one hypothesis and one implementation revision. I stopped after it
matched every visible demonstration. I did not consult the Racket source,
generator source, reference solution, or private query labels during this solve.
I had earlier rule exposure from the required generator-review phase and will
record that honestly when finishing the episode.
