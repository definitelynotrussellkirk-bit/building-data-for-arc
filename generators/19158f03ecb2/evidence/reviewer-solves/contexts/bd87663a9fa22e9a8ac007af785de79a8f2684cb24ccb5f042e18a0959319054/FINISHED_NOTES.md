# Solve notes

## Visible-only hypothesis

Every training output preserves the input height and doubles its width. For each
row, the left half is the original row and the right half is that same row in
reverse order. This explains both asymmetric rows (where the second half visibly
changes direction) and palindromic rows (where duplication and reflection happen
to coincide).

I implemented `row + reversed(row)` independently for every row. No Racket rule,
generator source, reference solution, private label, or previous solve explanation
was consulted during this solve phase. I had earlier rule exposure from the
required generator review, so the final exposure declaration is `yes`.
