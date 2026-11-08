# Current notes: 2602c3d31d21

## Decision

The task-local native parametric family varies one episode-fixed rule choice: the pairwise distance used to compute each keyed object's signature.

- `squared_euclidean` is the default and preserves the canonical Racket program byte-for-byte.
- `manhattan` is the bounded alternate and changes only the guarded pairwise-distance expression.
- Inputs are sampled independently of the private metric, so matched settings receive identical demonstrations and queries and differ only through labels.
- Supported counts are 2–6 demonstrations and 1–4 queries; the promotion path qualifies four distinct queries.

Exact program bindings:

- canonical squared-Euclidean SHA-256: `a99125d5b90022542887f6e79b1b36dd0a976abd38724b2d59f766eddf5a1c5d`
- Manhattan SHA-256: `82b254883dc7ab3fa591a3714ed6c8b650c8c1e5c70cbb67e0d6625a5d2ddf3e`
- canonical normalized rule hash: `af35f40d51ca`
- source manifest SHA-256: `686506ad295db0b4637ba32e8d400ecc7562a91a32b4f909e5c9175fb52dea17`

## Teaching and coverage

The first demonstration contains two constructive collisions that separate the metrics without increasing the minimum demonstration count: one pair is equal only under Manhattan distance and another is equal only under squared-Euclidean distance. Consequently either setting is the sole survivor against the declared metric rival from two demonstrations. The four queries are distinct from one another and from all demonstrations.

The maximum-size query is a substantive 30×30 input with seven keyed bodies and 60 nonzero body cells. Shapes touch row and column boundaries and the right-edge key is used by the rule; the grid is not a padded small example.

The bounded self-review executes labels in protected Racket and refutes four plausible shortcut families for each setting: congruence, body size, always-equal and always-unequal. This establishes only finite tested-rival coverage, not universal uniqueness.

## Sequential dependency

- Step A: compute the selected pairwise-distance sum for every keyed body shape.
- Intermediate: the ordered vector of per-shape metric signatures in right-edge key order.
- Step B: compare those signatures pairwise to emit the labeled equality matrix.

Step B cannot choose an off-diagonal block before Step A supplies both referenced signatures. The protected-Racket witness replaces the signature expression with a wrong constant intermediate and changes the final output for both settings. Recorded intermediate vectors are `[4, 6, 30, 30]` for squared Euclidean and `[4, 4, 18, 20]` for Manhattan.

## Verification and local repairs

- Native task suite: 37 passed, including 3 subtests.
- Native qualification: 2 settings × 2 fresh seeds, 3 demonstrations and 4 queries per job, protected Racket, one demonstration-only survivor per job.
- Sequential replay: 2 cases and 4 protected-Racket evaluations, status `owner_replayed`.
- The pre-existing task test was made packet-portable by loading through `reviewer_support.load_selected_generator` instead of a missing installed package path.
- Authority comparison now follows the retained records' explicit `preserved_executable_source` status: raw and target code remain identical to each other, while equivalence to canonical authority is checked by normalized rule hash rather than formatting identity.

## Handoff limits

This is a source-bound, reviewer-qualified prototype. Owner integration must verify these exact bytes, rerun native qualification and acceptance, and keep `training_admitted` false unless that separate owner gate succeeds. The optional peers `11221f58af4b` and `174b3ec6b87c` were not run because the available effort was used to finish MAIN.
