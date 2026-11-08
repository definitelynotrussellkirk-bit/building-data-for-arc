# Parametric orientation-to-motif family for `74e83caa0660`

This is reviewer authoring work, not an accepted family. The default
`completion_rule=canonical_x` is the catalog's exact canonical Racket source.
The alternative `orientation_selects_motif` keeps the same opposite-corner
input grammar but composes two steps: identify whether each pair is on the main
or anti diagonal, then use that input-dependent result to choose an X or plus
completion for that pair.

The sampler fixes one rule per episode, emits 2–6 demonstrations and up to four
queries, uses setting-independent inputs, teaches both orientation branches in
every normal pair set with at least two colors, and includes an exact 30x30,
eight-pair stress query. `always_plus.rkt` and `wrong_intermediate.rkt` are
bounded semantic rivals/counterfactuals; neither is an admitted setting.

Focused check from the packet root:

```sh
python3 review.py run python3 -m pytest -q \
  generators/74e83caa0660/tests/test_generator_74e83caa0660.py \
  generators/74e83caa0660/tests/test_parameters.py
```
