# Blind solve work log — 59c2f0a5d4a9

This is an authored summary of observations and experiments, not a token-level
conversation trace. Earlier rule exposure: no. No generator, reference rule,
canonical helper, private labels, or prior explanation was consulted.

## Visible evidence and hypothesis

Example 0: Input: 10 rows × 10 columns. Output: 10 rows × 10 columns.
Example 1: Input: 12 rows × 13 columns. Output: 12 rows × 13 columns.
Example 2: Input: 12 rows × 9 columns. Output: 12 rows × 9 columns.
Query 0: Input: 10 rows × 10 columns. Output: unknown.
Query 1: Input: 12 rows × 19 columns. Output: unknown.

The blue (1) outlines enclose rectangular regions. A region containing at least
one red (2) marker is filled yellow (4), including its original markers. Empty
regions, blue outlines and the exterior remain unchanged. Example 0 refutes
changing only marker pixels; example 1 includes both marked and unmarked small
enclosures; example 2 shows that exterior red markers must stay red.

## Probe before implementation

Using only challenge.json, a Python flood-fill enumerated four-connected
non-blue components, retaining those that do not touch the grid edge.
Observed (area, red markers, yellow cells in visible output):
- Example 0: (10, 0, 0), (10, 1, 10).
- Example 1: (1, 0, 0), (1, 1, 1), (10, 4, 10).
- Example 2: (10, 4, 10), (15, 0, 0).

These observations support the fill rule. A bounding-box implementation would
also fit the examples, but the region formulation avoids relying on a box's
location or size. All observed enclosures are rectangular; extension to other
closed shapes is an untested assumption. Colors are treated as fixed semantic
roles because the visible evidence uses only those roles.

## Revision 1

Implemented non-blue component flood-fill and recoloring only when a component
is enclosed and contains a red marker. This is the first actual solution
attempt. No deliberate negative or artificial failed revision was constructed.
The official visible-only check and finish receipts record the outcome.
Masked-query correctness remains withheld for independent scoring.

Official check: revision 1 completed, 3/3 visible examples passed, exit 0.
No additional revision was needed. I stopped because all visible cases fit
the proposed rule; query correctness is deliberately unknown.
