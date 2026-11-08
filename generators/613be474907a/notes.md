# Current decisions: 613be474907a

## Proposed parameter

Use one episode-fixed `center` parameter: `preserve` (canonical), `near` (left/top),
or `far` (right/bottom). It changes ownership of the sole middle line of an odd
gap; even gaps agree. This is a small semantic extension of the original block,
bounding-box and half-gap reasoning. Geometry, palette and count controls are
sampling choices rather than additional rule parameters. Input sampling is
independent of `center`, making same-seed counterfactual comparisons possible.

The Python API and CLI default to `preserve`, which returns the exact canonical
program with normalized rule hash `adc52fde010d`. The approved generator,
canonical ledger, fixtures and approval records are unchanged. Near/far remain
proposed variants with their own materialized Racket programs.

## Teaching and export decisions

Minimum two demonstrations expose both orientations, odd-gap ownership,
horizontal precedence in diagonal separation, and spatial rather than numeric
color roles. Each requested query is checked against all parameter hypotheses
and six declared shortcuts still consistent with the demonstrations. Query
answers never eliminate hypotheses. The negative regression shows why even-gap
examples alone cannot teach an odd-gap query. This is finite rival coverage,
not a proof over every possible rule or a measured learning result.

Expose demonstration and query counts independently (2..32 and 1..32). Exact
height/width overrides support 7..30. The bounded sampler rejects exhausted
requests; it does not duplicate pairs or silently reduce counts. Public files
contain only demonstrations and query inputs and are named from exact visible
bytes with the existing shared helper. Keep the entire private directory,
programs, manifests and source receipts outside the solver's input.

## Reusable support tool

`workspace/zip_backed_package.py` allows native delta packaging when a complete
checkout cannot be materialized. It binds initially absent source paths to an
immutable, fully verified input ZIP and an externally pinned inventory hash.
Present bytes always win; later deletion of a previously materialized file,
changed shared bytes, symlinks and baseline changes remain errors. The selected
task and frozen authorities must be present. It invokes the issued native
builder unchanged. This is a task-local proposal for possible shared adoption,
not a general virtual filesystem or verification of a full physical extraction.

## Evidence and next action

The current code passed 52 focused tests (25 prototype, 27 packaging helper).
Retained seed 17, 73, 109 and 211 runs contain ten complete episodes, 26 demos,
40 distinct-within-episode queries and 66 executed Racket labels, including
7x7 and 30x30 cases. Exact commands, hashes, programs and private teaching
receipts are in the return's `checks/` tree. The README contains portable commands.

A useful next action is maintainer replay of these specific receipts and review
of the proposed semantic and export interface before any production integration.
No approval or training admission is inferred. Broader seeds/rivals and the
unsupported below-7 size override range remain outside this prototype evidence.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
