# Solve notes

The top row behaves as a legend rather than part of the body. Its number of blue
cells varies across the three demonstrations: 2, 2, then 3.

I grouped each nonzero body colour into 4-connected components. Two different
components are graph-neighbours when they touch along an edge. In training pair
1 the selected central block has two neighbours; in pair 2 the selected singleton
also has two neighbours even though another component has higher degree; in pair
3 the selected 2x2 block has three neighbours. This rules out selecting the
largest component, selecting a fixed colour, or simply selecting maximum degree.

Hypothesis: count the blue legend cells to get k, then output in colour 8 every
body component whose contact-graph degree is exactly k, erasing the legend and
all other body cells. The implementation uses an independent flood fill and
pairwise cardinal-contact test.
