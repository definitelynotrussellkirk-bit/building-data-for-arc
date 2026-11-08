# Aligned-segment length normalization

The input contains an odd number of parallel, one-cell-thick straight segments.
Exactly one endpoint from every segment lies on a common perpendicular guide.
Order those aligned anchors along the guide. The canonical setting takes the
length of the positional middle segment; the alternative takes the longest
length. Every segment is then redrawn from its original aligned endpoint using
the selected target length, preserving its color.

Step A detects the common anchor side, orders the segments, and derives the
reference length. Step B consumes that scalar and redraws all segments. The
native adapter emits matched input streams for both settings, supports 2–6
labelled demonstrations and 1–4 private queries, and includes two 30×30 scenes.
