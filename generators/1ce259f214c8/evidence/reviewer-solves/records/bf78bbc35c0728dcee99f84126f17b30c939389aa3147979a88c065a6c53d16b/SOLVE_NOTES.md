# Solve notes

This is a human work log, not a token-level model trace.

## Earlier exposure

I had already inspected this task's generator and rule-related review material before the fresh-solve phase began. I therefore declare **earlier rule exposure: yes**. During this solve phase I did not consult the generator source, Racket authority, reference solutions, private query labels, or prior solve artifacts; I used only `solve/challenge.json`.

## Revision 1 hypothesis

Each input has one full-height gray-5 divider that splits it into equal left and right panels. Colors identify the two objects but their particular values do not matter. At each relative panel coordinate:

- output 8 when exactly one panel is occupied by a nonzero cell;
- output 0 when both panels are empty or both are occupied.

This is occupancy XOR. The visible examples include left-only, right-only, and overlap cells, including activity on different borders and corners, so fixed-side copy, OR, AND, directional difference, and border-zero variants do not explain all five demonstrations.

## Implementation

`solution.py` locates the unique full-height gray divider, verifies equal panel widths, compares nonzero occupancy coordinate by coordinate, and emits 8 for exclusive occupancy. No color-specific or size-specific constants are used beyond the structural divider and output color visible in the examples.
