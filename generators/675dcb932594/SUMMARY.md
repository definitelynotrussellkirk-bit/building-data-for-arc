# 675dcb932594 — all shortest maze paths

Version **2.0.0**. Recolor to 8 exactly the color-0 cells on any unit-cost cardinal
shortest path between the unique color-2 start and color-3 goal. Preserve all
other cells and dimensions. Color 5 is the wall; symbolic colors are fixed.
Canonical rule hash: `1e4fa5a56660`; canonical rule and labels are unchanged.

Default inputs alternate equal-length route tradeoffs with irregular mazes.
The tradeoffs distinguish orientation-weighted path costs, endpoint shortcuts,
single-path and intersection rules, and broader region-painting rivals. Default
lessons use **four demonstrations plus one query**, with a period-2 semantic
schedule and query-rotation support against the finite declared rival set.
The review measured 300 production lessons and 1,500 rotations with no ambiguity.

Exact controls: `grid_h` and `grid_w`, Python integers **5..24** in every band.
Removed legacy controls are rejected. Dimensions of 5 use the generic maze
fallback and do not carry the default lesson guarantee. Half the default size
mixture uses canonical shapes in each band. All grids have a color-5 frame and
connected endpoints with at least one intervening open cell.

See `notes.md` for decisions and limits, `workspace/README.md` for the reusable
source-bound diagnostic, and `counterexamples/step_cost_tradeoff.json` for an
exact generated counterexample with a public Racket receipt. The task-local
regression and probe tests total 191 passing cases in the isolated review run.
Approval is derived by the catalog from current code and retained evidence;
these checks do not themselves admit training data.
