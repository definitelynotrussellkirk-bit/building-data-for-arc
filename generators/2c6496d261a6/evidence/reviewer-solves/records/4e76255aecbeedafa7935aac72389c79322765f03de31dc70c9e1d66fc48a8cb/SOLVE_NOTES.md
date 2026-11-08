# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1

Earlier exposure: none known. I had not opened this task's generator, canonical
rule, reference solution, private labels, or audit records. I used only the
visible examples printed by `python3 review.py blind prepare`.

Hypothesis: each input contains (a) a signal color whose nonzero cells all lie on
one horizontal row, (b) a marker color occurring exactly once, and (c) one or
more distractor colors. The output preserves the horizontal signal and singleton
marker and replaces every distractor cell by background 0.

Evidence from the visible examples:

- Example 0 keeps the three 4s on row 5 and the single 8; all four 7s vanish.
- Example 1 keeps the three 6s on row 3 and the single 7; all four 9s vanish.
- Example 2 keeps the four 4s on row 2 and the single 9; both 7s and all 8s vanish.

Rejected alternatives: "remove the color occurring four times" fails example 2,
where both the two 7s and four 8s vanish. Vertical alignment with a signal cell
also fails because example 2 has removed 7s in signal column 4. The structural
horizontal-row plus singleton description fits all three examples and both
queries visibly contain one candidate of each kind.

Implementation: collect non-background cells by color, retain all singleton
colors and the longest color confined to one row, and erase the rest. Remaining
uncertainty: the examples do not show malformed cases with multiple singleton or
multiple horizontal candidates; deterministic fallbacks are included but are not
part of the inferred task rule.
