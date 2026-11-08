# Solve work log — 4c26a1072222

This is a human work log from the visible examples. I had already inspected the
repair target before this required post-repair solve, so this episode is exposed,
not blind. During the solve episode I kept the generator, Racket source,
reference solutions, and masked labels closed and used only `challenge.json`.

## Visible structure

- Every active region is two rows high. All-zero rows separate independent
  regions.
- In each region, columns 0–1 are a 2x2 example block A, columns 3–4 are a 2x2
  result block B, and columns 7–8 are a 2x2 block C whose result becomes the
  corresponding two output rows.
- Geometry and recoloring can both occur. The relation is independent in each
  band; a single global transform or color map does not explain the examples.

## Concrete check

In training example 1, the first A block is `[[3,6],[6,6]]` and B is
`[[6,3],[6,6]]`. A horizontal mirror maps A to B without recoloring. Applying
that mirror to C=`[[4,9],[4,4]]` gives `[[9,4],[4,4]]`, exactly the first two
output rows. Other bands show recoloring and other symmetries, so the solver
must infer both pieces rather than copy this one operation.

## Hypothesis and implementation

For each band I enumerate all eight symmetries of a square. A candidate is legal
when equal colors in transformed A always correspond to equal colors in B,
which defines a functional color map. Among legal candidates I choose the one
with the most cells already equal before recoloring; ties use the fixed
identity/mirror/rotation/transpose enumeration. I apply the selected symmetry
to C and then apply the learned map, leaving a C color unchanged when A did not
teach a mapping for it. Separator rows remain zero.

No diagnostic or deliberately wrong revision was needed; the first complete
implementation is the visible-example hypothesis I am checking.
