# Working notes: 683b2102b08c

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## Native attachment-side extension (review-c864adfb6c8c982e)

The native prototype preserves the exact approved left-attachment rule and adds
right attachment at the main mask's rightmost column. Both preserve one-column
bounding-box overlap, secondary overwrite and floor centering. A counts complete
lower color masks; its selected majority mask/bounds feed B's attachment location.
The canonical generator and reference remain unchanged.

The adapter supports independent 2–6 demo / 1–4 query requests. Inputs match
across settings, demo/query streams preserve prefixes, and the four-query path
covers 8×8 through dense 30×30 (14×9 main and 9×10 secondary masks). Two constructive
demos preserve disconnected-mask, odd-centering and overwrite distinctions.

Self-review found and repaired a concrete hole: a tallest-mask selector fit seed
8's original three demos but failed its equal-height third query. The second
core demo now gives the masks equal heights, makes the minority occur first,
and reverses bbox-area ranking; the first demo reverses encounter order. This
rejects stable-height, height/area, and first/last-encounter selectors within two
demos. The original protected witness is checks/683b2102b08c/tallest-mask-before.json.
The regression failed before this change and passes after it. Current bounded
self-review rejects all 21 declared rivals for seeds 0/8/17, both settings, and
2/3/6 demos (18 configurations, 1,320 protected Racket grid evaluations).
Eight focused tests pass, including exact default-source identity, input/count
independence, generation boundaries, malformed requests and RNG isolation.
No universal-identifiability or measured training-gain claim is made.

Current source/inventory and qualification are the owner handoff; exact-source
owner acceptance and training admission remain separate. The reusable task-local
verify.py checks labels, teaching, counts, density, and public first-turn bytes.
The source packet is an isolated extraction without Git metadata; checks remain
focused on this new prototype, as required by the packet.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/683b2102b08c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
