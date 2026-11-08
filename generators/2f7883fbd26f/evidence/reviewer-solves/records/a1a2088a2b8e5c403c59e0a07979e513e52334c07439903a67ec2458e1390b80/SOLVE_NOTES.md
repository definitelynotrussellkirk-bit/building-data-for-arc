# Solve work log

## Exposure declaration before solving

I had already read the canonical rule and generator while performing the assigned review, so this is an **exposed post-repair solve**, not a blind solve. During this solve episode I used only the visible challenge presentation, my own Python, and visible-example check feedback; I did not reopen the Racket source, generator implementation, reference solution, private query labels, or earlier solution explanations.

## Revision 1 — sliding 2 × 2 color-1 windows

Visible examples suggest that color 2 is distraction and the output is a fixed-width unary count. In example 0, the 2 × 5 strip of ones contributes four overlapping 2 × 2 windows, matching `[1,1,1,1,0]`; counting connected components or isolated squares would not. Example 1 has a 2 × 3 all-1 rectangle, giving two sliding windows. Example 2 contains three separated 2 × 2 all-1 blocks, giving three. Therefore the rule is: count every sliding 2 × 2 window whose four cells are color 1, including overlapping windows, and output five cells with that many leading ones followed by zeros.

The implementation directly enumerates all top-left anchors. Remaining uncertainty is only whether generated counts could exceed five; the visible output contract and examples use width five, and the assigned generator family is designed within that range.
