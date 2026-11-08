# Public creation notes: b9e38dc0

## Rule and parameter

The canonical rule identifies the modal background and the uniquely next-most-
frequent connected wall, infers cardinal flow from the wall tips, normalizes the
scene downward, and continues the observed stepped side walls. The enclosed
forward band is the paintable interior. Its earliest foreign marker determines
the dye; later foreign markers remain unchanged and cast same-column shadows.
The completed grid is rotated back to the input orientation.

The native family adds episode-fixed `obstacle_mode: opaque | transparent`, with
`opaque` as the byte-identical canonical default. Opaque mode computes the first
blocker row in each normalized column and excludes cells beyond that frontier.
Transparent mode retains the same geometry and dye inference but uses an empty
shadow mask. This creates a real A→intermediate→B dependency: inferred frontiers
control downstream painting.

## Constructive domain

The sampler emits six demonstrations and four queries, projected at supported
prefixes of 2–6 demonstrations and 1–4 queries. Palettes, flow orientation,
stepped-wall cadence, blocker placement, and query order vary deterministically
by seed. The largest profiles reach 30×30. Inputs are constructed directly;
there is no answer lookup, rejection filter, or retry loop.

The family admits exact-integer ARC rectangles whose wall is one eight-connected
component with two tips, a contiguous rear cap, complete equal terminal steps,
and a nonempty connected interior. Partial terminal steps, crossed virtual
boundaries, and ambiguous earliest dye rows are outside the constructive grammar.

## Current packet evidence

- `checks/public_eval_b9e38dc0/preflight/`: protected-Racket authoring preflight
  passed all four official labels and four 2-demo/4-query jobs. This is not owner
  qualification or acceptance.
- `checks/review-800deaecef69f120/b9e-tests-final.log`: 160 focused tests passed.
- `checks/public_eval_b9e38dc0/audit/compact-audit.json`: 176 protected Racket
  evaluations over two seeds, both settings, the alternate setting, 12 structural
  rivals, and four demonstration-learned role constants. No invalid candidate or
  surviving query disagreement was found. Transparent shadow-only survivors are
  retained as declared semantic aliases.
- `checks/public_eval_b9e38dc0/causal/witness.json` and replay: replacing the
  opaque frontier/shadow intermediate with transparent frontiers changes 51 cells
  while downstream painting remains the same operation.
- `checks/public_eval_b9e38dc0/export/`: 16 one-query public challenges passed
  saved-file conformance and 16 hidden-field byte-invariance mutations.

The adversarial audit is finite, not a universal uniqueness proof. Owner source
reconciliation, registration, native qualification, and acceptance remain
pending; no production authority or training state is changed here.
