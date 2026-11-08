# Solve notes

I used only the three visible input/output examples in `challenge.json`.

The color-2 object is unchanged in every example and acts as the reference.  For each
monochrome 4-connected object I recorded two visible properties:

1. whether any of its cells touches the outer grid border; and
2. whether its normalized bounding-box shape is invariant under top/bottom reflection
   and under left/right reflection.

The output recolors to 8 exactly the non-color-2 objects whose complete three-part
signature (border-touch, top/bottom symmetry, left/right symmetry) equals that of the
color-2 object.  The examples include useful near-misses: objects agreeing only on
border contact or only on reflection behavior remain unchanged.  The output dimensions
and all other cells are preserved.

Implementation: extract 4-connected same-color components, calculate the signature of
the unique color-2 component, then recolor each matching non-anchor component to 8.
