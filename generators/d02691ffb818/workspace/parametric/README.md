# Cue-selected satellite-count X radius

This native family preserves the exact canonical rule and adds one nearby,
episode-fixed alternative on matched inputs.

- `fixed_one` is the canonical Racket program byte-for-byte: every blue marker
  stamps an orange center plus the four in-bounds radius-one diagonal cells.
- `cue_satellite_count` finds the unique blue marker nearest the red cue, counts
  that marker's green cardinal satellites, and uses the count as the diagonal
  X radius for every blue marker.

The alternative has a real sequential dependency. Step A resolves the cue's
unique nearest blue marker. Its input-dependent intermediate is that marker's
one-to-four satellite count. Step B cannot choose the global stamp radius until
that count is known. Substituting a different marker's count changes the final
output while preserving the same stamping operation.

Inputs are independent of the private setting. The first two demonstrations
use selected radii two and three, include one- and four-satellite distractors,
and move the selected marker so fixed-radius, global-maximum, farthest-marker,
row-major, selected-only and per-marker shortcuts cannot fit both labels. The
sampler supports 2–6 demonstrations and 1–4 prefix-stable queries. The fourth
query is a distributed exact 30×30 scene with fourteen marker pods, a clipped
border marker and a close pair.

`prototype.py` exposes one-query `public_view` and visible-byte `public_id`
helpers. Settings, programs, future queries and query answers stay private.
Owner qualification/acceptance and training admission remain separate.
