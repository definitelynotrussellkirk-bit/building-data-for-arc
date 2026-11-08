# Solve notes

This is a human work log based only on `solve/README.md` / the visible challenge.
I had already seen the task rule while reviewing its generator, so this is an
**exposed post-repair solve**, not a blind solve. During this solve I did not
reopen the generator, Racket source, reference solutions, private labels, or old
solution explanations.

## Observations

- Row 0 is a dense sequence of colors and acts as a column-indexed key. The one
  gray `5` in that row is aligned with the vertical cyan `8` line.
- Output cells before the first line cell and after the last line cell are all
  gray. Train examples 1 and 2 are important because their lines are off-center
  and stop at the penultimate row; the output follows the observed line rather
  than the geometric center or the bottom edge.
- At line-top the output has only cyan. Each next row widens by one column on
  each side. Non-line cells inside that interval copy the value from row 0 in
  the same column. The cyan column remains `8`, even though its row-0 key is 5.
- Train example 1 projects a row-0 `8` beside the structural line, producing two
  adjacent 8s. This confirms that ordinary key values are copied literally and
  line detection must ignore row 0.
- The widest radius is capped at `(width - 1) // 2`. Grid boundaries clip the
  interval naturally.

## Implemented hypothesis

1. Find the sole column containing color 8 below row 0.
2. Read its first and last occupied rows as the active interval.
3. Start an all-5 output of the same shape.
4. For active row `r`, set radius to `min((w-1)//2, r-line_top)`; keep the line
   cell cyan and copy row-0 values at every other column inside the radius.
5. Leave all other cells gray.

No accidental failed revision was needed; the off-center and truncated visible
examples directly distinguish the two most tempting shortcuts.
