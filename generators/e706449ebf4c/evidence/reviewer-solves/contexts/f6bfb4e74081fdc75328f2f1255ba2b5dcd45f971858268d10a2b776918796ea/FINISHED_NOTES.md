# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — doubled-coordinate Manhattan auras

Earlier exposure: **yes**. Before this visible-only solve I had reviewed the
assigned generator family and therefore knew the broad intended transformation.
During this solve I did not reopen the generator, Racket rule, reference solution,
or private query labels; I used only the prepared visible examples and my own
program.

Visible hypothesis: every 4-connected red component is a straight bar. For each
bar, take its inclusive bounding-box length `L` and exact bounding-box midpoint.
Paint cyan (8) into background cells at Manhattan distance at most `L/2` from
that midpoint, independently for every bar, clipping at the grid boundary and
preserving existing red cells. Using doubled coordinates gives the integer test
`abs(2*r-(top+bottom)) + abs(2*c-(left+right)) <= L`, which handles both odd
and even bar lengths without rounding the center.

Checks against the visible examples before running the harness:
- Example 0 has two length-10 vertical bars, so their half-cell-centered diamonds
  overlap while both red bars remain intact.
- Example 1 has two nearby length-8 horizontal bars; the same rule creates the
  observed layered diamonds and preserves the lower bar under the upper aura.
- Example 2 has two length-6 horizontal bars with smaller, partly overlapping
  fields.
- Query 0 is a single odd length-9 vertical bar; query 1 has two length-14
  horizontal bars. Both are covered by the same doubled-distance calculation.

Remaining uncertainty before checking: none material; the exact visible boundary
cells distinguish the doubled midpoint from an integer-rounded center.
