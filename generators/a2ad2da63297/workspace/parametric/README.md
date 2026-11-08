# Proposed crossing-mode parameter prototype

Status: **proposed and unapproved**. This task-local workspace does not alter the
production generator, canonical `937e30cc1e90` Racket authority, source approval,
or training admission.

## Parameter

`crossing_mode` is selected once from the episode seed and stays fixed across all
demonstrations and queries:

- `cross_through` — canonical/default. For every barrier lane with one dot on each
  side, the two colors cross the barrier and land flush on the opposite sides.
- `compress_to_barrier` — proposed alternate. The same matched dots move flush to
  the barrier but remain on their original sides.

Both settings keep the original reasoning structure: find the most frequent
non-background barrier, infer its orientation, inspect each occupied barrier
lane, require a dot on both sides, preserve unmatched dots, and place moved dots
immediately outside the lane's barrier extent. Only the side receiving each
matched color changes.
No input constraint depends on `crossing_mode`; paired settings may therefore use
the same lawful grids without changing the sampling domain.

The default program is the exact canonical source, SHA-256
`937e30cc1e90881f7f01d4b05e8ec9bbb6a71432bfd75b8e7b744ccc9e2abf1c`.
The alternate is produced by four exact, count-checked destination replacements:
two for horizontal lanes and two for vertical lanes. Retained labels are executed
by `RacketBridge`; the independent Python mirror is only a parity check.

## Materialize two complete episodes

From the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/a2ad2da63297/workspace/parametric/prototype.py \
  --seeds 0 1 \
  --demo-count 2 \
  --query-count 4 \
  --out ../checks/parametric/crossing-mode-v1/evidence
```

Seed `0` selects `cross_through`; seed `1` selects `compress_to_barrier`. Adjacent
seeds share the same deterministic input stream, so the retained episodes compare
settings on identical inputs. Each episode has one horizontal and one vertical
demonstration plus four distinct queries, alternating orientations. Counts are
independent: demonstrations support `2..8`, queries support `1..8`.

The files under `public/` contain only labeled demonstrations and unlabeled query
inputs. Their opaque names are SHA-256 of exact visible bytes. Seeds, settings,
Racket source, source hashes, and query answers remain outside `public/`, in the
private evidence and control manifest.

## Focused checks

```sh
python3 review.py run python3 -m pytest -q \
  generators/a2ad2da63297/tests/test_parametric_crossing_mode.py
```

The checks cover exact default authority, guarded alternate materialization,
horizontal and vertical witnesses, all four labeled canonical pairs, strict
seed/count/setting validation, setting-independent paired inputs, fixed episode
semantics, four distinct queries, demonstration-only elimination of the opposite
setting and identity, Racket/Python parity, and public/private export boundaries.

Retained adversarial evidence additionally checks both settings on the four
irregular canonical inputs and 24 generated boundary inputs spanning both
orientations, pair counts `2`/`4`, and easy/hard sizes. It also verifies exact
public IDs, private-metadata independence, visible-label sensitivity, and rejection
of bool, float, and out-of-range cells.

## Limits

This is bounded prototype evidence, not production approval. The sampler inherits
the current production generator's straight-barrier domain even though parity is
also checked on the irregular canonical walls. Identifiability is finite: the
opposite crossing mode and identity are tested, not every imaginable ARC program.
The production generator still advertises several weak or ignored input axes; that
separate canonical-generator repair remains useful but is not silently bundled
into this rule-variant proposal.
