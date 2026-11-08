# Blind solve work log — 40dea3d45f2a

This is a concise model-authored experiment log, not a captured token-level trace.
Earlier rule exposure: no. During this solve I opened only the public challenge,
the solution stub and this log; no generator, rule, canonical answers, prior
explanations, audit evidence or private labels were consulted.

## Revision 1

The three visible inputs are each 9 rows × 9 columns; each visible output is
4 rows × 4 columns. The two queries have 9 rows × 9 columns as input and unknown
outputs. Four separated objects suggest a matrix indexed by object position.

Hypothesis: mark an entry 8 when two spatially ordered objects have the same
shape under rotation or reflection, ignoring color; otherwise mark it 0.
Objects are ordered by visual row band, then left to right. Sorting simply by
the first occupied row would reverse the top two objects in example 1.

Visible Python probes, retained in visible_probes.json, compared cell count,
rotation equivalence, and rotation/reflection equivalence. Cell count fits
examples 0 and 2 but fails example 1. Rotation alone fails all three examples.
Rotation/reflection equivalence fits all three, so revision 1 implements it.
These were hypothesis probes before the first submitted solution, not failed
solve attempts or manufactured teaching negatives.

Remaining uncertainty: the visible examples do not determine arbitrary object
layouts, touching objects, nonzero backgrounds, or a different ordering policy
outside the displayed two-by-two arrangement. The implementation generalizes
to separated row bands and uses black as background, consistent with all visible
examples. Query correctness will remain unscored here.
