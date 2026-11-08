# Cue-parity parametric family — `2243318b8e96`

`parity_reference` is fixed for an episode and has three values:

- `absolute` (canonical): odd components → 3, even components → 8.
- `same_as_cue`: find the unique color-1 component; components with the same
  size parity as that cue → 3, all others → 8.
- `opposite_to_cue`: the same input-derived comparison, with the two output
  colors reversed.

The first two demonstrations use odd and even cue sizes, so all three programs
are uniquely identified at the supported minimum. Inputs are matched across
settings. Each episode has 2–6 demonstrations and exactly four queries; the
fourth query is a distributed 30×30 stress scene. The adapter keeps settings,
programs, answers, and future queries private from `public_turn` projection.

The alternative settings are genuinely sequential: A locates the unique
color-1 object and computes its size parity; the resulting bit is consumed by B
when every component is recolored. `adversarial_probe.py` attacks fixed parity,
connectivity, bounding-box, color-frequency, total-foreground, partial-cue,
certificate, count, and public-projection shortcuts.
