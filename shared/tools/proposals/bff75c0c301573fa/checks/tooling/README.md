# Optional rotation containment check

`rotation_fit.py` is a standalone Python standard-library tool for tasks that
promise to fit a rotated object inside a target interior. It imports no generator,
Racket authority, canonical data, or repository helper. It can be copied with
its tests and fixture to another checkout.

## Input and output

The positional input file contains one case object or a nonempty list of cases:

```json
{
  "source_shape": [1, 3],
  "turns_cw": 1,
  "interior_shape": [2, 3],
  "target_origin": [9, 9],
  "canvas_shape": [12, 15]
}
```

Shapes are `[height, width]` in cells, with strictly positive integer dimensions.
`source_shape` describes the source bounding box; its original position is
irrelevant. `turns_cw` is exactly 0, 1, 2, or 3 clockwise quarter turns. The source
is rotated about its bbox and rebased to its top-left before placement. Odd
quarter turns swap the height and width; even turns preserve them.

`target_origin` is the absolute zero-based `[row, column]` of the interior's
top-left, which is also the transformed bbox's placement origin. Supply it and
`canvas_shape` together, or omit both. Negative origins are allowed so that
off-grid placements can be diagnosed. The canvas check concerns the placed
transformed bbox, not the entire target region. Bool/float/string coercions,
unknown or missing fields, duplicate JSON keys, and nonfinite constants are
rejected. A malformed case rejects the batch without partial results.

Standard output is JSON with schema `rotation-fit-v1`, ordered per-case results,
and an aggregate `fits_all_checked`. Each result includes the transformed shape,
interior/canvas fit flags, and `top`, `bottom`, `left`, `right` overflow extents.
Each extent measures how far a bbox edge extends beyond the relevant boundary;
it is not a count of lost colored cells. The bbox is anchored at the interior's
top-left, so interior top/left overflow is zero. Canvas fields are `null` when
not requested. Exit codes: **0** all checked bounds fit; **1** some bbox does
not fit; **2** invalid input or a file-read error. Data errors emit a JSON
`error` instead of results.

This checks dimensions and placement only. It cannot distinguish the pixel
orientation of a clockwise turn from a counterclockwise turn with the same
dimensions. It does not compute puzzle outputs or detect cell-level overlap.
Containment must be opted into by the task author: intentional growth, painting
over borders, and clipping are legitimate in some tasks and must not be globally
rejected by this proposal.

## Run and reproduce

From the outer review packet directory:

```bash
python3 review.py run python3 ../checks/tooling/rotation_fit.py ../checks/tooling/rotation_fit_cases.json
python3 review.py run python3 -m unittest discover -s ../checks/tooling -p test_rotation_fit.py -v
```

The two-case fixture deliberately exits **1**: `[1,3]` turns into `[3,1]` in a
`[2,3]` interior (bottom overflow 1), and `[3,2]` turns into `[2,3]` in a `[3,2]`
interior (right overflow 1). These dimensions reproduce observed generator
failure geometry; the fixture contains no puzzle labels. The tests cover all
four turns, swapped axes, exact boundaries, negative origins, independent
interior/canvas failures, and strict CLI validation.

Outside a packet, run `python3 rotation_fit.py rotation_fit_cases.json` and
`python3 -m unittest discover -s . -p test_rotation_fit.py -v` from this folder.
The Python API is `check_case(case)`, which returns one result dictionary or
raises `ValueError`. This remains an optional proposal, not an installed shared
gate or a generator approval.
