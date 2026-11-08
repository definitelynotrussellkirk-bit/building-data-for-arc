# Solve work log

## Exposure declaration before solving

Before the blind task was drawn, I read the packet-level `WELCOME.md`, the
repository `AGENTS.md`, and part of the general `ARC-DESIGN.md` / return guide.
Those documents describe reviewer workflow and generic ARC composition ideas; I
did **not** inspect task `2c7b1545edf9`'s generator, Racket rule, notes, private
labels, prior solutions, or any target-specific record. The visible examples
printed by `solve_episode.py blind prepare` and `solve-blind/challenge.json` were
the only task data consulted.

## Revision 1 — largest monochromatic component

**Observation.** Each input contains several monochromatic 4-connected objects.
The output is a tight crop of one object, preserving its color and replacing all
other cells with background. In training examples 1 and 2 the chosen object is
the unique largest connected component. In training example 0, color 8 has two
separate components (sizes 6 and 5), while colors 4 and 7 each form a size-7
component. The output uses color 4, which is the first size-7 component in
row-major order.

**Hypothesis.** Enumerate same-color 4-connected nonzero components in row-major
order, choose the largest, keep the first on a size tie, and translate it to its
tight bounding box.

**Probe.** I added `test_visible_examples.py`, which loads only
`challenge.json`. Before implementation it failed on the first example with the
expected `NotImplementedError`. After implementing the component/crop rule, the
same test is expected to cover all three visible examples.

**Predicted queries.** Query 0 selects the size-7 color-2 component over the
later size-7 color-1 component. Query 1 selects the size-7 color-5 component over
the later size-7 color-1 component. The 11 cells of colors 3/8 are split into
smaller components and therefore do not win.

**Remaining uncertainty.** The examples support row-major tie-breaking, but only
one training example exercises a maximum-size tie. A different hidden tie policy
could agree on the demonstrations. I stopped at the simplest deterministic rule
that explains every visible pair and both query layouts without consulting any
reference material.
