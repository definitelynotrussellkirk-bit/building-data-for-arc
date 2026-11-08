# Proposed paint-semantics parameters for `3f533a120cf5`

This directory is a **task-local, unapproved prototype**. It leaves the
production generator, canonical Racket program, `RULE_HASH`, catalog status,
and training-admission state unchanged.

## Parameters

Both parameters are chosen once from the episode seed and remain fixed across
all demonstrations and queries.

| Parameter | Allowed values | Canonical/default | Effect |
| --- | --- | --- | --- |
| `key_target` | `gray_cells`, `bbox_holes` | `gray_cells` | Selects whether the column-key colors paint gray cells or holes inside the cropped gray bounding box. The other cell class receives the separator color. |
| `key_order` | `forward`, `reverse` | `forward` | Reads the same-width legend key left-to-right or right-to-left before painting columns. |

The canonical setting, `gray_cells` + `forward`, is byte-for-byte the supplied
rule. All settings preserve the original reasoning sequence: locate and crop
the gray bitmap, locate the adjacent key and separator bar, then paint each
cropped cell using the episode-fixed interpretation. The input grammar is not
changed. Retained inputs are filtered only to ensure that all four declared
settings make distinct predictions; every input still passes the selected
production generator's `self_check`.

Each retained episode has two labeled demonstrations and four distinct
queries. Every label is executed by the exact matching Racket program. Rival
settings are eliminated using demonstration outputs only; query answers are
not used to choose the compatible setting.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/3f533a120cf5/workspace/parametric/prototype.py materialize \
  --seed 90212 --episode-count 4 --demo-count 2 --query-count 4 \
  --out ../checks/parametric/paint-semantics-v1

python3 review.py run python3 \
  generators/3f533a120cf5/workspace/parametric/prototype.py verify \
  --out ../checks/parametric/paint-semantics-v1

python3 review.py run python3 -m pytest \
  generators/3f533a120cf5/tests/test_parametric_paint_semantics.py -q
```

The four consecutive seeds cover all four declared settings. Public challenge
files contain only labeled demonstrations and unlabeled query inputs. Their
opaque IDs are SHA-256 hashes of exactly those visible bytes; seeds, settings,
Racket source, and query answers remain under `private/`.

## Limits

This is finite evidence for four declared settings and four episodes, not a
proof against undeclared rules. It does not create a production parametric API,
approve any variant, refresh canonical authority, or admit generated episodes
to training. Broader seed coverage and independent semantic review would still
be required before integration.
