# Visible-only solve work log

This is a model-authored implementation/work log, not a captured token-level model
conversation, hidden reasoning transcript, or log-probability trace.
Earlier rule exposure: **yes**, during generator authoring. Reference, generator,
prior explanations and private labels were not consulted during this solve phase.
This is not a blind evaluation. The prepared challenge has three visible examples
and two masked queries; all experiments below use only those visible grids.

## Attempt 1 — actual solution attempt

The visible outputs preserve object color and shape, move objects to the bottom,
and place their bounding boxes consecutively from the left in increasing occupied
cell count. Same-color disconnected components must remain separate: the second
example has both a one-cell and a six-cell zero object. Color 0 is an object there,
not a default background. The large sparse object in the third example retains its
holes. Background is inferred independently from each input's most frequent color.

Implemented a standard same-color four-neighbor flood fill, bounding boxes, stable
size ordering and bottom-aligned translation in solution.py. It is standalone
Python with input checks and no generator/reference imports. No actual failed
solution preceded this attempt; none was fabricated.

The enclosing-border branch needs qualification. None of the three visible demos
has a uniform enclosing frame, while both queries do. Removing such a frame is a
choice informed by prior authoring exposure, not uniquely determined by these demos.
The solve is therefore useful execution evidence, not evidence of unbiased discovery
of the complete rule from this particular lesson.

## Visible-only diagnostic

Ran `python3 solve/visible_analysis.py` from packet_root. It records component
features, candidate predictions and a deliberately constructed frame-preserving
rival. The rival does the same packing, then restores a uniform non-background
outer border when present. It matches all three visible demonstrations but produces
a different prediction on both masked queries. This is an **intentional diagnostic
probe**, not an accidental failed solution and not a query-correctness score.
Full predictions and visible feature counts are retained in visible_analysis.json.
No private answer was opened or used to choose the rival.

This reveals a lesson-level limitation outside the three declared rivals checked
during authoring: frame removal is not demonstrated in this fresh lesson. Keep it
as a new regression target for later authorized work; do not claim unrestricted
identifiability from the finite-rival census.

## Check outcome and stop

The official attempt check completed: 3/3 visible examples passed. Its reported
label is unknown; hidden-query correctness is withheld. Two query predictions are
retained, with no claim that either was independently scored. There was one genuine
solution revision and no fabricated failure. Stop with the implementation and the
unresolved frame-branch ambiguity recorded for intake rather than consulting a
reference or private output to improve this solve.
