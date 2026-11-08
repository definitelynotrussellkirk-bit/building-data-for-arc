# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Initial observations and hypothesis

I had not seen task `671a9af906aa`, its generator, or its reference rule before
this episode. I inspected only `challenge.json`.

The non-8 cells form a maze graph containing four colored terminals 2, 3, 4,
and 5. In the first four demonstrations, the orange cells are exactly the
interior cells of two vertex-disjoint paths. The endpoints always form a
bipartite matching from source set `{2, 5}` to target set `{3, 4}`:

- either `2→3` together with `5→4`, or
- `2→4` together with `5→3`.

I explicitly compared all three perfect matchings. The tempting third matching
`2→5` plus `3→4` is the only disjoint one in the fifth demonstration, yet that
example remains unchanged. This is evidence that source-to-source and
target-to-target connections are forbidden, not merely that any disjoint
pairing should be drawn.

The working rule is therefore: compute maze paths through non-8 cells for the
two allowed matchings, select the unique matching whose paths share no vertex,
and recolor only zero-valued interior path cells to 7. If neither allowed
matching (or more than one) is valid, leave the grid unchanged.

## Probes

I represented every non-8 cell as a 4-neighbour graph and measured the unique
shortest paths for all six color pairs. The inferred allowed matching exactly
reproduces every orange cell in demonstrations 1–4. In demonstration 5 both
allowed matchings overlap other routes/terminals, while the excluded matching
is disjoint; the no-change output distinguishes the bipartite rule from a
weaker “choose any disjoint pairing” rule.

Before implementation I added `test_visible_examples.py`; it failed with the
stub's `NotImplementedError`, confirming the test exercised the missing solve
behavior. The implementation uses BFS and refuses to guess when the legal
matching is absent or ambiguous.

Remaining uncertainty: the examples appear tree-like, so each relevant route
is unique. On a cyclic maze, selecting one arbitrary shortest route might not
capture an intended existential choice among multiple routes. The visible data
does not require handling that broader case.
