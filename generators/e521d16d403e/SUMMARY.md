# e521d16d403e

Extract the tight bounding box of the largest eligible left-right symmetric
object. Objects are same-color four-connected components. Eligibility requires
bbox width greater than one and exact equality of every raw bbox pixel with its
left-right reflection. Rank by occupied cells, not bounding-box area. The
canonical Racket authority is unchanged at rule hash `9d224076bec5`.

The default generator cycles through four ordered profiles. Compact profiles
use a six-cell 2×4 winner, a five-cell 3×3 eligible cross, a larger width-one bar,
and a larger asymmetric block. Broad profiles use varied symmetric winners,
smaller eligible decoys, larger asymmetric objects, and disconnected components
sharing the winner's color. Profiles reverse scan order; profiles 0 and 2 put a
smaller eligible object below the winner. Three demonstrations from any four
consecutive default draws therefore retain witnesses against all ten declared
rivals, including the canonical-fitting `bottommost_lr` shortcut.

The selected curriculum requires a unique eligible maximum and at least one
noneligible distractor. Six exact integer controls are supported: grid
height/width 10..22, winner bbox height 2..6, winner bbox width 2..7,
noneligible-component count 1..3, and smaller-eligible-decoy count 0..2. Unknown
controls, noninteger seeds/indices, and negative sample indices fail explicitly.

A separate native candidate under `workspace/parametric/` retains canonical
`occupied_cells` and alternative `bbox_area`, and adds `occupied_anchor_partner`:
select the occupied-cell anchor, then crop its disconnected same-color partner.
It supports 2–6 demos and independently 1–4 queries, including substantive 30×30
scenes. Reviewer native qualification passed; owner acceptance remains pending.

Kind: `per_puzzle`. Reviewed production version: `4.1.0`. Final source SHA-256:
`b012fe138cc2497dc1615e75815a0fc1f05cb5577e5f162cfc942702f8ec685f`.
Approval remains a catalog/maintainer decision, not a consequence of this review.
