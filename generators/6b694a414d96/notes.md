# Working notes: 6b694a414d96

## Review `review-a0b13fb270e8873e` — canonical-domain and curriculum repair

### Reproduced defect

The frozen `2.2.0` source encoded one implementation-specific picture of the
rule: a single horizontal strip of rooms separated by full-height wall columns.
Its validator consequently rejected all three labeled canonical inputs with
`door color 7 should occur only inside wall columns`; the canonical examples
contain both horizontal and vertical room boundaries. Six ordinary baseline
samples had full-height separators and no full-width separator. The exact
source-bound replay is retained in
`checks/root-cause-before/6b694a414d96-canonical-rejection.json`.

This was not only a validator bug. The default sampler could not teach vertical
door adjacency or distinguish direct graph neighbors from rooms reachable after
two or more doors. The canonical pairs themselves admit the transitive-closure
shortcut, so a lawful generated second-hop witness is required.

### Repair

Version `3.0.0` replaces the strip sampler with bounded closed 2-D lattices of
rectangular rooms. Colors `1` and `9` are walls, color `7` cells are doors, and
non-wall 4-connected components are parsed as rooms. The Python mirror now
implements the same room graph as the unchanged Racket authority and accepts
all three canonical pairs.

The exact override axes are `rooms_r=2..4`, `rooms_c=2..5`, `room_h=2..5`,
`room_w=2..4`, and `wall_color in {1,9}`. A seed-rotated three-slot schedule
covers:

1. a horizontal-door example,
2. a vertical-door example, and
3. a corner-seed example with a guaranteed graph-distance-2 room.

Every complete default window therefore refutes transitive closure,
fill-all-nonseed, horizontal-only, vertical-only, and seed-plus-neighbors
competitors. `transitive_closure` is separately declared as the one
canonical-fitting shortcut and is killed by the second-hop profile.

### Tests and reusable probe

The repair was developed red/green against canonical acceptance, generated
validity, schedule coverage, exact override observability, canonical-shortcut
fit, per-window rival refutation, and the second-hop witness. The portable task
suite now passes 8 tests and 319 subtests.

`workspace/room_graph_probe.py` is a source-bound replay tool for future
reviewers. With 80 seeds per band it checked 240 complete lesson windows and
960 generated grids, accepted 3/3 canonical pairs, observed exactly 240 of each
schedule profile, produced 240 second-hop witnesses, and found no validation,
parity, schedule, shortcut, or finite-rival failures. See
`checks/6b694a414d96-room-graph-probe-final/result.json`.

### Authority and measured checks

The canonical Racket authority was not changed. Its normalized hash remains
`bf24da6609f2`. The repaired generator SHA-256 is
`d62e12de8d52bf223823a1b64fc7c798588cd5f5f4db5e6e0c2fe4aee5ab9708`.
Post-repair checks include:

- semantic gate: 600/600 strict samples, 3/3 canonical pairs, 2/2 witnesses,
  2/2 rival claims, and 12/12 identifiable sampled lessons;
- exact override contract: 10,800/10,800 accepted draws over 120 cases and
  three bands;
- Racket rule smoke: 120/120 applied and Python-mirror parity, zero crashes;
- self-check: 60/60 defaults and all three canonical inputs accepted.

### Deliberate boundary and remaining uncertainty

The generator teaches a uniform rectangular room-lattice subset of the oracle's
broader possible graph domain; it does not claim to cover arbitrary irregular
rooms. The rival set is finite, and the semantic gate reports 7/48 query
rotations as diagnostically ambiguous even though every requested lesson passed.
Those limits do not contradict the repaired default three-example contract, but
a future widening should add new graph topologies only with matching validators,
Racket parity, and explicit shortcut witnesses.
