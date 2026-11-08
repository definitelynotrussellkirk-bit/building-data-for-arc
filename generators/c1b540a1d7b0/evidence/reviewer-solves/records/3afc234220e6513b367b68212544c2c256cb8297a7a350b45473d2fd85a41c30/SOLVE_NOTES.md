# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — minimum primitive cover

Visible examples suggest that each gray foreground is a superposition of solid
2×2 blocks and axis-aligned bars of length at least three.  The output recolors
bar cells red (2) and block-only cells azure (8).  I enumerated all contained
2×2 blocks and straight bars, searched for a minimum-cardinality cover of the
foreground, and used minimum total primitive area as a tie-break.  This is an
MDL-style reconstruction rather than a claim that the latent drawing is unique.

A private scratch enumeration using only `challenge.json` showed that examples
0 and 1 have a unique minimum-overlap cover matching the visible output.  Example
2 has multiple one-bar covers after placing the three obvious 2×2 blocks, so I
expect this first rule may expose a tie-break failure there.  I am checking it
rather than silently baking the visible answer into the first revision.

## Revision 2 — distinguish avoidable from unavoidable overlap

Revision 1 passed 2/3 visible examples.  The failure is the two-row example:
a three-square plus one-bar explanation is minimum-cardinality, but the visible
red bar is not the shortest possible bar.  The common property of examples 0
and 1 is stronger: they have a minimum-object cover with **no primitive overlap**,
and that cover uniquely matches the labels.  Example 2 has no non-overlapping
minimum cover at all.  I therefore changed the tie-break to prefer a zero-overlap
minimum cover when one exists; otherwise it uses stable row-major primitive
order.  This selects the left-anchored bar seen in example 2 without matching on
its dimensions or coordinates.

Remaining uncertainty: the test shapes can still admit several equally compact
overlapping latent drawings.  The visible examples do not determine the hidden
placement among all such drawings, so the row-major fallback is a documented
inductive choice rather than a proof of uniqueness.
