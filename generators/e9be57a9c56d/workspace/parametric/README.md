# Proposed `extra_copy_gap` episode prototype

This task-local prototype keeps the production generator and canonical Racket
authority unchanged. It adds one episode-fixed rule parameter:

| parameter | allowed values | original/default |
|---|---|---|
| `extra_copy_gap` | integer `0` or `1` | `0` |

The original rule chains recolored copies of the largest template from the
same-color marker, using each consecutive marker distance as the edge-to-edge
copy gap. Setting `extra_copy_gap=1` preserves every object role and reasoning
step, but adds one cell of padding at each consecutive step away from the
anchor. The forward and backward horizontal/vertical branches all receive the
same adjustment. Setting `0` returns the canonical Racket source byte-for-byte.

The parameter is selected once per episode (even seed → `0`, odd seed → `1`)
unless supplied explicitly, then remains fixed across all demonstrations and
queries. Inputs are sampled from the selected production generator and padded
only along the chain axis so both settings stay in-bounds. Demonstration labels,
query labels, the opposite-setting rival, and canonical replay are all executed
through the protected Racket bridge. The opposite setting is fitted using
labeled demonstrations only; every retained query records whether it changes
under that rival.

Demonstration and query counts are independent. The retained command uses three
demonstrations and four distinct queries for each setting:

```bash
python3 review.py run python3 \
  generators/e9be57a9c56d/workspace/parametric/prototype.py \
  --seeds 10 11 \
  --extra-copy-gaps 0 1 \
  --demo-count 3 \
  --query-count 4 \
  --out ../checks/parametric-e9be57a9c56d-extra-copy-gap-v1
```

Run the focused contract from the outer extracted packet directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/e9be57a9c56d/tests/test_parametric_extra_copy_gap.py
```

Public files contain only labeled demonstrations and query inputs. Their opaque
filenames are SHA-256 IDs of exactly the canonical visible bytes from
`reviewer_support.public_challenge_bytes`; hidden parameters, rules, query
labels, seeds, and metadata stay under `private/`. Duplicate visible payloads
and pre-existing output directories fail closed. `verify_evidence` also rebinds the current canonical rule, selected generator, and prototype bytes; rejects path traversal or unrecorded episode files; checks recorded byte counts and hashes; and rechecks public/private rule, parameter, and label-separation contracts.

## Scope and limits

This is **proposed, unapproved prototype evidence**. It does not add a production
axis, alter `generator.py`, modify the catalog or canonical data, refresh an
approval hash, or admit examples to training. The retained evidence covers two
episodes, settings `0` and `1`, three demonstrations and four queries per
episode, the declared opposite-setting rival, and the bounded deterministic
sampler exercised by the focused tests. It is not an exhaustive proof over all
seeds, grid shapes, or alternative hypotheses.
