# `a2b749aefc65` travel-mode family

The episode chooses one finite `travel_mode`:

- `one_step` — exact canonical default, byte-for-byte.
- `two_steps` — use the same border-color direction decoder, but advance each
  matching marker two cells instead of one.

The deterministic sampler is independent of the setting. Every sample includes,
for each decoded direction, one marker blocked under both settings and one
marker that moves under `one_step` but is blocked under `two_steps`. Freely
moving markers provide the remaining density. The sampler reserves each
marker's actual source/destination cells and all stationary distractors across
objects before painting, so neither rule relies on overwrite order. Episodes
contain 2–6 representative demonstrations and exactly four queries; the last
query is a substantive 30×30 case with 24 side-colored markers and 12
unmatched distractors.
