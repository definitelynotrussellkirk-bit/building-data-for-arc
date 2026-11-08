# Proposed wall-offset and length-measure family (prototype only)

This directory is separate from the selected canonical execution path. It does
not change the production generator, canonical task labels, or rule hash
`326f0e0036c3`.

The prototype retains the original object roles and reasoning sequence: detect
the track, summarize the gray motif, rebuild symmetric parallel walls, preserve
the perpendicular crossbar, and draw a centered one-cell-wide gray line.

## Parameters

| Parameter | Allowed values | Canonical/default | Effect |
| --- | --- | --- | --- |
| `output_wall_offset` | `1`, `2` | `1` | Rebuild the two output walls center ± this distance. |
| `length_measure` | `cell_count`, `track_span` | `cell_count` | Set output-line length from gray-cell count or the motif's longitudinal bounding-box span. |

A complete setting is chosen once per episode as `ALL_SETTINGS[seed % 4]` and
held fixed for all three demonstrations and the query. The four retained Racket
programs are under `rules/`. Public challenges under `examples/` contain labelled
demonstrations and an unlabelled query, but no hidden parameter or query answer.

Run the bounded authoring probe from the outer packet directory:

```bash
python3 review.py run python3 \
  generators/5c0bcc9d1b8b/workspace/parametric/prototype.py \
  --seed 17 \
  --out ../checks/parametric/wall-offset-length-measure-seed17.json \
  --write-public generators/5c0bcc9d1b8b/workspace/parametric/examples
```

The probe executes every example with the exact included Racket program, checks
the Python mirror only as a secondary assertion, replays the canonical/default
setting on all labelled canonical pairs, and verifies that every demonstration
refutes all three alternative parameter settings. Its evidence is bounded to
these four settings and one episode seed; it is not production approval and does
not establish uniqueness against undeclared rules.
