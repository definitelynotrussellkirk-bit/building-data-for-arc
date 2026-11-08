# Proposed completion-transform parameter prototype

Status: **proposed and unapproved**. This task-local workspace does not alter
the approved production generator, canonical `RULE_HASH`, or canonical Racket
authority.

## Parameter

`completion_transform` is selected once per episode and stays fixed across every
demonstration and query:

- `rotate_180` — canonical/default. Fill each color-7 cell from its 180-degree
  rotational counterpart when that counterpart is non-7.
- `flip_lr` — proposed alternate. Fill each color-7 cell from its left-right
  reflected counterpart when that counterpart is non-7.

Both settings preserve every existing non-7 cell, the color-7 writable
background, the central color-4 divider, the three color-8 anchors, and the
one-sided connected source figure. Only the counterpart map changes. The
production generator already requires at least four cells where the two maps
disagree, so each authored demonstration distinguishes the declared settings.
The canonical setting is byte-identical to
`(rule! (grid-overlay-on (rotate-180 g) g 7))`; the alternate is one guarded
replacement with `flip-lr`.

## Build two complete episodes

From the outer extracted packet directory:

```sh
python3 review.py run python3 \
  generators/1674812130ff/workspace/parametric/prototype.py \
  --seed 23 \
  --difficulty medium \
  --train 2 \
  --test 4 \
  --out ../checks/parametric/completion-transform-v1
```

The command writes one private episode for each setting over the same six
distinct inputs. Each contains two labeled demonstrations and four labeled
private queries. Every label is executed through the matching Racket program;
a separate Python implementation is used only as a parity diagnostic. The
writer also replays the exact canonical program on all four official labeled
pairs.

Public challenge files are named only by SHA-256 of canonical visible bytes:
demonstration inputs/outputs and query inputs. They omit seed, hidden setting,
Racket source, source hashes, and query answers. Private episodes, exact programs,
Racket query labels, source bindings, and declared-rival checks remain under
`private/` or in the private report.

## Focused checks

```sh
python3 review.py check --stage task_tests --phase after --timeout 600 \
  --out ../checks/task-tests-parametric-v3
```

The portable staged suite covers exact canonical authority, guarded alternate
materialization, real Racket execution, deterministic fixed-setting episodes,
same-input paired settings, distinct four-query supervision, demonstration-only
rival elimination, strict validation, public/private export boundaries,
manifest hashes, the thin promotion adapter, and the inherited regression test's
portable canonical-data lookup.

For the assignment's bounded adversarial pass:

```sh
python3 review.py run python3 \
  generators/1674812130ff/workspace/parametric/adversarial_probe.py \
  --seed 0 --seed 17 --seed 31 \
  --difficulty easy --difficulty medium --difficulty hard \
  --out ../checks/parametric/completion-transform-adversarial-v1.json
```

The reusable probe uses the count boundary of one demonstration plus eight
queries, executes both settings through Racket, checks all emitted cells are
exact Python integers rather than booleans, and verifies that public IDs bind
visible bytes while ignoring private source, seed and query answers.

## Promotion-ready adapter

`adapter.py`, `promotion.json`, and the source-bound reviewer evidence manifest
implement the repository's explicit adapter → qualification → acceptance path
with bounded counts of 1..8. The reviewer qualification passed for both settings
at seeds 0 and 17 with two demonstrations and four queries: four episodes and 32
protected-Racket evaluations. Qualification does not constitute owner acceptance
or training admission. An owner can independently rerun:

```sh
arcpuzzles parametric qualify 1674812130ff \
  --seed 0 --seed 17 --demos 2 --queries 4 \
  --out var/review/qualification-1674812130ff
```

before a separate reviewed acceptance decision.

## Limits

This is bounded prototype evidence for two declared transforms, not production
approval or training admission. Identifiability is checked against the opposite
transform only; finite demonstrations do not prove uniqueness against every
conceivable program. Both settings use the selected generator's existing
one-sided divider-and-anchor grammar.
