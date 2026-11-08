# Final-source visible-only solve: 95524d104174

Earlier exposure: yes, from the generator repair and an earlier post-repair
solve. Reference consulted during this episode: no. This is not a blind solve.
The earlier source-bound finished episode is preserved under checks/prior-solve/;
this newly prepared challenge is bound to the final caller-validation repair.
I inspected only this episode's visible preparation/challenge while solving.

The visible examples preserve dimensions: 12 by 12, 4 by 7, and 5 by 4.
Each contains one completely occupied row and one completely occupied column.
Their crossings are (5,10), (2,4), and (3,2), respectively, using zero-based
coordinates. All eight neighboring positions become yellow (4); the original
center value and cells outside that local square remain unchanged. The first
example has a horizontal-color center while the other two have vertical-color
centers. The second example preserves center 1 despite color 9 being more
frequent, so a frequency-based replacement would contradict a demonstration.

Revision 1 locates the crossing by nonzero occupancy, paints the neighboring
ring, and preserves its center. It makes no assumption that both lines are
uniform at their intersection. This is the only attempt on this challenge;
there are no manufactured negative revisions. The query inputs measure
11 by 7 and 6 by 6; their outputs and correctness remain withheld.
