# Native disagreement-action family

The native adapter preserves the source puzzle's repeated-tile comparison and
adds an episode-fixed choice of what to do with damage:

| Setting | Executed transformation |
| --- | --- |
| `mark` | Exact canonical/default program: mark only disagreement coordinates with 1. |
| `restore` | Reconstruct the intact consensus tile. |
| `mark_component` | Reconstruct the consensus, find its same-color 4-neighbor components touched by erased cells, and mark their complete extent with 1. |

`adapter.py` exports `program(settings)` and
`generate(seed, settings, demos=3, queries=4)`. It supports 2–6 demonstrations
and 1–4 independent queries, with four queries in every qualification/example.
The lower query count exists for exact single-query first-turn compatibility.
`promotion.json` declares the native contract. The old `prototype.py` is retained
as a legacy two-setting authoring entry; it is not the new native delivery path.

## Reasoning and teaching

First recover the modal intact tile from its repeated copies, including colors
and connectivity erased in the anomalous tile. Only then can the component rule
identify which same-color regions to mark. An erased bridge and an untouched
diagonal same-color object make the order and connectivity observable.

Every setting uses the same first two 29×29 demonstration inputs for a given seed.
They include a deleted bridge, same-color disconnected and diagonal distractors,
a touching different color, multiple damaged components, and an untouched largest
component. Additional demonstrations and queries vary geometry, density, palette,
erasure counts, anomaly location and orientation through the canonical sampler
and transformed constructive templates. The bounded audit states exactly which
rivals it tested; finite examples do not establish universal unique induction.

The canonical input is always 29×29: 25 copies of a 5×5 tile separated by one cell.
The noncanonical rules also use a genuine 30×30 final query: 16 copies of a 6×6
tile separated by two cells. These larger tiles have 19 foreground cells, several
components, three erasures, and foreground on every boundary. Their six-cell
output uses the larger tile; the 30th row/column is not ignored padding.
The supported minimum/maximum input sizes are 29/30, and canonical mark stays at 29.
Geometry alone cannot distinguish restore from mark_component. All settings'
first query inputs remain identically sampled; their demonstrations teach the rule.

## Run from an extracted packet

After `python3 review.py setup`, use a Python interpreter that passes
`review.py python-check` (the packet-local example below includes pytest).

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/8b320727aa72/tests/test_native_parametric.py \
  generators/8b320727aa72/tests/test_native_audit.py

WORK/.venv/bin/python review.py run python3 \
  generators/8b320727aa72/workspace/parametric/check_native.py \
  --out ../checks/8b320727aa72/native-audit-NEW

WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  8b320727aa72 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/8b320727aa72/qualification --summary
```

Before qualification, refresh the native source/evidence inventory using
`parametric manifest` as described in `docs/parametric-promotion.md`.
After integration, the owner must qualify and accept the exact live source;
reviewer evidence and Python-claimed labels do not replace that acceptance.
No training data admission or training activation is included.

## Public/private boundary

Complete episodes, settings, programs, all four answers and teaching evidence
are private controller records. A model-visible first turn contains only all
visible demonstrations and the first query input. Use the existing serializer:

```python
from reviewer_support import public_challenge_bytes, public_challenge_id
first = {"train": episode["train"], "test": episode["test"][:1]}
raw = public_challenge_bytes(first)
name = "challenge-" + public_challenge_id(first) + ".json"
```

Hash the projected first turn, including the serializer's newline, rather than
its four-query private container. The existing consumer reveals subsequent
queries one at a time; this adapter introduces no turn controller or count hint.
The audit checks real one-query/four-query request parity and unchanged public
identity after edits to future inputs, private answers, settings and seed metadata.

## Limits

The original production generator, canonical authority and legacy prototype are
unchanged. Erasure-only teaching does not cover arbitrary novel-color insertions,
as already recorded in the task notes. Only the two implemented tiling geometries
are supported. Deterministic duplicate rejection has an eight-attempt bound and
raises visibly instead of shortening a lesson. Qualification and self-audit cover
their declared settings, seeds and rivals; they do not measure learning benefit.
