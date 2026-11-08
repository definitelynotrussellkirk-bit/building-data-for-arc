# Proposed `compression_axes` episode prototype

This task-local prototype keeps the production generator and canonical Racket
authority unchanged. It adds one episode-fixed rule parameter:

| parameter | allowed values | original/default |
|---|---|---|
| `compression_axes` | `both`, `rows`, `columns` | `both` |

`both` is byte-for-byte the canonical `(rule! (compress-grid g))`. `rows`
removes only adjacent duplicate whole rows; `columns` removes only adjacent
duplicate whole columns. The input grammar remains rectangular multicolor ARC
grids. Authored episodes deliberately include at least one duplicate on each
axis so the demonstrations identify the setting; all settings preserve the
family's full-line comparison and consecutive-only reasoning.

The setting is selected once from the episode seed (`seed % 3`) unless supplied
explicitly, then held fixed across every pair. Demonstration and query counts
are separate positive integers, with at most 32 total pairs. The retained
command uses three demonstrations and four distinct queries for each of three
seeds, covering every setting. Every label and rival prediction is executed by
the protected Racket bridge.

From the outer packet directory:

```bash
python3 review.py run python3 generators/4e081a15d785/workspace/parametric/prototype.py \
  --seeds 0 1 2 \
  --demo-count 3 \
  --query-count 4 \
  --out ../checks/parametric/4e081a15d785-compression-axes-v1
```

Focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/4e081a15d785/tests/test_parametric_compression_axes.py
```

The writer is atomic and fails if the output path already exists or two requested
episodes have identical visible challenges. Public filenames are SHA-256 IDs of
exactly the visible demonstration inputs/outputs and query inputs. Public files
omit seeds, settings, Racket source, and query answers; private files retain the
fixed setting, exact rules, labels, generator controls, hashes, canonical replay,
distinguishing witness, and a second live-Racket verification pass.

## Scope and limits

This is a **proposed, unapproved prototype**. It does not add a production axis,
change `generator.py`, alter the catalog, relabel the canonical task, or approve
new data. Finite evidence covers the requested seeds, three declared settings,
and the authored teaching grammar; it is not an exhaustive proof over all grids
or alternative programs.
