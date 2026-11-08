# Exposed post-repair solve

Earlier exposure: yes. I authored/reviewed the generator and read its rule before
preparing this episode. This is not a blind discovery claim. During this solve
I consulted only solve/challenge.json and the visible preparation presentation;
the generator, Racket reference, earlier solve explanations and private labels
were kept closed. The two masked query outputs were never inspected.

Visible demonstration 0 is 25x16 in/out. Its [3,3,8] header paints a square
with center 3, radius-one 3 and radius-two 8 around the lone lower point.
The header is unchanged, and the square fits below the gray separator.
Demonstration 1 is 30x30 in/out, with seed (3,17), key [3,2,2,7,0,8]:
the visible square-radius color counts match the original positional key exactly,
including the zero gap. The radius-two, radius-three and radius-five header
colors become gray; the overflowing zero at radius four remains zero.
Demonstration 2 is 23x20 in/out with seed (3,0). Every nonzero key entry
after index zero becomes gray because every positive-radius square crosses
the left edge. Zeros at radii three and six remain zeros.

Hypothesis: draw clipped Chebyshev-distance rings from the unmodified header;
mark each nonzero header entry gray exactly when its full ring fails to fit
inside rows2..height-1 and columns0..width-1. Preserve the separator.
Using the modified gray key for painting would disagree with demonstration1.
Dropping zeros or deduplicating colors also disagrees with its visible body.

Revision1 is a direct Python implementation using full-ring containment tests.
No deliberate negative or fabricated failure was added. Stop when the visible
checker confirms this hypothesis; hidden correctness remains unscored here.
