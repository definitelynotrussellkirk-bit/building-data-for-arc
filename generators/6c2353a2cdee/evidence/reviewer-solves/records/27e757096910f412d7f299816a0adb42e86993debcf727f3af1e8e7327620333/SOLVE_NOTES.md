# Solve notes

This is a **human work log**, not a captured model chain-of-thought or token trace.
I had earlier rule exposure during the generator review, so this solve is not
claimed blind. During the solve phase I consulted only `solve/challenge.json`.

## Revision 1 — transformed-support overlap

**Visible hypothesis.** The input has three 5×5 panels in columns 0–4, 6–10,
and 12–16. Panel colors identify objects but do not survive into the output.
Each block has one code on row 6. Across the four visible demonstrations, the
consistent code mapping is:

- 1: identity
- 2: 90° clockwise
- 3: 180°
- 4: 90° counter-clockwise

After transforming the three binary supports, count occupancy at every 5×5
coordinate. The visible outputs consistently encode count 0→0, 1→2, 2→4,
3→8.

**Probe.** Implement the mapping directly and replay all four visible pairs.
The key rival rejected by the examples is “ignore the code row”: asymmetrical
panels move to different coordinates, changing both the 4 and 8 cells. A second
rival, binary union, cannot explain the visible 4 and 8 values.

**Stopping rule.** Stop after a clean visible replay because all four transform
codes and all three nonzero overlap counts are represented in the supplied
examples; masked-query correctness remains withheld by policy.
