# Blind solve notes

Assignment: review-fcac4ea7f9b85c18; task: a452b4b4f04a.

## Exposure

This solve began without earlier rule exposure. I inspected only the prepared
README.md and challenge.json, plus the prepare/check command feedback. I did
not consult rule text, generator code, reference solutions, private labels,
prior solution notes, or reference-source helpers.

## Revision 1

Hypothesis: each nonzero color marks corners of a separate axis-aligned
rectangle. Complete its perimeter using the minimum and maximum row and
column occupied by that color; retain the original grid elsewhere.

The visible demonstrations cover four marked corners, two opposite corners
(both diagonal orientations), and three marked corners. All show hollow
rectangles whose bounding boxes match the markers. The query inputs use the
same visible arrangements.

Implementation: group positions by nonzero color and draw each bounding-box
border. This is the first implementation; there are no discarded revisions.

Local experiment: all three visible training examples matched exactly, with
zero mismatched cells. A hand-authored two-corner example also produced the
expected hollow border. The experiment exited 0. No implementation revision
was indicated by those results.

Official check: `python3 review.py blind check --intent solve --note
'Complete each nonzero color bounding-box perimeter; test the first
implementation against all visible demonstrations.'` exited 0. Revision 1
completed execution and passed 3/3 visible examples. Masked-query correctness
was reported as unknown, as expected.

Stopping reason: the single implementation explains every visible
demonstration and passes the visible check, with no observed discrepancy to
justify another revision. Query labels remain uninspected and correctness is
withheld. No failures were removed; no additional revisions were fabricated.
