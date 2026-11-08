# Solve work log

## Exposure declaration

Before this blind solve I had not opened the task's generator, canonical rule,
reference solution, private labels, audit material, or any earlier explanation.
I used only the visible examples emitted by `review.py blind prepare` and the
public `challenge.json`.

## Observations and hypothesis

Across all three demonstrations, color `1` forms a small hub object. Several
other monochromatic components touch that hub by an edge. Every such touching
component is recolored completely to `4`; remote components of the same colors
are unchanged. This explains cases where only one cell touches the hub but the
entire connected component changes, and it explains why an already-color-4
component is visually unchanged.

I considered two alternatives and rejected them from the visible examples:

1. Recolor only cells immediately adjacent to `1`. Example 0 disproves this,
   because the full four-cell color-9 component changes although only its lower
   cell touches the hub.
2. Recolor components matching a remote shape or selected by size. The examples
   include changed components of several sizes and colors, while remote duplicate
   colors remain unchanged; edge contact with `1` is the common property.

## Implementation

Find every non-background, non-`1` orthogonal neighbor of a `1` cell. From each
seed, flood-fill the complete 4-connected component of that seed's color and
paint it `4`. Preserve the grid shape, the `1` hub, background, and all remote
components.

## Verification

A visible-example regression script was created first. It failed on the initial
`NotImplementedError`, establishing the red test. After implementing the rule,
it is rerun against all three visible training pairs, followed by the packet's
blind checker. Remaining uncertainty is limited to whether diagonal-only contact
could count; every visible changed object has orthogonal contact, so the solver
uses the narrower evidenced interpretation.
