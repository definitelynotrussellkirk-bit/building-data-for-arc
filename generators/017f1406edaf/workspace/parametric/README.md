# Native `count_scope` object-area family

This task-local family preserves the selected production generator and the exact
canonical Racket program. It varies one episode-fixed input-derived count:

- `count_scope = "row0"` — canonical/default. Count blue (`1`) cells only in
  row 0.
- `count_scope = "all_blue"` — alternative. Count every blue cell in the grid.

For either setting, the count is used as a target area. The rule scans monochrome
objects in row-major order, excludes blue objects and every object touching row
0, selects the first remaining object whose area equals the target, and returns
a blank grid with only that object painted cyan (`8`). `rules/count_row0.rkt` is
byte-for-byte the catalog authority. `rules/count_all_blue.rkt` changes only the
counted input scope and remains one standalone `rule!` expression.

`adapter.py` supports 2–6 demonstrations and exactly four private queries. Each
ordinary input contains both a unique eligible row-0-count object and a unique
eligible all-blue-count object, plus lower blue cells, a row-0-touching nonblue
decoy, and other eligible distractors. The two target objects swap vertical order
across examples, so neither a fixed location nor a fixed first-object shortcut
can explain the lesson. Inputs are setting-neutral, distinct, and deterministic.
The fourth query is a substantive 30×30 board with 148 nonbackground cells spread
across 14 rows and 27 columns.

The required sequential dependency is:

1. **A:** count blue cells in the episode-selected scope to derive a target area.
2. **Intermediate:** that input-derived integer target area.
3. **B:** find the first eligible nonblue, non-row-0 object of exactly that area
   and paint its cells cyan on a blank grid.

B cannot select an object before A supplies its size. The qualification-bound
witness substitutes the canonical row-0 count for an `all_blue` case; the wrong
intermediate selects a different object and changes the final output.

`self_audit.py` replays both native settings through protected Racket for seeds
0/17, demo counts 2/6, and all four queries. It also checks exact default identity,
matched inputs, deterministic replay, finite setting identification, six cheap
bypasses, stable count prefixes, target-location variation, public redaction,
64 additional generation seeds, and the 30×30 stress surface. The retained audit
is bounded evidence, not universal induction proof, owner acceptance, or training
admission.
