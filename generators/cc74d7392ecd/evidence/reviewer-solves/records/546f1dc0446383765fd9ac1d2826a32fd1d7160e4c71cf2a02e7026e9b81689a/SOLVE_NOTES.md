# Blind solve notes — cc74d7392ecd

## Observations

- Every input contains isolated nonzero single cells on a zero background.
- In each output, every such cell becomes an orthogonal radius-1 cross: center,
  one cell up/down, and one cell left/right.
- The color of each cross is the original singleton's color.
- Cross arms are clipped at the grid boundary. This explains the four-cell color
  9 at the top edge and the three-cell color 1 in the bottom-left corner of
  training example 1.
- No training example has overlapping crosses. The implementation writes all
  centers and arms in source scan order; overlap behavior is therefore untested,
  but the visible distribution strongly suggests separated seeds.

## Hypothesis

Copy the input, then for each nonzero cell paint its own color at Manhattan
radius at most one, clipped to the original dimensions.

## Expected queries

- Query 0: color 5 at the top-left corner becomes three cells; colors 8 and 3
  on row 7 become clipped/ordinary crosses respectively (the color 3 at the
  right edge has four cells).
- Query 1: colors 2 and 7 each become a five-cell cross; they are far enough
  apart not to overlap.

## Exposure declaration

This reasoning used only `solve-blind/README.md` and `challenge.json`. No rule,
generator, private label, reference solution, or prior solution explanation was
consulted.
