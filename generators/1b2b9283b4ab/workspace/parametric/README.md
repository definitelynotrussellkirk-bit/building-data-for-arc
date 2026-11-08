# Native tie-marker family

This directory contains the source-qualified parametric adapter for
`1b2b9283b4ab`. It preserves the selected canonical Racket program exactly for
`tie_marker=8` and provides one nearby rule setting, `tie_marker=6`, which
changes only the color used when multiple **distinct** seed colors share the
minimum doorway-graph distance to a room.

## Contract

- Settings: `{"tie_marker": 8}` and `{"tie_marker": 6}`.
- Default: `8`; `canonical.rkt` is byte-for-byte the canonical authority.
- Demonstrations: any prefix of 2–6.
- Queries: any prefix of 1–4; qualification uses four.
- Inputs are deterministic, count-prefix stable, and independent of the hidden
  setting.
- The four query bank covers a path, a cyclic grid, disconnected rooms, and a
  substantive 30×30, 25-room grid with 400 non-wall cells.
- The first two demonstrations distinguish both declared settings and also
  exercise repeated seed colors, multi-seed rooms, unreachable rooms, and
  graph-distance rather than pixel-distance behavior.

The sequential rule is explicit. Step A parses rooms and doorways and computes,
for every room, the minimum graph distance and the distinct seed-color set
attaining it. Step B consumes that intermediate to choose the sole nearest
color or the episode tie marker and paints the room. The retained
`wrong-all-seed-colors.rkt` ablation discards the nearest-color intermediate;
protected-Racket causal replay confirms that doing so changes qualified labels
for both settings.

## Reproduce

From the extracted packet root:

```bash
python3 review.py run python3 generators/1b2b9283b4ab/workspace/parametric/audit.py \
  --out ../checks/1b2b9283b4ab/self-audit.json
python3 review.py run python3 -m arcpuzzles parametric qualify 1b2b9283b4ab \
  --demos 2 --queries 4 --out ../checks/1b2b9283b4ab/qualification --summary
python3 review.py run python3 -m arcpuzzles.review_witness check \
  --qualification ../checks/1b2b9283b4ab/qualification/qualification.json \
  --witness ../checks/1b2b9283b4ab/causal/witness.json \
  --out ../checks/1b2b9283b4ab/causal-recheck.json
```

`audit.py` checks 32 seeds, demo counts 2/3/6, both settings, declared-setting
confusion, six semantic shortcut rivals, determinism, count-prefix stability,
setting-independent inputs, and the 30×30 boundary. It also executes 32 adapter
labels through protected Racket. Native qualification separately executes two
fresh seeds per setting with two demonstrations and four queries.

## Status and limits

Reviewer qualification is ready and source-bound, but owner acceptance and
training admission are intentionally not performed here. The finite rival audit
and causal replay do not prove uniqueness against every possible program or
measured model-training gain.
