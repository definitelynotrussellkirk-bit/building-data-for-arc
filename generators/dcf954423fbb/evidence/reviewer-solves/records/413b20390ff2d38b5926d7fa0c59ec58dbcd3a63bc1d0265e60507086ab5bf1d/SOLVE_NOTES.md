# Solve notes

Prior exposure: yes. I reviewed this task's generator before this required
visible-only episode, but did not consult the generator, Racket rule, reference
solutions, private labels, or prior solution notes after preparing this episode.

## Visible-example hypothesis

Treat color-1 cells as 4-connected components. Recolor an entire component from
1 to 2 exactly when at least one of its cells lies on the outer grid border.
Preserve interior color-1 components, background 0, and the unrelated 7/9
objects.

Evidence from the three visible pairs:

- Pair 1 recolors the top-touching and left-touching components while preserving
  the lower interior component.
- Pair 2 recolors components touching left, right, and bottom, while preserving
  the small component one column from the left edge.
- Pair 3 recolors a left-touching component and a bottom-touching component,
  while preserving isolated/interior blue components.

I implemented a direct 4-neighbor component traversal. One ordinary solve
revision is sufficient if it reproduces all visible outputs.
