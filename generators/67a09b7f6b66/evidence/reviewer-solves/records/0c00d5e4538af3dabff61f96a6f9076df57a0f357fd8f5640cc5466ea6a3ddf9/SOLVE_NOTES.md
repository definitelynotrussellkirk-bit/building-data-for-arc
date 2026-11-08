# Solve work log

## Exposure disclosure

I had already inspected and repaired this task's generator and authority before
this required post-repair solve, so the finish record must say
`earlier-exposure=yes`. After `solve_episode.py prepare`, I used only the visible
examples in `solve/challenge.json`, my own Python implementation, and visible
check feedback. I did not reopen the generator, Racket rule, private labels, or
an earlier solution explanation during this episode.

## Visible-example inference

Each example has a three-color legend in row 0, columns 1–3, followed by three
rectangular chambers separated by full color-8 walls. The output leaves the
legend and walls unchanged and replaces every chamber interior with one legend
color. Counting color-1 marks explains the choice: one mark selects the first
legend entry, two marks the second, and three marks the third.

This is not a left-to-right position rule. In train example 2 the dot counts are
2, 1, and 3, and the output colors are the second, first, and third legend
entries. The examples also vary chamber width, and examples 1 plus both queries
use color 8 as a legend entry, so the solver must detect walls below the legend
rather than treat every 8 in row 0 as structural.

## Implemented transformation

1. Read the ordered legend from row 0, columns 1–3.
2. Locate the four columns that are color 8 throughout the framed body.
3. Locate the first and last all-8 rows below the legend.
4. Count color-1 marks inside each chamber.
5. Fill that complete interior with `legend[count - 1]`, preserving the frame
   and legend.

The implementation validates rectangularity, the expected frame, nonempty
chambers, and counts outside 1–3 rather than silently guessing.
