# Observable solve record

This is a reviewer-authored work summary, not a model-token transcript. I had
already read the rule and generator during the generator repair. Earlier rule
exposure is **yes**. After preparing this challenge I kept those sources,
reference solutions, previous solution explanations, and private labels closed.
The solve used only `challenge.json`, the new Python program, local public-pair
experiments, and the solve-episode checker. This is not a blind human/model test.

## Visible observations

There are three public demonstrations and two masked query inputs. A green
silhouette is retained while each isolated differently colored pixel acquires a
copy of that silhouette in its own color. The second demonstration puts markers
above the green object, so location is not restricted to its lower-right.

The third demonstration distinguishes two candidate anchor conventions. Its
green bounding box begins at (0,5), but its first occupied pixel is at (0,6).
The color-1 marker at (5,2) remains in place while a pixel is also added at (5,3).
This observation supports bounding-box-origin alignment and preservation of the
original anchor, not first-occupied-cell alignment or replacing the whole stamp
box with a crop. Coordinates here are zero-indexed and refer to public examples.

## Actual sequence

1. `python3 solve/visible_probe.py` first ran against the supplied unimplemented
   stub and stopped with `NotImplementedError`. This is a harness/stub failure,
   not a failed inferred rule and not a submitted solve attempt.
2. Wrote the first substantive candidate in `solution.py`: collect the green
   silhouette, normalize its coordinates by minimum row and column, copy the
   input, and add a recolored copy at every singleton marker. The function
   validates the observed input contract and does not mutate the input.
3. Reran `python3 solve/visible_probe.py`. All three visible outputs matched,
   both masked inputs executed, and shape/color/nonmutation assertions passed.
   That probe reads no expected query output and makes no query-correctness claim.
4. Submitted this first candidate using the provided solve-episode check command.
   The automatically recorded attempt contains the exact program, notes, and
   public feedback. No alternative candidate was submitted just to create a
   failure history.

## Limits and stopping rule

Three demonstrations do not identify all possible programs. The solver retains
observed conventions (green reference and distinct singleton marker colors),
not a claim of validity for arbitrary grids. Stop once public examples match and
both queries execute; hidden correctness remains for independent intake scoring.
There was no reference consultation during the solve, but prior exposure prevents
using the result as independent blind-solving evidence.
