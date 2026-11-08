# Proposed base-edge parameter for cde6cd1740f9

**Status: proposed task-local prototype; no production approval.** This extends
the original column-to-pyramid family with one small semantic parameter. It
does not alter the selected canonical generator, runtime API, catalog, rule pin,
or approval state.

| Contract | Value |
|---|---|
| Parameter | `base_edge`, exactly `"bottom"` or `"top"` |
| Original/default setting | `"bottom"` |
| Episode choice | One `random.Random(seed).choice(("bottom", "top"))`, before any pair |
| Bottom behavior | Broad base on the last row; apex points inward/upward |
| Top behavior | Broad base on row 0; apex points inward/downward |
| Demonstrations | Current selected generator's `EXAMPLES_NEEDED` |
| Queries | One input, without its answer in the public challenge |
| Input constraints | Identical for both settings; the selected generator supplies and validates every input |

The invariant reasoning remains: identify each active source column, count its
`k²` nonzero cells, read distinct source colors **bottom to top**, partition their
exact counts into complete consecutive layers of widths `2k−1, 2k−3, …, 1`, and
center every layer on the **same source column**. Background is 0. Pyramids stay
on the canvas, have nonoverlapping footprints, and preserve color multiplicity.
Only the output edge changes. In particular, `top` does not reverse the source
color-reading order or rotate the input.

## Exact programs and authority

`materialize_rule()` returns the canonical program **byte for byte** for the
default setting. The canonical program's full source SHA-256 is
`1eabf7f4ae2d7acbaa8ba9db677c140a76bfabce59d672ea30d1ba06cbd3fae5`;
the existing canonical authority remains `RULE_HASH = 027335bb451f`.
The prototype verifies the full source hash before applying the unique edit:

```racket
; bottom (canonical)
(row (- (- h 1) i))

; top (the sole program change)
(row i)
```

The executable rule body, including layer allocation and source color order,
is otherwise unchanged. Every demonstration answer, private query answer, and
declared parameter-rival prediction is produced by the included `RacketBridge`.
The prototype contains no Python answer mirror.

## Reusable commands

Run from the **outer extraction directory**, which contains `review.py` and
`WORK/`. The wrapper selects the included offline Racket and executes payloads
from `WORK/repo/`:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/cde6cd1740f9/workspace/parametric/prototype.py \
  --seeds 0 1 --difficulty medium --start 0 \
  --out ../checks/parametric/episodes-final

WORK/.venv/bin/python review.py run ../.venv/bin/python -m pytest -q \
  generators/cde6cd1740f9/tests/test_parametric_cde6cd1740f9.py
```

Seed 0 selects `top`; seed 1 selects `bottom`. The same seed, start, band, and
source bytes reproduce the same episode. The output directory must be new or
empty to prevent evidence from different runs being mixed. A different
`--difficulty` (`easy`, `medium`, `hard`) or nonnegative `--start` is supported.
Use a fresh directory when changing settings or source bytes.

The default demonstration count is read at execution time instead of being
hardcoded, so the prototype follows a canonical schedule repair without
changing the fixed rule parameter. The finite rival check compares the chosen
edge with the other declared edge before the query. On the retained episodes,
each demonstration refutes that alternate edge.

## Public challenge and private evidence

Only files under `public/` are challenge material:

```text
public/episode-000.json
public/episode-001.json
```

Their entire schema is `{"train": [{"input": ..., "output": ...}], "test":
[{"input": ...}]}`. They contain no seed, parameter, reference program, rule
hash, rival predictions, or query answer. Filenames do not encode the setting.

The separate `private/` directory is authoring evidence:

| File | Evidence |
|---|---|
| `report.json` | Status, actual payload argv/cwd, observed settings, file hashes, runtime identity, limitations |
| `episode-NNN.json` | Seed, parameter, accepted sample indexes, generator/prototype/test hashes, exact chosen Racket, masked query's answer, all parameter-rival predictions and disagreement indexes |
| `rules/base-bottom.rkt` | Exact canonical program |
| `rules/base-top.rkt` | Exact alternative program |
| `canonical_replay.json` | Every labeled canonical pair, its executed default output, and parity verdict |
| `distinguishing_witness.json` | One lawful shared input, both executed outputs, and the inequality verdict |
| `source_snapshot/` | Exact prototype, selected generator, test, and README bytes used for this run |

Execution logs and tests-first failure receipts belong under
`WORK/checks/parametric/`, separate from the canonical repair evidence. The
focused tests in `tests/test_parametric_cde6cd1740f9.py` exercise this prototype
only: default canonical parity, exact layer geometry/counts under both settings,
8+1 and 5+4 two-color groupings, 5+3+1 three-color grouping, parameter validation,
deterministic episode choice, demonstration identifiability, and the CLI's
public/private boundary.

## Evidence limits

Two seeds at one band/start provide bounded evidence for the two declared
settings. They do not exhaust the input distribution or establish uniqueness
against every possible ARC interpretation. The parameter check only names the
alternate edge as its rival; the canonical generator's broader semantic rivals
and approval gates remain the separate canonical review's responsibility.

Both settings reuse the canonical input sampler, which leaves the future bottom
pyramid rows empty. Consequently the top-setting inputs can occupy their future
output rows. This does not affect the transformation because source row
positions are discarded, and it does not change source-column identity or color
reading. A separately approved production parametric API and broader sampling
study would be further work; this prototype does not claim either.
