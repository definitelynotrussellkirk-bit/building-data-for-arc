# Blind solve work log: 6c8eefa043e1

This is a concise model-authored work log, not a token-level conversation trace.
Earlier rule exposure: no. Reference consultation during solving: no.
I read only the public challenge/README, the initial solution/work-log stubs,
the general DUTIES and RETURN-GUIDE instructions, and visible command output.
No generator, rule, canonical/reference data, private answer, or audit evidence
was opened. The initial README read occurred before preparation and reported
that the file did not yet exist; it was read successfully after preparation.

## Preparation

From the outer packet directory:
`python review.py blind prepare` exited 0 and displayed three demonstrations
and two queries. The demonstration input/output shapes were respectively
7 by 18, 15 by 18, and 9 by 9. Query inputs were 9 by 16 and 7 by 7;
their outputs were unknown.

## Hypothesis and visible-only experiment

Color 5 forms walls. Each remaining four-connected component that contains
a colored marker receives that marker's color. Components without a marker
stay zero. Existing walls and seeds stay unchanged.

Evidence for four-neighbor connectivity: in demonstration 2, cell (4, 0)
stays zero despite being diagonally adjacent to the colored region through
(3, 1). This excludes unrestricted diagonal flood fill. Other unseeded regions
also stay zero, so filling every non-wall region is inconsistent with the data.

A Python heredoc reading only `solve-blind/challenge.json` enumerated non-5
four-connected components, collected their nonzero seed colors, recolored
seeded components, and compared only the three visible outputs. It exited 0.
All three comparisons were exact. Seeded component sizes and changed counts:

- Demonstration 0: color 7 has 20 cells; color 9 has 9; 27 cells change.
- Demonstration 1: color 3 has 3 cells; color 7 has 12; color 2 has 12;
  24 cells change.
- Demonstration 2: color 3 has 41 cells; color 7 has 7; 46 cells change.

The same input-only analysis found one distinct seed color per seeded component
in each query: sizes 16/4/11 for colors 7/9/4 in query 0, and 19/2/4 for
colors 8/6/9 in query 1. These are structural observations, not hidden-answer
validation. No hidden labels were accessed or compared.

## Revision 1

Implemented the component flood fill using a queue and a visited set, with an
independent copy of the input. Unseeded components and walls are preserved.
The visible examples do not specify what to do if different seed colors share
one component, so the implementation raises an explicit error for that case;
none of the visible demonstration or query inputs has it.

The component experiment supports this first attempted solution. No previous
solution failed, and no intentionally wrong revision was manufactured.
The official visible-only check is the next step.
