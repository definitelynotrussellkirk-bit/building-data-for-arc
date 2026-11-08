# Exact-two directional composition — proposed native family

`composition=vertical_only` returns the selected canonical Racket source exactly.
`composition=vertical_then_horizontal` executes that vertical pass, then runs the
same exact-two rule horizontally on the completed intermediate. Counts and color
order are frozen separately at each pass. Overlapping paints use first appearance
order, not numerical color order. There is exactly one vertical/horizontal cycle.

A produces the filled vertical grid. B must inspect its per-row color counts:
new bars can create two occurrences, or a third bar can suppress a join. Offset
spans and unlike overwritten interior cells make this more than rectangle fill.
The wrong-order witness executes horizontal before vertical and changes the grid.
The private native witness is in `checks/2ab8c1aaa3e2/causal/witness.json` in the return.

## API and grammar

`generate(seed, {"composition": MODE}, demos=3, queries=4)` supports exact integer
seeds >=0, demos 2..6, and queries 1..4. Four queries is the authoring target;
query 1 and each prefix are identical when fewer are requested. Inputs do not
depend on MODE. Unknown settings and invalid/coercive counts fail closed.

The first two demonstrations are constructive contrasts, with shuffled colors
and reflected layouts. They teach exact counts, input versus intermediate counts,
overwrite behavior, pass order, and stopping after one cycle. Later demonstrations
vary placement. The first scene has reserved empty cells so incidental overlays
cannot erase the >=2 negative. The second uses two offset horizontal pairs to
refute repeated cycles. This is a restricted curriculum, not a claim about every
possible rule or every lawful input.

Input sizes range from 10x11 to 30x30, all outputs preserve dimensions. Larger
queries populate extra columns with genuine span endpoints and interior noise.
The 30x30 case touches every edge, has at least 55 input cells and at least 350
output cells across the retained sweep; it is not a padded copy of a small case.
The unchanged production generator remains bounded to 22x20; only this separate
parametric grammar extends to 30x30.

`public_turn_bytes(episode, query_index)` uses the native serializer and includes
only train input/output pairs and one test input. No settings, programs, answers,
future queries, ordinal metadata or query-count hint is exported. Hash these exact
bytes for public filenames. These helpers do not create a turn controller.

## Reproduce

From the outer packet directory:

```sh
python3 review.py run python3 generators/2ab8c1aaa3e2/workspace/parametric/audit.py --seeds 32 --out ../checks/2ab8c1aaa3e2/new-audit
python3 review.py task-tests 2ab8c1aaa3e2 --phase after --out ../checks/2ab8c1aaa3e2/new-tests
python3 review.py run python3 -m arcpuzzles parametric qualify 2ab8c1aaa3e2 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/2ab8c1aaa3e2/new-qualification --summary
```

Add `--regressions ../checks/2ab8c1aaa3e2` to replay the three retained frozen
before fixtures and their repaired two-demo lessons. The audit uses a real
protected Racket backend, never substitutes Python if it is unavailable.
The 32-seed sweep is Python diagnostic evidence; Racket checks 40 baseline labels
and 30 regression executions. Qualification independently executes its own jobs.

Current results: 320 episodes / 2,560 labeled-pair checks / 320 distinct inputs;
13 finite policies, no query-disagreeing survivors; 70 protected Racket audit
executions; 72 staged task tests. All 16 one-query public files pass the saved
export checker. Evidence is finite and author-reported, not universal uniqueness,
owner acceptance, measured learning benefit or training admission.
