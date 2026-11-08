# fe4e4cc0157f

0-bg grid with 2-5 4-connected non-bg objects, each a distinct color and a DISTINCT number of interior holes (so the most-holes pick is unambiguous). Objects are solid rectangles of varied size with k single-cell interior holes punched (each hole fully enclosed and separated so it is its own bg component). Objects are non-touching. Rule: count each object's interior holes (bg components inside the bbox padded by 1 that don't touch the padded border); pick the object with the MOST holes (tiebreak size DESC, then top-row, then left-col) and OUTPUT its bbox crop.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
