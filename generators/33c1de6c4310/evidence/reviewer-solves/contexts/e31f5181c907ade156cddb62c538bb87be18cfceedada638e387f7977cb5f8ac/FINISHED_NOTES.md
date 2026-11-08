# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — nonzero stencil over the right panel

Earlier exposure before this solve: none to task 33c1de6c4310's rule, generator,
solutions, private labels, or prior notes. I only read the public challenge.

Observation: every input has a single full-height color-9 separator. The panels
on its two sides have equal dimensions. The output has the panel dimensions and
keeps the right-panel value exactly where the corresponding left-panel cell is
nonzero; all other cells become 0. This accounts for every visible output cell,
including examples whose stencil uses more than one nonzero color.

Probe: `python3 solve-blind/test_visible.py`. Before implementation it failed at
the starter `NotImplementedError`; after implementing the stencil rule it should
match all three visible examples. I did not test against or inspect query labels.

Official visible-only check: revision 1 completed and matched 3/3 visible
examples. I stopped because one simple rule accounts for every output cell and
both queries share the same separator/panel structure. Masked query correctness
remains unknown by policy.
