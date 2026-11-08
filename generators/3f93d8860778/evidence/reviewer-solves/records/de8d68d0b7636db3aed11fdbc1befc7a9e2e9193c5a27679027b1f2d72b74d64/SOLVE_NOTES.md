# Solve notes

## Hypothesis 1

The transformation acts independently by column. When a column contains exactly two nonzero cells and they have the same color, fill the inclusive vertical interval between them with that color. Leave singleton columns, columns with mismatched colors, and columns with three or more nonzero cells unchanged.

Evidence from the three visible demonstrations:
- Demo 1 consists only of clean equal-color endpoint pairs and fills each interval.
- Demo 2 leaves the mismatched `3/5` column and the three-marker color-5 column unchanged, while filling every exactly-two matching pair.
- Demo 3 likewise leaves the `8/9` mismatch, a singleton, and a three-marker color-9 column unchanged, while filling four clean pairs.

Implemented this rule directly without consulting reference code or labels.
