# Solve work log

## Exposure declaration

Before `solve_episode.py prepare`, I had already inspected this task’s generator and selected rule as part of the required generator review. This is therefore **earlier rule exposure: yes**, not a blind solve. After preparation I used only `solve/challenge.json`, this work log, my own Python code, and visible-only checker feedback; I did not reopen the generator, Racket source, reference solution, or private labels.

## Visible observations

- Training example 1 has two closed same-color outlines; every zero inside each outline changes to that outline’s color.
- Training example 2 is the important negative control. The upper color-6 outline has a wall gap and remains unchanged, while the lower closed color-2 outline fills.
- Training example 3 has a mostly rectangular color-9 wall with an outward cell on the right. The enclosed center fills, but zeros in the extra bounding-box strip remain zero.

## Hypotheses and probes

1. **Fill every object bounding box.** Rejected from the visible examples: it would fill the leaking color-6 outline in training example 2 and the exterior cells beside the color-9 spur in training example 3.
2. **Fill only zeros enclosed by each same-color connected component.** Operational probe: crop to a component’s bounding box, flood-fill non-component cells reachable from the crop border, and fill the remaining zero cells with the component color. This predicts both closed rectangles, preserves the open rectangle, and handles the spurred object without painting its exterior bbox strip.

## Implementation choice

`solution.py` finds 4-connected same-color nonzero components. For each component it performs the bbox-border flood fill described above and paints only original zero cells that are not exterior-reachable. Existing nonzero cells are always preserved.

## Remaining uncertainty

The visible episode has separated single-color components and no nesting or mixed-color walls. The implementation follows the simplest component-local rule supported by all three demonstrations; those absent cases are not needed to distinguish the two test inputs.
