# Visible-example solve work log

This is a work log of hypotheses, implementation choices, and observed checks;
it is not a token-level reasoning transcript.

## Exposure and scope

- I am a separate solver, assigned after a coordinating repair reviewer had
  inspected the task source/rule. I received no transformation hints from that
  reviewer and have not inspected the source/rule, reference implementation,
  canonical files, private labels, other agents' reports, or prior explanations.
- The final declaration uses `--earlier-exposure yes` because that earlier
  coordinating-review exposure exists in this task's history. It does not mean
  this separate solver consulted the reference.
- My only task-data reads were this solve lane's `README.md`, `challenge.json`,
  the initial `solution.py` stub, and my own code/work log. I used no browsing.

## Hypothesis 1: color pairing, numbered rotation, upper-left placement

The inputs contain outlined rectangular frames, each with one numbered clue,
and detached shapes whose colors match the frame borders. Outputs preserve
the borders, remove the loose shapes and clue pixels, and reproduce the loose
shapes at the upper-left of the corresponding frame interiors.

The clue values fit this rotation table:

| Clue | Rotation of the matching loose shape |
| --- | --- |
| 1 | None |
| 2 | 90 degrees clockwise |
| 3 | 180 degrees |
| 4 | 270 degrees clockwise |

Visible evidence before implementation:

- Train 0: clue 1 preserves the orientation of the four-cell shape.
- Train 1: clue 2 changes `11/10` to `11/01`.
- Train 2: clue 3 changes `10/11` to `11/01`.
- Train 3: clue 4 changes `11/01` to `11/10`.
- Train 4: two frames use clues 1 and 3 and match detached pieces by color,
  even though those pieces are nearer the other frame.
- Train 5: clues 2 and 4 give different rotations of identically oriented
  detached shapes; the frame color can itself equal another valid clue value.
- Train 6: clues 1 and 3 are consistent with the same rotation table and
  upper-left placement in differently sized interiors.

Clue position varies independently of the destination shape; the frame
interior's upper-left corner, rather than the clue coordinate, is the anchor.
The query inputs also contain clue colors matching other frame colors, so
all frame rectangles must be excluded when collecting detached shape cells.

## Implementation and planned check

`solution.py` finds monochromatic four-connected rectangular outlines,
extracts their interior clues, excludes all frame rectangles from detached
shape collection, rotates each color-matched shape by `clue - 1` clockwise
quarter-turns, erases its original cells and clue, and places it at the
corresponding interior upper-left corner. It uses geometry and colors from
the input and contains no example-specific coordinates or stored outputs.

The first official check will test this hypothesis against all seven visible
training pairs and execute both query inputs. There were no earlier check
attempts or observed failed candidates in this solver's work.
