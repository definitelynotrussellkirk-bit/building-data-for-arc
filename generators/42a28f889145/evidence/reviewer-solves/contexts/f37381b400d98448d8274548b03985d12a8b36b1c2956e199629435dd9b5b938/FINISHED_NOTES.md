# Solve work log

## Prior exposure

Before this solve I had already inspected and repaired the assigned generator and
seen the intended task description. Earlier rule exposure is therefore **yes**.
During this solve I did not reopen the generator, Racket source, reference
solution, private labels, or earlier solve explanations; the observations below
come from the newly prepared visible examples.

## Revision 1 hypothesis

All three visible outputs preserve the grid dimensions, every background cell,
and every occupied coordinate. Exactly two nonzero colors occur in each input,
and every cell of each color becomes the other color:

- example 0 exchanges 3 and 4;
- example 1 exchanges 8 and 9;
- example 2 exchanges 1 and 6.

The second example is especially diagnostic: the left object begins with the
larger color 9 and the right object with 8, then they become 8 and 9. That rules
out merely sorting numeric colors descending from left to right. Object size and
shape are irrelevant because no occupied coordinates move.

I implemented the most direct visible rule: collect the two nonzero color values
and replace each with the other everywhere, leaving zeros unchanged. The program
rejects inputs that do not have exactly two nonzero colors instead of silently
inventing behavior outside the visible domain.

Expected query behavior: query 0 exchanges 1↔8; query 1 exchanges 2↔8. Remaining
uncertainty is only masked-query scoring, which the check command intentionally
withholds.
