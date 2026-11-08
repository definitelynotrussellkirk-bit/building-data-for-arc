# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — diagnostic skeleton

I had already seen this task's generator and rule during the required repair
phase, so this is an exposed post-repair solve, not a blind solve. I closed those
sources before preparation and used only the displayed examples here. The first
check deliberately ran the untouched skeleton as a harness probe; it errored and
passed 0/3 visible examples.

## Revision 2 — bottommost-5 column segments

Visible-example hypothesis: inspect each column independently. A column is
active exactly when its bottommost nonzero marker is color 5. For an active
column, scan its nonzero markers top to bottom. Fill from the top through the
first marker with that marker's color; after that, fill the cells following the
previous marker through the current marker with the current marker's color.
Leave non-active columns and cells below a floating final marker unchanged.

The third demonstration is decisive: a column containing an internal 5 but
ending in 2 remains unchanged, while columns ending in 5 are segmented. It also
shows the lower/current marker owns the interval immediately above it. This
rejects “any column containing 5,” “fill every multi-marker column,” and
“previous marker owns the gap.”

Revision 2 passed all 3/3 visible demonstrations. I stopped because the examples
separately expose column selection, current-marker segment ownership, top fill,
and floating-tail preservation. The masked queries remain unscored here.
