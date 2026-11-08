# Solve work log

## Prior exposure

I had inspected the selected generator and canonical Racket authority earlier in
this review, so this is an exposed post-repair solve, not a blind solve.  During
this solve phase I did not reopen either source, any private labels, reference
solutions, or earlier solution explanations; I used only the visible challenge.

## Revision 1 hypothesis

Each input has two colored singleton cells, one in the upper horizontal half and
one in the lower half.  The output preserves the input dimensions and turns
those cells into two stacked open frame regions:

- the upper color fills the top row, the upper dot's row, and the left/right
  borders above `floor(height/2)`;
- the lower color fills the lower dot's row, the bottom row, and the left/right
  borders from `floor(height/2)` downward;
- all other cells remain zero.

Evidence from the visible examples:

- Example 0 uses rows 2 and 7 on height 10; those exact rows become horizontal
  bars, while the side-color transition occurs at row 5.
- Example 1 uses rows 1 and 12 on height 14, disproving fixed dot rows 2 and 7.
- Example 2 reverses the numerical color order and places dots on rows 4 and 5,
  showing that spatial half membership, not color sorting, assigns the two
  frames.
- Query 0 has odd height 15 and puts the lower dot at row 7, so the natural
  integer split is `15 // 2 = 7`; row 7 belongs to the lower region.

I implemented this rule directly and will check it against all visible examples.
The main remaining uncertainty before checking is only whether an unseen case
could use a different split convention; Query 0 is designed to resolve that.
