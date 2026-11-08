# Proposed `lower_band_order` rule parameter

This directory is a **task-local, unapproved prototype**. It leaves the selected
production generator, canonical labels, canonical Racket authority, and
`RULE_HASH` unchanged.

## Parameter

`lower_band_order` is selected once from the episode seed and is fixed across
every demonstration and query.

| Value | Effective physical-band priority | Role |
| --- | --- | --- |
| `band3_then_band2` | `0 > 1 > 3 > 2` | Canonical/default |
| `band2_then_band3` | `0 > 1 > 2 > 3` | Proposed alternative |

Both settings preserve the original reasoning structure: split the 12-row input
into four aligned 3-row monochrome masks, project them onto one 3-row frame, and
choose the first nonzero value by a fixed physical-band priority. Only the order
of the two lower-priority bands changes. The existing generator's reserved
pairwise witnesses include a direct band-2/band-3 overlap in every input, so the
settings differ on lawful scenes without changing the input manifold.

Each retained episode has two labeled demonstrations and four distinct unlabeled
queries. Every label is produced by executing the matching exact Racket program.
Each query is checked independently against the other declared setting using
only the two demonstrations. Public files contain only visible demonstrations
and query inputs; opaque filenames are hashes of those visible fields and are
independent of seeds, parameter names, Racket source, and query answers. The
materializer plans both public artifacts first and emits them in lexicographic
visible-filename order, so the private seed/setting schedule cannot leak through
filesystem creation order. Duplicate visible IDs are rejected before any public file is emitted.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/3a0af56db83e/workspace/parametric/prototype.py materialize \
  --seed 0 --demo-count 2 --query-count 4 \
  --out ../checks/parametric/lower-band-order

python3 review.py run python3 \
  generators/3a0af56db83e/workspace/parametric/prototype.py verify \
  --out ../checks/parametric/lower-band-order
```

Focused portable tests are under
`generators/3a0af56db83e/tests/test_parametric_lower_band_order.py` and run as
part of the packet's `task_tests` stage.

## Limits

The retained evidence covers the two declared settings and two consecutive
seeds. It does not prove uniqueness against undeclared rules, approve a
production parametric API, refresh the canonical authority, or admit these
variants to training. The hidden setting is inferable in the retained episodes,
but broader sampling and review would still be required before integration.
