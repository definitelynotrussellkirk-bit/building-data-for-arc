# Post-repair visible-only solve notes

I had already read the selected generator and canonical rule during the required repair phase, so this is **not blind** and I will record `earlier-exposure yes`. During this solve episode I used only the displayed train/query grids and did not reopen the generator, Racket source, private labels, or earlier solution explanations.

## Visible hypothesis

- Color `2` is a border emitter.
- The beam starts inward. At a corner, the visible top-corner examples imply top/bottom precedence, so a top corner starts downward.
- Each traversed `0` becomes `7`.
- Color `8` is an opaque stop.
- Color `4` and `5` are handed mirrors:
  - `4`: `(dr, dc) -> (-dc, -dr)`
  - `5`: `(dr, dc) -> (dc, dr)`
- Mirrors, wall, and emitter remain unchanged; exiting the grid also stops the beam.

## Checks against visible demonstrations

Example 0 starts at the top-right corner, travels down, reflects left at `4`, then up at `5`, and stops before `8`; all ten shown trail cells follow that path. Example 1 confirms both mirror handednesses without a wall. Example 2 confirms one reflection followed by a wall. Example 3 confirms one reflection followed by a boundary exit.

The two queries exercise an off-route mirror/wall case and a corner/two-mirror/active-wall case. The generic trace handles both without query-specific branches.
