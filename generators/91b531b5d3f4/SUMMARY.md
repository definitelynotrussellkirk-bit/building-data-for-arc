# 91b531b5d3f4

Treat row 0 as column headers. For each body cell equal to color 1, replace it
with the nonzero header color in the same column; preserve cells below a zero
header and preserve every non-1 cell.

Default generation is a four-example semantic curriculum:

1. one strict linked official-profile anchor;
2. an unchanged color-1 marker below an empty header;
3. unchanged non-marker distractors below live and empty headers; and
4. a mixed counterfactual combining both negative branches, including a body
   cell whose color is another header color but which must remain unchanged.

The generator declares executable semantic witnesses, four canonical-compatible
shortcut rivals, and a lesson-identifiability hook. A task-local
`workspace/curriculum_probe.py` reproduces the schedule and shortcut-separation
claims without replacing the repository battery or Racket checks.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
