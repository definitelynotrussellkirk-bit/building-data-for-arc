# Working notes: 2534c7164e36

## Current decision — episode-fixed panel priority prototype

The selected production generator remains version `3.0.1`, SHA-256
`eab765a3418f667520bfac6419a2730a4666dcb1e3fb54508c5cc117ef051ac5`.
Its canonical transformation and `RULE_HASH = 3d9402d2c7a5` are unchanged.

A task-local prototype under `workspace/parametric/` adds one episode-level
parameter, `priority_order`:

- `q1_q2_q3`: canonical/default `Q1 > Q2 > Q3`; exact Racket SHA-256
  `3d9402d2c7a5a95e4e76a0cac9b607451694f4f32a7a501664be99032ab453e1`.
- `q1_q3_q2`: proposed `Q1 > Q3 > Q2`; exact Racket SHA-256
  `da3fc34aa6f5f7414d2b2e2a864a0a1abe35bc79cb5693fb1588aad078917534`.

Only the two lower-priority clauses differ. The default program is byte-exact
canonical, and the prototype rejects variants that cannot be restored exactly
to that authority. Inputs are generated independently of the hidden setting
from the lawful `generalized` family, whose all-eight occupancy coverage gives
each input a Q2/Q3-only witness cell.

Each retained setting has two Racket-labelled demonstrations and four distinct
queries. The other setting is the declared rival: demonstrations refute it, and
it predicts a different answer for every query. The public projection contains
only visible demonstrations and query inputs. Its filename hashes the exact
visible bytes, so hidden settings, seeds, programs, and query labels cannot
alter the public ID.

Evidence: `checks/parametric/2534-priority-order/report.json`. It records two
settings, four demonstrations, eight queries, 12 episode labels, 12 canonical
labels, zero query ambiguities, and a successful replay of both public files.

The inherited generator test was also made portable without changing its
assertions: it now uses `find_root`, `canonical_path`, and
`load_selected_generator` rather than a fixed parent depth and runtime-only
module path. The supported task-test wrapper passes after this repair.

## Limits and next useful action

This is an unapproved prototype, not a production API, canonical rewrite, or
training admission. Evidence covers two consecutive seeds and one declared
alternative, not every possible ordering or rival program. The generalized
input family is deliberately stronger than canonical-linked scenes. A future
owner decision can either keep this as an opt-in episode writer or promote the
parameter through the normal generator/version/approval process after broader
schedule and deduplication evaluation.

## Current decision — content-addressed public batch preflight

The retained public-export finding is resolved in the task-local prototype without changing either Racket rule or the production generator. `materialize()` now constructs and validates both private episodes entirely in memory, derives the exact visible public bytes and IDs, rejects a duplicate visible payload (or theoretical ID collision) before creating the output tree, and commits public files in lexicographic public-ID order rather than episode/seed order. Private episode paths remain in episode order and map explicitly to their public IDs.

Focused regressions cover the two failure modes directly: seed `0` previously emitted IDs in reverse lexical order, and two Racket-labelled episodes with identical visible content but different private metadata previously overwrote one public file. The latter now raises before the output directory exists. Replayed evidence at `checks/parametric/2534-priority-order-public-batch-v2/` retains two settings, four demonstrations, eight distinct queries, 12/12 canonical labels, zero ambiguities, sorted public writes, and a passing verifier receipt.

No variant approval or training admission follows. The next useful action is downstream owner evaluation of the opt-in episode writer; broader undeclared-rival and multi-seed duplicate rates remain unmeasured.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/2534c7164e36/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
