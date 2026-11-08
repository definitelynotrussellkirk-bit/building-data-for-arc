# Region-depth band propagation: public_eval_13e47133

## Rule and settings
The general reference identifies the modal background and most frequent remaining wall color. It partitions nonwall cells by four-connectivity, repeatedly erodes all eight neighboring directions to obtain inward layers, and reads a palette independently for each region. Cues label their actual depths; absent earlier entries use background. The deepest cue fixes sequence length. A cue-free region has a one-color background palette. Walls remain unchanged. Protected Racket reproduces all three original demonstrations and both supplied 30x30 test labels.

`propagation=cyclic` is byte-identical to the root reference. `bouncing` traverses the recovered palette forward and backward without repeating endpoints. One- and two-color palettes are legitimately equivalent, so visible lessons also contain a deep three-color region. Geometry-derived region depth and recovered palette are consumed by the final painter, not substituted by rectangular crop coordinates.

## Sampling and teaching
The standalone generator and parametric sampler are byte-identical. Inputs vary dimensions, four rotations, vertical split, attached closed box and resulting concavity, optional extra divider, cue corners, one- through three-color palettes, background outer entries, repeated same-depth cues and cue-free chambers. Repeated cues decouple palette length from cue count. Two settings receive identical inputs.

The native adapter accepts 2–6 demonstrations and exactly four distinct queries. Earlier demonstrations and the independent query bank are prefix-invariant across demonstration counts. The fourth query is substantive 30x30. Public delivery independently shuffles the four-query order and reveals only the current query, with no hidden settings, programs, answers, future inputs or total-count hints.

## Verification and limits
The task-local suite has 27 passing tests, including all originals, independent geometric fixtures, palette/band behavior, request validation, input neutrality, prefix invariance, canonical bytes and standalone relocation. A 32-seed audit covers 192 episodes, 1,472 labeled pairs, demo counts 2/3/6 and 25 policies. It rejects all harmful named survivors, including bounding-box/cardinal layers, global/sorted/reversed palettes, cue-count period, fixed-two, solid and stripe rules. These finite audit labels are Python claims; separate original, preflight, six-demo boundary and causal receipts use protected Racket.

Authoring preflight passes for two settings x seeds 17/43, two demos and four queries. Forty additional protected labels cover six-demo boundaries at seeds 0/31. Sixteen sequential public views pass exact-byte, masking and first-turn mutation checks. The causal foil preserves the recovered palette but replaces true inward layers with bounding-box edge depths: 109 depths differ in the 445-cell concave region, and 82 final cells change in the retained 30x30 query. Fresh protected replay confirms the outputs.

The reference assumes modal-background/wall identifiability and region-local cue sequences. It resolves conflicting same-depth cues by modal color with a low-color tie break, but generated inputs use consistent cues. The constructive sampler is not exhaustive over arbitrary wall topologies, palettes or legal puzzles. Finite rival rejection is not universal uniqueness.

## Handoff
This remains unregistered authoring work. Current `preflight-final` binds exact source bytes and is not owner qualification. Catalog `task-tests` returns Unknown puzzle until registration; complete local and relocated-generator tests pass. Owner registration, native qualification and fresh acceptance remain required, with no training admitted. Shared authority and immutable public-parent provenance were not changed.

## Current repeated-parent reconciliation

Preserve exact cyclic/bouncing rules and broad concave/rectangular sampler. Retain both incoming standalone repairs and finite rival evidence; measure constructor aliases explicitly. Current evidence resides in evidence/repeat-tenth-union. Private native acceptance and root publication are separate.
