# Blind solve — visible evidence only
No generator, reference rule, private labels, previous solutions, or audit evidence has been opened. The packet integrity checker/preparation tool handled private sources automatically.

Hypothesis: find four-connected monochrome nonzero objects, sort by number of occupied cells ascending, crop each to its own bounding box, top-align in a horizontal sequence separated by one background column. Preserve original colors and object orientation.

Evidence: example 0 has areas 2,3,5,6 in output order. Example 1 splits two disconnected objects of color 7 (areas 1 and 4), placing them around the area-2 color-8 and area-3 color-4 objects. Example 2 has areas 7,8,9; example 3 has 1,2,3. These distinguish component-based from color-based sorting and show top alignment despite unequal heights.

The examples do not establish a tie policy; use stable scan order for equal areas. Background is consistently 0. Both masked queries are handled by the same component rule. No masked-query correctness has been revealed.

Revision 1 is the first actual solution attempt; no deliberate negatives or artificial failed revisions were created. Stop if the visible-example check agrees on all four demonstrations and the masked queries execute.
