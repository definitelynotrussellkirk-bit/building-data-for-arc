# Proposed target-colour variant for 113d9bb402d3

**Status: proposed prototype, unapproved.** This task-local authoring interface
keeps the original reasoning pattern: locate the cyan bounding box, select blue
cells inside it, and recolour only those selected cells. The single episode
parameter changes the executed target colour from canonical green `3` to yellow
`4`; it does not change input constraints, object roles, the selected region,
or the production `generate(...)` API.

| Contract item | Value |
|---|---|
| Parameter | `target_colour`, literal Python integer in `{3, 4}` |
| Original/default | `3`; `materialize_rule()` returns the exact canonical source |
| Episode selection | one `random.Random(seed).choice((3, 4))` before any pair |
| Complete episode | three labeled demonstrations and one masked query |
| Input support | four authored lawful cyan-bbox inputs, shuffled independently |
| Public boundary | train inputs/outputs and test input only |

Every setting is exact Racket text derived from the canonical source SHA-256
`6e7fd13287b51f1d00269aee4d794739d2bba148c8ddf16c6a927ab4eabc580d`.
The canonical setting is byte-for-byte unchanged. The only alternative edit is
at the unique guarded recolouring literal `(= v 1)) 3 v`, replaced by
`(= v 1)) 4 v`. Every example label and rival prediction is executed with the
included `RacketBridge`; no Python answer mirror is used.

From the outer extraction directory:

```bash
python3 review.py run python3 \
  generators/113d9bb402d3/workspace/parametric/prototype.py \
  --seeds 0 1 --out ../checks/parametric/episodes

python3 review.py run python3 -m pytest -q \
  generators/113d9bb402d3/tests/test_parametric_variant.py
```

Seeds `0` and `1` cover both settings. Every retained demonstration changes at
least one selected blue cell, so the other target-colour setting is refuted by
all three demonstrations before the query. Private evidence retains parameter
values, query answers, exact Racket source and hashes; public files omit all of
those fields.

This is bounded evidence, not approval. The fixture set is intentionally small,
and checking the declared colour rival does not rule out every alternative ARC
interpretation. Canonical generator repair checks remain separate.
