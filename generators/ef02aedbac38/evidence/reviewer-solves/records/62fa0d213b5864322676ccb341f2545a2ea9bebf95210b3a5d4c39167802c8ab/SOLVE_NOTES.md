# Solve work log

## Exposure declaration before solving

I had already reviewed this task's generator and authority before this required
post-repair solve, so this attempt is **not blind**. After `solve prepare` I did
not consult the generator, Racket rule, reference solutions, private labels, or
previous solve explanations; I used only the displayed visible examples.

## Revision 1 — literal color-5 mask

**Visible pattern.** Every input has exactly two nonzero colors: literal color 5
and one companion color. Across all four demonstrations, output dimensions are
unchanged. A cell is the companion color exactly where the input cell is 5;
all cells holding the companion color become 0. This explains both sparse and
dense cases, including the 25×6 example where most input cells are 5.

**Implementation.** Find the sole observed value different from 5, then map each
input cell independently: `5 -> companion`, `companion -> 0`.

**Alternatives considered.** Selecting the rarer color fails the dense 25×6
example, where 5 is the majority. Selecting a connected component or copying a
shape also fails because the marked cells can be disconnected. Literal color 5
is the invariant supported by every demonstration.

**Remaining uncertainty.** The visible examples imply the input always contains
5 and exactly one companion color. The solver intentionally relies on that task
grammar rather than inventing behavior for malformed inputs.
