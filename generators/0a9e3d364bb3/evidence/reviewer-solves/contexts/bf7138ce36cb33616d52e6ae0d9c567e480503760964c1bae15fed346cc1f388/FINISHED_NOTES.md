# Solve work log

## Exposure declaration

Before this post-repair solve I had reviewed and edited this task's generator and had seen its rule-related tests and authority checks. Therefore this is **not blind** and `earlier_rule_exposure` must be recorded as yes. From `solve_episode.py prepare` onward I kept the generator, Racket source, reference solutions, private query labels, and earlier solution explanations closed. I used only the visible examples printed by the solve episode and my own Python.

## Visible-example inference

All seven examples preserve the grid shape and contain:

- a unique 2×2 block of four distinct nonzero/non-8 colours in one corner;
- an L-shaped separator of colour 8;
- a rectangular body in the opposite corner containing zeroes and one or sometimes two other colours.

The 2×2 block acts as a quadrant key in its displayed orientation: top-left, top-right, bottom-left, bottom-right. In each body, occurrences of one marker colour are replaced by the matching key entry according to their position in the body's bounding rectangle.

The marker is the first nonzero/non-8 body colour in ordinary row-major reading order. Example 2 is the decisive distractor case: colour 2 occurs first and is recoloured, while the later colour 1 remains unchanged. Example 6 similarly recolours the first colour 4 while preserving later colour 3. Thus the rule is not “recolour every nonzero body cell.”

Examples place the key in all four corners, so the body bounds must be derived from the key corner rather than hard-coded. Example 3 contains marker cells on an exact body midpoint; the observed output assigns an exact midpoint to the bottom/right half. I implement quadrant selection with strict `<` against twice the inclusive bounding-box midpoint, making equality bottom/right.

## Revision 1

Implemented:

1. locate the unique corner 2×2 key;
2. derive the opposite `(h-2)×(w-2)` body;
3. find the first coloured body cell in row-major order and use its colour as the marker;
4. copy the input and recolour only marker cells by body quadrant using the four key entries;
5. leave zeroes, separators, the key, and any later body colour unchanged.

Remaining uncertainty before checking: only malformed inputs with no unique key are outside the visible grammar. The two masked queries appear to follow the same grammar, including one top-left key and one top-right key.

## Check result and stop decision

Revision 1 executed successfully and matched all 7/7 visible training outputs. I made no further revision because every visible discriminator is covered: all key corners, a marker outside the key, an unchanged later distractor colour, and an exact midpoint. Masked-query correctness remains intentionally unknown to this solve process.
