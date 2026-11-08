# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — single-seed chamber flood

I had no earlier exposure to this task's generator, Racket rule, reference solution,
private labels, or prior solution notes. I used only the visible examples above.

Hypothesis: color 5 forms walls. The non-5 cells split into 4-connected chambers.
A chamber is flood-filled with the color of its seed only when it contains exactly
one nonzero/non-5 cell. Chambers with no seed or more than one seed are copied
unchanged. This explains all visible behavior: example 0 fills the one-seed top
and middle horizontal chambers but leaves the chamber containing both 2 and 3;
example 1 fills the left 1 chamber and lower-middle 3 chamber but leaves the
right chamber containing 1 and 2; example 2 behaves the same across irregular
wall partitions.

Probe: I wrote a visible-example harness against challenge.json before changing
solution.py. The initial stub failed with NotImplementedError, establishing the
red test. I then implemented iterative 4-neighbor component traversal and the
exactly-one-seed condition. Remaining uncertainty: no visible example contains
multiple seeds of the same color in one chamber, so I interpret "exactly one
seed" literally rather than "exactly one distinct color"; the dot-count framing
and the unchanged multi-marker examples support that choice.
