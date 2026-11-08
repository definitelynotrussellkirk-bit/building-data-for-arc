# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Visible-only analysis

I had not opened this task's generator, canonical rule, reference solution, private
query labels, or prior solve notes. I had only read the packet-level workflow and
the visible examples printed by `solve_episode.py blind prepare`.

The 11×11 grids are partitioned by full color-5 rows and columns into a 3×3 array
of 3×3 panels. My first visual possibility was that the panel containing the
unique color-4 cell might be reflected or shifted according to its global panel,
because example 0 moves a middle-right panel to middle-left. Comparing all three
examples rejected that: the source panel's global location does not predict the
destination consistently.

The consistent rule is that color 4 acts as a local pointer. Find the 3×3 source
panel containing the unique 4. Its zero-based local row and column select a panel
in the 3×3 panel array. Clear every non-divider panel, then copy the entire source
panel unchanged into that selected destination panel. Evidence:

- Example 0: the marker is at local (1,0), so the source panel is copied to the
  middle-left panel.
- Example 1: local (1,1) selects the center panel.
- Example 2: local (1,2) selects the middle-right panel.

For query 0 the marker is local (0,0) in the bottom-right source panel, so I expect
that panel to be copied to the top-left. For query 1 it is local (0,1) in the
middle-left source panel, so I expect that panel to be copied to the top-middle.

I implemented divider discovery rather than hard-coding row/column indices, while
keeping the inferred color-4 pointer semantics explicit. Remaining uncertainty:
the visible data does not test unequal panel sizes, multiple markers, or a divider
color other than the full uniform nonzero lines; the prepared queries share the
same structure, so these are outside this solve's observed domain.
