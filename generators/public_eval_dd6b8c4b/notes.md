# public_eval_dd6b8c4b — current authoring design

Parent rule: flood non-6 cells from the single red marker; rank reachable maroon
cells by shortest four-neighbor path distance, and move up to nine into the green
3x3 box in row-major order, replacing removed cells with orange 7. Walls and
unreachable maroon cells remain. The red center is also a destination slot.

Native setting collection_order=nearest (parent) or farthest. The intermediate
is the reachable-cell distance map; ranking and capacity-limited selection consume
that map. Fresh mazes, moved targets, reachable and sealed maroon cells, below/full/
over-capacity lessons and 30x30 geometry preserve the reasoning.

Parent labels do not resolve a distance tie across the capacity cutoff. Reference
uses row-major ties as an explicit totalization. Generated over-capacity inputs
have tie-free nearest AND farthest cutoffs; no tie-resolution learning claim.

Validation: literal parents, independent hand cases, Python/Racket parity, finite
rivals, count/presentation stability, protected wrong-distance-map witness, privacy
and source-bound preflight. Owner registration and acceptance remain pending.

## Current verified handoff

All 5 supplied labels pass protected Racket. The exact new reference is copied
into canonical.rkt; nearest is the parent rule and farthest reverses only distance
priority among reachable tokens. Two demos defeat 13 finite rivals under both
settings. Fresh mazes include boundary exits and genuinely interior sealed
maroon pockets, not just unreachable corners. Destination painting follows exit
carving to prevent a lower/right exit from erasing the box.

The 30x30 seed-17 profile has 538 non-background cells, 45 reachable tokens,
and more unreachable tokens. Each setting moves 9 tokens (18 changed cells).
The causal witness substitutes Manhattan reachability/distances for the wall-aware
map and changes 2 final cells. Distance ties across the selection cutoff are not
settled by the official examples; the admitted generated grammar avoids those
cutoff ties. The total reference uses row-major order at a tie.

Default query presentation now mixes the source seed with the independent
presentation seed before shuffling all four pairs; an early stop selects only
a prefix of that complete permutation. Neither requested counts nor hidden
metadata alter the first public view.

Current evidence is checks/public_eval_dd6b8c4b/preflight-current/ and audit-current/.
Earlier successful snapshots are superseded; failed check logs remain as honest
regressions. Full catalog task-tests cannot run before owner registration.
Direct and independently relocated tests pass. Registration, source approval,
unchanged native qualification, and actual owner acceptance remain pending;
training_admitted=false. Final review was author self-review, not independent.

## Current repeated-return reconciliation

Exact nearest/farthest programs/default preserved. Add the upper-median-distance setting: derive reachable geodesic distances, select the upper median, rank by distance from that pivot, then collect within capacity. Retain both original and median-cutoff-separated maze banks. Two returns carry identical new bytes and are aliases. Four distinct queries now have a seed-shuffled native order with stable count prefixes. Evidence: `evidence/reconcile-17/`. Private native qualification, protected causal/relocated execution, fresh private acceptance and a fresh accepted episode passed. Live owner publication and training admission remain separate.
