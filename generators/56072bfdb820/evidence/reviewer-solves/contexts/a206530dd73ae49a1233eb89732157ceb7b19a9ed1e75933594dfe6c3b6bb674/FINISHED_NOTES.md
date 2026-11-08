# Visible-example solve notes

I treated each 3×3 region separated by color-6 lines as one meta-cell.  A
four-pixel diamond is a symbol in that meta-cell.

Observed rule from the five visible pairs:

1. Any input diamond whose color is not 2 sends the task to a separate error
   branch: a 16×16 grid filled with color 7.
2. Otherwise, preserve the two color-2 diamonds and infer one color-5 and one
   color-8 diamond from their ordered relative geometry.
3. The proposals are clipped at the 3×3 meta-grid boundary, explaining why
   some valid examples add only one symbol rather than always completing four.
4. For a same-row pair, step left from the left symbol and place 8 above and 5
   below.  For a same-column pair, step above the upper symbol and place 5 left
   and 8 right.  For diagonals, use the lower row-major symbol: when it is to
   the right, place 8 to its right and 5 below; when it is to the left, place 8
   to its left and 5 below.

For the two queries this predicts, respectively, one clipped completion (an 8
at the bottom-right meta-cell) and a full same-row completion (8 top-left, 5
bottom-left).  I implemented the general rule rather than hard-coding them.

Earlier exposure: yes. I had reviewed the generator before this required
visible-only episode, so this is not a blind solve. During this episode I read
only `solve/challenge.json` and did not consult the Racket rule, generator,
reference outputs, private labels, or previous solution explanations.
