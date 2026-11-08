# Post-repair visible-only solve notes

## Exposure record

I had already inspected the assigned generator and canonical rule while repairing it, so this is **not blind**. During this solve episode I kept the generator, Racket source, reference solutions, private labels, and earlier explanations closed. The hypothesis below was re-derived from the three visible input/output examples.

## Observations and hypothesis

Every input has a full-height gray(5) vertical divider and one colored connected object on each side. Output color is always cyan(8), and output height equals the larger of the two object bounding-box heights rather than the input height.

For each object I counted occupied cells row by row after conceptually cropping to that object's own bounding box:

- Example 0: left profile `[3,2,3,1,3]`; right profile `[3,5,4]`. Padding the right with zeros gives absolute differences `[0,3,1,1,3]`, exactly the five output row lengths.
- Example 1: profiles `[5,2,4,4]` and `[3,2,2,2]`; absolute differences are `[2,0,2,2]`, exactly the output.
- Example 2 is the decisive alignment probe because the objects occupy different canvas rows. Their local profiles are `[4,2,4]` and `[5,5,4]`; absolute differences are `[1,3,0]`, exactly the output. Thus profiles align by local object-row index, not absolute canvas row.

Hypothesis: select the object in each panel, form each object's local row-count profile, pad the shorter profile at the bottom with zeros, take elementwise absolute differences, and render those counts as left-justified cyan bars.

## Query predictions used to sanity-check the implementation

- Query 0 profiles: left `[4,2,2]`, right `[1,4,3,1]`; padded difference `[3,2,1,1]`. Predicted output rows have lengths 3, 2, 1, 1.
- Query 1 profiles: left `[5,2,4,3,4]`, right `[4,4]`; padded difference `[1,2,4,3,4]`. Predicted output rows have lengths 1, 2, 4, 3, 4.

I implemented monochrome 4-connected component extraction and choose the largest component in each panel, then apply the inferred profile rule. No alternate hypothesis survived all three visible examples, especially the staggered third example.
