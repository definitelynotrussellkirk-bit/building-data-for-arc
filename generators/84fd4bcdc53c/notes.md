# Working notes: 84fd4bcdc53c

## Current canonical behavior and collision repair

The canonical Racket rule remains unchanged: connect each color's markers in
row-major order with horizontal-then-vertical paths. The ordinary sampler keeps
each color's sampled 2–4 endpoints on distinct rows and columns. Explicit
degenerate textures retain their existing separate behavior.

Cross-color input-cell collisions previously caused the later endpoint to be
silently skipped. The source-bound witness is seed 6, sample index 0: medium
sampled three color-1 endpoints but retained only one; hard retained only one of
two color-6 endpoints. Both grids passed the existing self-check. The repair
keeps the sampled row and selects a free column while reserving the color's
other columns. This is a finite constructive choice: each earlier color can
occupy at most one cell in that row, and the supported widths leave spare
columns. There is no retry loop or oracle-dependent sampling. The existing
VERSION/seed stream is retained, so draws without a collision stay unchanged.

## Focused evidence and limits

`workspace/probe_endpoint_collisions.py` retains both witnesses and executes
selected labels through `Catalog.apply(..., reference="canonical")` in Racket.
The bounded final probe checked 50 draws: those two recipes plus eight seeds at
each actual minimum and maximum size for easy, medium, and hard. It found no
endpoint-count or distinct-row/column failures and executed eight labels with
matching canonical rule identity. Supported sampled shapes in that probe range
from 7x8 through 19x20; the canonical sampler does not expose 30x30.

The exact old/new source hashes, recipes, full selected inputs, Racket outputs,
and command receipts are under `checks/84fd4bcdc53c-review/` in the review return.
The regression pins the historical seed stream and checks the complete retained
endpoint counts. It failed against the old sampler and passes with the repair.
The first after-run revealed a too-small expected count in the medium fixture;
tracing the original sampled coordinates established three endpoints, and the
assertion was strengthened accordingly.

This is a bounded collision repair, not a full battery, control-surface audit,
lesson-identifiability proof, or parametric variant. The self-check's historical
acceptance of intentional single-cell/empty degenerates is unchanged; ordinary
endpoint counts are verified directly by the regression and bounded probe.

## Current parametric build: L-bend order

The reviewer-ready family keeps the exact canonical
`bend_order=horizontal_then_vertical` program and adds
`bend_order=vertical_then_horizontal` on identical visible inputs. Stage A
orders each color's endpoints row-major and constructs the selected L-bend trace
between consecutive endpoints. Stage B renders those input-derived traces in
ascending color order with first-color-wins collision handling.

Current evidence is under `workspace/parametric/evidence/`, with native
qualification and the source-bound wrong-intermediate replay under
`checks/84fd4bcdc53c/` in the return. The bounded audit covered seeds 0/17/211,
both settings, demo prefixes 2/3/6, four queries, nine named rivals, public
masking, and substantive 30x30 routing. Fresh task-local regression: 10/10
passed. Production `generator.py` and canonical authority are unchanged. Next
useful action is owner integration followed by fresh exact-source qualification,
witness replay, and explicit acceptance; training remains unadmitted.
