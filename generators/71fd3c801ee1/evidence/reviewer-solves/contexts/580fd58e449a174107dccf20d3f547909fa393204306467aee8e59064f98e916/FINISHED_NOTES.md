# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Visible-example analysis

- I had no earlier exposure to this task's rule, generator, labels, or solution notes.
- Each grid contains one four-cell object and four equal-size larger objects. Exactly two larger objects are recolored azure; positions and original colors vary, so neither is the selector.
- Initial rejected hypotheses included exact congruence, nearest/farthest objects, and a row/column positional rule. They do not explain all three examples.
- I extracted the visible objects and compared topology and symmetry. The recolored pair is the unique repeated structural class among the four large objects:
  - example 0: both have one enclosed hole and no mirror axis;
  - example 1: both are hole-free with one mirror axis;
  - example 2: both have one enclosed hole and one mirror axis.
- To distinguish the second query's rounded/diamond-shaped object from the intended pair, the implementation records the number of mirror axes and half-turn symmetry, not just a yes/no symmetry flag.
- The solver therefore ignores the size-four distractor, groups the four modal-size objects by `(enclosed holes, mirror-axis count, half-turn symmetry)`, and recolors the unique class occurring twice.
- Remaining uncertainty: the examples support this invariant-based classifier but cannot prove no unshown shape attribute is intended. I avoided positional tie-breakers; malformed/ambiguous inputs are returned unchanged.
