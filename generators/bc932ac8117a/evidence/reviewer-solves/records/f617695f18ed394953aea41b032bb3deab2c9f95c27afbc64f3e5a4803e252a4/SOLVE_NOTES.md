# Solve notes

I used only the three visible input/output examples in `solve/README.md` for this final-source episode. I had earlier rule exposure from repairing the generator, so this is explicitly not blind.

Hypothesis from visible examples: there are two same-bounding-box colored objects. One object contains enclosed background regions; the other is solid. Copy every enclosed zero region from the hollow object's local bounding-box coordinates into the solid object, changing those target cells to zero. Object left/right order is irrelevant.

Implementation plan: extract monochromatic 4-connected components, flood-fill zero regions inside each component's bounding box, identify the unique component with enclosed regions and a same-shape component without them, then carve all corresponding local cells from the solid twin.
