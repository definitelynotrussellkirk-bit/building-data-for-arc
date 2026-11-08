# Post-repair visible-only solve

Task c5f62271ea44; source hash at prepare:
8e242979e5d7db509e8298c877fa99c8a8143505c7fb2ff74e32a0c25924aa82.

Earlier rule exposure: yes. I inspected the task generator, canonical examples
and Racket during the preceding repair. This is an exposed solve record, not
an independent blind discovery. After preparation I used only the visible
challenge presentation and my Python implementation; I did not reopen those
reference sources, import generator helpers or consult private query labels.
These are reviewer-authored work notes, not captured token-level traces.

## Revision 1

Visible example dimensions, before any interpretation:

| Pair | Input | Output |
| --- | --- | --- |
| train 0 | 22 rows x 21 columns | 9 rows x 9 columns |
| train 1 | 22 rows x 21 columns | 9 rows x 9 columns |
| train 2 | 23 rows x 19 columns | 9 rows x 10 columns |
| train 3 | 22 rows x 21 columns | 9 rows x 9 columns |
| query 0 | 21 rows x 27 columns | unknown |
| query 1 | 19 rows x 30 columns | unknown |

Each input has a solid blue panel and three isolated colored dots. The panel
body is retained in the output along with three colored inner-corner markers.
Treating the unoccupied key corner as blue yields these corner correspondences,
in top-left, top-right, bottom-left, bottom-right order:

| Pair | Input panel corners | Key / visible output corners |
| --- | --- | --- |
| train 0 | 5,4,1,8 | 8,4,1,5 |
| train 1 | 1,8,4,5 | 8,5,1,4 |
| train 2 | 1,4,3,2 | 3,2,1,4 |
| train 3 | 5,4,1,8 | 1,5,8,4 |

These require an anti-diagonal reflection, counterclockwise rotation,
vertical reflection and clockwise rotation, respectively. A fixed transform
cannot explain the examples. Transferring corners alone would lose the body,
which is visibly preserved and moved. Matching the full four-value signature
distinguishes transforms that would move only the blue corner identically.

The program crops the blue bounding box, reconstructs the key signature and
enumerates four rotations with and without a left-right reflection. It returns
the unique matching whole-panel orientation. It reads no hidden metadata or
labels. Rotation is implemented directly with coordinates; no task helpers
are imported. Unknown or nonunique signatures raise an explicit error.

Command from outer packet root:
WORK/.venv/bin/python review.py solve check --intent solve
--note 'Match the entire four-corner key and transport the whole panel; enumerate eight orientations from visible geometry.'

No failed attempt was manufactured. The query outputs and their correctness
remain withheld by the checker; I do not treat execution completion as a
private-label correctness result.
