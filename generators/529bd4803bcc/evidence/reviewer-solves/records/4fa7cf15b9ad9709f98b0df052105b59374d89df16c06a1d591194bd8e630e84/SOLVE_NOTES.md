# Solve work log

## Prior exposure

I had not opened the task's generator, Racket rule, notes, reference solutions,
private query labels, or audit evidence. I used only the visible examples printed
by `python3 review.py blind prepare` and the generated solve stub.

## Revision 1 — singleton seed fills its compartment

The gray cells (`5`) act as walls. Treat every four-connected component of
non-gray cells as a compartment. Count colored cells in that compartment, where
`0` is empty background and values other than `0` or `5` are seeds.

- If the compartment contains exactly one colored seed, fill the whole
  compartment with that seed's color.
- If it contains no seed or more than one seed, clear the whole compartment to
  `0`.
- Preserve every gray wall cell.

Evidence from the visible examples:

- Train 0 has one compartment with three blue seeds and another with one blue
  seed. Only the singleton-seed compartment becomes blue.
- Train 1 has a compartment containing three differently colored seeds and a
  separate compartment containing one red seed. Only the latter is filled red.
- Train 2 has two singleton-seed compartments, filled blue and red, while a
  compartment containing three green cells is cleared.

I considered rules based on seed color, compartment size, or choosing only one
region globally, but Train 2 rejects those alternatives because two differently
sized regions with different singleton colors are both filled.

Implementation uses a four-neighbor breadth-first search over cells whose value
is not `5`, then rewrites each complete component according to its seed count.
