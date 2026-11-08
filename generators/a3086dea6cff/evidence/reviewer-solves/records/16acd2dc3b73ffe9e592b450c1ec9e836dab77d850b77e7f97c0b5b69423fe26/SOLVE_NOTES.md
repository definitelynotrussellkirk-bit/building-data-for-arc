# Solve work log

## Exposure declaration

Before this sealed solve I had already inspected the generator family and its
rule while repairing it. I therefore cannot claim an unexposed human-style
solve. During this solve episode, however, I consulted only `challenge.json`,
this solution, these notes, and the visible-only check command. I did not open
the generator, Racket authority, reference solutions, private labels, or any
prior solution explanation after `prepare`.

## Revision 1

### Visible evidence and hypothesis

Across the three training examples, each nonzero color behaves according to
its global occurrence count and alignment:

- A color appearing exactly twice in one row is filled inclusively between its
  endpoints (training 1: colors 9 and 2; training 2: color 3; training 3: color
  3).
- A color appearing exactly twice in one column is filled inclusively between
  its endpoints (training 1: color 6; training 2: colors 1 and 9; training 3:
  colors 8 and 4).
- A color appearing three times is not connected (training 2: color 5).
- A twice-occurring but diagonally displaced color is unchanged (training 3:
  color 2).

The examples also identify crossing precedence. In training 1, vertical 6 is
encountered first in row-major order, then horizontal 9; their intersection is
9 in the output. In training 3, vertical 8 is encountered before horizontal 3;
the intersection is 3. Thus eligible colors are processed in order of their
first row-major occurrence, with later segments overwriting earlier ones.

### Program

Collect positions for each nonzero color while scanning row-major. In that
insertion order, connect only two-cell colors sharing a row or a column. Leave
all other colors untouched. Draw directly into a copy so later eligible colors
win at crossings.

### Alternatives rejected from visible examples

- “Connect every repeated color” fails on the three 5s in training 2.
- “Connect every pair with an L path” fails on color 2 in training 3.
- “Always let vertical or horizontal win” conflicts with the two visible
  crossings; first-occurrence processing explains both.

### Remaining uncertainty before check

The test examples contain one triple and one nonaligned pair, so the main
shortcut exclusions are represented. The only material uncertainty is whether
an unseen crossing follows the inferred first-occurrence precedence, but both
visible crossing cases support it.
