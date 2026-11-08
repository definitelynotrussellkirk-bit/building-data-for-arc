# Post-repair visible-only solve: 312fb4bdff00

Earlier exposure: YES. I inspected this task's Racket rule and developed its
generator before starting this phase. This is an exposed implementation attempt,
not independent blind induction. During this solve I consulted only the visible
challenge and my Python; I did not reopen the generator, Racket rule, workspace
oracle, canonical solutions, or private labels. These notes summarize experiments;
they are not a captured token-level model conversation.

## Revision 1
The five visible examples show a target color in the header, square panels divided
by full-height 8 columns, recoloring of a matching candidate shape, and one absent
match returning [[0]]. Several output locations differ from the query's location,
so comparing absolute coordinates or simply recoloring the query fails visibly.

I wrote a fresh grid-transform implementation: partition the body, compare each
candidate's translation-normalized nonzero support under rotations/reflections,
and preserve the entire transformed candidate grid on output. Candidate order
and the conventional transform order are consistent with the examples and with
my earlier exposure; the examples alone may not establish every tie ordering.

The supplied stub was checked only as scaffolding (checks/repair/exposed-solve-stub.json),
not submitted as a failed natural solve. One actual solution revision was submitted.
No deliberate wrong rule was presented as a natural failure. I stopped after the
visible checker because masked query labels are unavailable and no further visible
counterexample justified a change.

Remaining uncertainty: masked correctness requires independent maintainer scoring;
visible agreement is not proof that the lesson identifies every possible rule.
