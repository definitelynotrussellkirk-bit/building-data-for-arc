# public_eval_8f3a5a89 authoring notes

## Rule family

`contour=outer_only` is the canonical behavior. Starting at the unique color-6
seed, flood-fill through colors 8 and 6. Complement components that do not
reach the canvas border are enclosed holes. Fill those holes only for purposes
of deciding the region's outer contour, retain the seed and adjacent color-1
walls, erase unrelated outside material, and paint the outer contour color 7.

`contour=include_holes` uses the same flood-fill and rendering, but it leaves
enclosed holes outside the boundary domain. Their inner rims therefore receive
color 7 as well.

## Sequential dependency

Stage A computes the seed region, classifies complementary components as
exterior versus enclosed holes, and chooses the boundary domain. Stage B must
use that input-dependent domain to decide which region cells see the outside.
The retained counterfactual replaces the include-holes intermediate with the
canonical filled-hole domain and changes the final output.

The ordinary generator is self-contained; the adapter retains four private
queries and emits one source query at a time through `public_view`.
