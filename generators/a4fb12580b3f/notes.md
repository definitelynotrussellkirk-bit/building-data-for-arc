# Working notes: a4fb12580b3f

## Current parametric extension

`workspace/parametric/` contains a separate native adapter with `mode=direct`
and `mode=largest_relay`. The default is the exact canonical Racket text;
the production generator and canonical authority are unchanged. The alternative
first binds the unique largest original component touching the blue anchor,
then recolors its original component neighbors as well as all anchor neighbors.
The anchor stays blue and expansion stops after one additional hop. An already-4
component remains eligible as the relay. This is a dependency on a derived
object, not an updated-grid simulation.

The constructive grammar supports independent dimensions 14..30, demos 2..6
(default 3), and queries 1..4. Four queries use 30×30, 14×30, 30×14, and 26×28. Modes
share input arrays. Components, competing branches, distant larger objects,
same-color distractors, third-hop continuations, cardinal/diagonal distinctions
and an already-yellow relay are represented explicitly. Larger canvases grow
reasoning-bearing objects. Query sampling is independent of demo count.

## Teaching repair and bounded evidence

The first draft's two demonstrations let a prefer-yellow-else-largest selector
survive while disagreeing on the first 30×30 query. Protected Racket reproduced
this for seeds 0 and 17; the retained seed0 witness changes 2 query cells.
The first demonstration now includes a smaller yellow direct competitor beside
its nonyellow largest relay. The second uses a truly largest yellow relay.
This refutes both preferring and ignoring yellow without increasing demo count.
The before witness and final checks are in the return's
`checks/a4fb12580b3f/prefer4-before/` and `self-audit-v2/`.

Final focused prototype tests: 82 passed. The protected-Racket self-audit covers
seeds 0/17, demos 2/3/6, four queries, 420 evaluations and 8 direct/16 relay rivals;
every rival is refuted by demonstrations in every retained lesson. Native
qualification covers both settings on both seeds with 3 demos/4 queries and 40
Racket evaluations. The causal witness substitutes the second-largest direct
component and changes 4 final cells on a 30×30 query. Finite rivals and sampled
seeds are the limits of these claims; no universal uniqueness is asserted.

## Public export and next action

`export_qualified.py` validates the current source-bound qualification and
execution before publishing only demos plus the first query. Public names
hash visible bytes. Settings, programs, answers, later queries and receipts
stay private. Its pure reveal helper adds no turn controller or count hints.

Native owner qualification/acceptance after integration is still required;
this return is reviewer-ready, not accepted or training-admitted. The inherited
production seed 73 diagonal-contact audit remains open for the unchanged
canonical sampler. Its finding is addressed in this new distribution only.
Imported associated notes remain in `evidence/associated_notes.jsonl`.
