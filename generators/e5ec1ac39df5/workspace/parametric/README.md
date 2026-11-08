# Room-target family for `e5ec1ac39df5`

The episode-fixed `target_rooms` setting is either:

- `seeded` — the byte-for-byte canonical rule paints boundaries of rooms containing color 2.
- `neighbors` — first identify seeded room IDs, traverse color-7 room-graph edges to their adjacent room IDs, then paint those neighboring rooms' boundaries.

Every lesson uses irregular room sizes, moving seed locations, and a partial color-7 graph that omits at least one geometric neighbor of the seeded room,
2–6 demonstrations, and four distinct queries. Centered and off-center seeds are
both demonstrated at the minimum lesson size. The fourth query is a substantive
30×30, 4×4 room graph. Python emits deterministic label claims; protected native
qualification replays both rules in Racket.
