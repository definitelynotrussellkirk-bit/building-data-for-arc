# Cyclic rank-offset prototype (proposed, unapproved)

This task-local prototype adds one hidden, episode-level rule parameter while
leaving `generator.py`, the canonical Racket authority, catalog approval, and
training admission unchanged.

| Parameter | Allowed values | Canonical/default |
| --- | --- | --- |
| `rank_offset` | `0`, `1` | `0` |

The original reasoning path is preserved. The input still encodes one recovered
motif twice: active motif cells choose the occupied macro blocks and the active
micro cells inside each occupied block. Macro and micro motif positions are
ranked in row-major order. The output remains their product, with red (`2`) at
every active product cell except one cyan (`8`) correspondence per occupied
macro block.

- `rank_offset=0` is the exact canonical rule: cyan appears where micro rank
  equals macro rank.
- `rank_offset=1` is the nearby cyclic variant: cyan appears where micro rank is
  the next active rank, wrapping the final macro rank to micro rank zero.

The setting is chosen once per episode and held fixed across two demonstrations
and four distinct queries. Both settings use the same six lawful inputs for the
retained comparison. Every output is produced by its exact Racket program and
checked against an independent Python mirror. Each demonstration rejects the
sole declared rival setting, and every query would receive a different answer
under that rival.

From the outer extracted packet directory, write the retained evidence:

```bash
python3 review.py run python3 \
  generators/9a94379ed070/workspace/parametric/prototype.py materialize \
  --seed 31 --train 2 --test 4 \
  --out-dir ../checks/parametric/9a94379ed070-rank-offset-v1
```

Replay every retained hash, public projection, exact program, canonical pair,
Racket label, Python mirror, and rival check:

```bash
python3 review.py run python3 \
  generators/9a94379ed070/workspace/parametric/prototype.py verify \
  --out-dir ../checks/parametric/9a94379ed070-rank-offset-v1
```

Run the focused contract:

```bash
python3 review.py run python3 -m pytest -q \
  generators/9a94379ed070/tests/test_parametric_rank_offset.py
```

## Retained artifact

The evidence tree contains exact `.rkt` programs, private fixed-setting episodes,
masked public challenges named only from visible bytes, a deterministic report,
and a hash manifest. The private episodes, report, and manifest bind the exact
prototype source path and SHA-256. The verifier fails closed on missing, added,
changed, stale-source, symlinked, or out-of-inventory files. It also rejects
seed/generator/program drift and split-brain `train`/`test` copies before
recomputing the semantic evidence through live Racket execution.

## Scope and limits

This is a **proposed, unapproved prototype** covering only offsets `0` and `1`,
seed `31`, two demonstrations and four queries per setting, the selected input
grammar, and the other retained offset as the declared rival. Finite examples do
not establish uniqueness against arbitrary programs, exhaustive seed coverage,
or suitability for production or training. The canonical/default program is
retained byte-for-byte and remains the only selected authority.
