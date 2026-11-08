# Proposed reflection-extent episodes

This directory is an isolated, **proposed / unapproved** prototype for ARC task
`66e63986855b`. It does not modify the production generator, canonical Racket
program, `RULE_HASH`, approval state, or training boundary.

## Parameter

`reflection_extent ∈ {1, 2}` is selected once per episode and remains fixed for
all demonstrations and queries.

| Value | Rule |
| --- | --- |
| `2` | Canonical/default. For each non-endpoint occupied row, fill from just right of that row's frontier through the point reflected across the global right frontier. The program is byte-for-byte canonical. |
| `1` | Proposed alternative. Use the same row-front reasoning, but stop the fill at the global right frontier. |

Both settings keep the same foreground color, row roles, per-row frontier,
global frontier, source clearing, and endpoint exclusion. Only the bounded fill
extent changes. Inputs reuse the selected generator's lawful domain and do not
depend on the hidden setting. Every retained input distinguishes the two values.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/66e63986855b/workspace/parametric/prototype.py \
  --out ../checks/parametric/reflection-extent-v1 \
  --demos 3 \
  --queries 4 \
  --episode-seeds 0 1

python3 review.py run python3 -m pytest -q \
  generators/66e63986855b/tests/test_parametric_reflection_extent.py
```

Use a new output directory for each materialization. `--demos` and `--queries`
are independent exact counts in `1..8`. Even episode seeds select the canonical
extent `2`; odd seeds select extent `1`. Explicit API calls may pin a setting,
but it is still fixed once for the entire episode.

## Evidence layout

- `report.json` — parameter contract, source/runtime hashes, private episode
  records, public file hashes, checks, command, and limits.
- `private/programs/` — exact materialized Racket for both settings.
- `private/episodes/` — complete Racket-labelled episodes, hidden setting,
  accepted generator draws, and rival certificate.
- `private/witness.json` — one shared lawful input and both Racket outputs.
- `public/<sha256>.json` — ordinary ARC-form challenges containing only labelled
  demonstrations and unlabeled query inputs. The filename is the SHA-256 of the
  exact visible bytes, so private seed/setting/program metadata and query answers
  cannot affect it.

All selected and counterfactual outputs are executed through the bundled Racket
bridge and checked against an independent Python implementation. The opposite
setting must be refuted by demonstrations alone; query outputs are examined only
after that identification check to verify that every retained query differs.

## Limits

The evidence covers two declared settings and bounded seeds. It is not a proof of
unique induction against arbitrary programs, does not approve either variant, and
does not admit generated examples or trajectories to training.
