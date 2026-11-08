# Parametric reverse-shift prototype

This is an **isolated proposed prototype**. It does not alter the selected
canonical generator, its production API, or the pinned canonical Racket rule.

## Parameter

`reverse_shift` is selected once per episode and held fixed across three
demonstrations and one query.

- `0` — canonical/default: trace the cyan-background path and reverse its color
  sequence in place.
- `1` — proposed alternative: perform the same reversal, then cyclically shift
  the reversed sequence one path position toward the traversal start.

Both settings use the same path cells, row-major endpoint choice, traversal,
background, and coordinate-preserving repaint. The production generator already
requires at least two distinct path colors, so every retained pair distinguishes
shift 0 from shift 1; the demonstrations therefore identify the episode setting.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/2c631747784e/workspace/parametric/build_prototype.py \
  --out-dir ../checks/parametric/reverse-shift-v1
```

The builder refuses to overwrite evidence. It executes both exact Racket
programs with the included bridge, checks the default against every labeled
canonical pair, checks a Python parity oracle, builds one complete episode per
setting, and writes source-bound private evidence plus redacted public
challenges. Public challenges omit the seed, hidden parameter, Racket source,
and query answer.
