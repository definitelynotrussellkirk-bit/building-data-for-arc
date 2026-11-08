# Blind solve notes — 2ca60ab198d6

This is a human-visible-example work log. I did not inspect the generator,
reference rule, private labels, prior solutions, or audit material.

## Observations

- Every output row is exactly one input row with its first cell removed.
- The retained input rows are precisely those whose first cell is color `7`.
- Output row order is unchanged.
- The examples vary in height, width, palette, the number of qualifying rows,
  and in whether additional `7` cells occur later in a row. This rules out
  selecting rows merely because they contain a `7`; the first column acts as a
  row marker.

## Hypothesis

Treat the first column as a selector column. Keep each row beginning with `7`
and strip that leading marker. Return the resulting rows in original order.

## Probe against all visible examples

For each training pair I manually matched every output row back to its source:

- train 1: source rows 1, 2, 4, 7;
- train 2: source rows 1, 2, 7, 8;
- train 3: source rows 2, 4, 6;
- train 4: source rows 5, 6.

In every case these and only these rows begin with `7`, and removing column 1
reproduces the output exactly. I therefore used this as the first solution
revision rather than manufacturing an incorrect attempt.
