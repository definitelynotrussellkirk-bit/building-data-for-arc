# Solve work log

## Exposure before solving

I did not inspect this task's generator, Racket rule, reference solution, private
query labels, notes, or audit evidence. Before `blind prepare` I accidentally
opened packet-level orientation documents (`START-HERE.md`, `WORK/WELCOME.md`,
`WORK/ARC-DESIGN.md`, `WORK/PARAMETRIC-RULES.md`, and repository overview text).
Those documents did not reveal this task's rule or examples. I therefore record
no earlier task-rule exposure and no reference consultation, while disclosing the
ordering mistake here.

## Revision 1 — zero-mask self-product

**Visible pattern.** Each output side is the corresponding input side squared.
Splitting an output into input-sized blocks showed that blocks appear exactly at
input zero cells. Every present block is the input's zero-cell mask, painted with
the single nonzero input color. Thus the output foreground mask is the Kronecker
product `Z ⊗ Z`, where `Z[r,c] = 1` iff the input cell is zero.

Evidence from the visible examples:

- Example 0 has 3 zeros and 9 output foreground cells (`3 × 3`).
- Example 1 has 4 zeros and 16 output foreground cells (`4 × 4`).
- Example 2 has 5 zeros and 25 output foreground cells (`5 × 5`).
- In every example, the nonempty outer block coordinates and the foreground
  coordinates inside each block are both exactly the input zero coordinates.

**Alternatives rejected.** Repeating the nonzero mask would give 36, 25, and 121
foreground cells instead, contradicting the visible counts. Ordinary tiling of
the input also conflicts with the all-zero blocks.

**Implementation.** For each outer input cell, emit either an all-zero block or
the zero mask painted with the unique nonzero color. A local test against visible
example 0 was first run against the template and failed with `NotImplementedError`;
then the implementation was added. Remaining uncertainty is limited to whether a
hidden episode could contain multiple nonzero colors; the visible contract always
uses one, so the solver rejects ambiguous inputs rather than guessing.
