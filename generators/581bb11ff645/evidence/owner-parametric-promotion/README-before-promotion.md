# Hole-ranking rule variants — proposed prototype

This opt-in workspace preserves the reasoning of ARC training task `42a15761`
and its assigned generator `581bb11ff645`: find red column groups, measure their
black holes, rank the groups, and move each complete pattern to a fixed slot.
It does not change the selected production generator, canonical rule, catalog,
approval status, or training admission.

## Parameters and semantics

| Parameter | Values | Canonical default |
|---|---|---|
| `count_mode` | `cells`, `components` | `cells` |
| `direction` | `ascending`, `descending` | `ascending` |

`cells` counts every black cell inside a group's full-height rectangle.
`components` counts four-neighbor connected regions of those black cells.
Diagonal contact does not join regions. Black cells touching the group boundary
count too; this is not an enclosure test. A flood cannot cross a separator.
Both directions preserve input order for tied scores.

The default program is the exact canonical Racket text, not a rewritten mirror.
The other three settings materialize `rule_template.rkt`. One setting is fixed
for the entire episode. All generated labels are executed in the matching
Racket program and compared with an independent Python implementation.

## Generate and replay four-query episodes

From the outer packet directory, with Python 3.12+:

```bash
python3 review.py setup
python3 review.py run python3 generators/581bb11ff645/workspace/parametric/prototype.py generate --all-settings --seed 42 --n-demo 3 --n-query 4 --out ../checks/parametric/examples
python3 review.py run python3 generators/581bb11ff645/workspace/parametric/prototype.py verify ../checks/parametric/examples --report ../checks/parametric/replay.json
```

Use a new output directory after edits. A batch and its replay report must be
separate: the verifier rejects undeclared files inside the batch.
For one variant, omit `--all-settings` and pass, for example,
`--count-mode components --direction descending`.

The wrapper supplies this checkout's `src` and `shared/runtime` imports and its
verified offline Racket. NumPy and Pillow are declared runtime dependencies;
the focused test command also requires the declared pytest development dependency:

```bash
python3 review.py run python3 -m pytest generators/581bb11ff645/tests/test_parametric_581bb11ff645.py -q
```

In a normal repository checkout, supply `PYTHONPATH=src:shared/runtime` and a
working `RACKET_PATH` when invoking the same prototype directly.

## Public export and reusable verification

`public/` contains only demonstration input/output pairs and query inputs.
Distribute that directory to a model. All parameters, seeds, reference programs,
query answers, source bindings, and certificates stay in `private/`.
`index.json` lists sorted public content IDs.

Public filenames are the SHA-256 of the exact visible bytes written by the
shared `public_challenge_bytes` helper. Changes to private settings, seeds,
programs, certificates, or query labels cannot change those names. Duplicate
visible payloads and existing output destinations are rejected before writes.

The writer serializes provided records; it is not an approval gate. The `verify`
command independently reads the files, checks exact bytes and names, rejects
extra files/symlinks, validates private program and current source identities,
replays all four parameter programs on every input, checks all stored labels,
and recomputes the demonstration-only certificate. It also rejects malformed
numeric types, including booleans or floats masquerading as integer colors.
The seed is retained authoring metadata; verification does not regenerate an
episode from that seed or prove its historical origin.

`lesson_certificate(challenge)` is useful independently of generation. It fits
these eight explicitly declared hypotheses to demonstrations only:

- The four supported parameter settings.
- Eight-neighbor component counting in each direction.
- Identity and reversing the original group order.

It retains all fitting hypotheses and checks whether their predictions agree
for each query input. A query answer is never read. Empty version spaces fail
closed. Hypotheses that differ in name but agree on a query are not counted as
query ambiguity. The sampler ensures its first demonstration eliminates every
incorrect declared rival, including the eight-neighbor shortcuts.

## Domain and limits

- Seeds are exact integers in `0..2**63-1`. Demo and query counts are independent
  exact integers in `1..16`; booleans are rejected. Defaults are three demos and
  four queries. Input duplication across either split is forbidden.
- Generated inputs contain three to five equal-width groups, one zero column
  between groups, and no outer padding. Whole red perimeters make sampled zero
  regions enclosed, although the rule also correctly counts boundary zeros.
- Default demonstrations are `11x17`, `13x23`, and `15x29`. Default queries are
  `9x11`, `13x19`, `21x29`, and `30x29`. Larger counts repeat these shape schedules
  with distinct inputs. Larger query grids contain new hole patterns, not padding.
- Exact `30x30` is unavailable under this slot geometry: width is
  `groups * (group_width + 1) - 1`, and none of three, four, or five divides 31.
- Rejection sampling is deterministic and bounded. Exhaustion raises an error;
  no truncated episode or duplicate query is emitted. Finite tested seeds are
  evidence of those runs, not an exhaustive guarantee for every seed.
- The generated score counts are distinct. Stable ties and boundary zeros are
  supported by the rule and covered by literal regression fixtures, but are not
  currently a generated curriculum dimension.
- Eight declared rivals do not establish uniqueness among all possible rules,
  measured difficulty, model performance, production approval, or training admission.

All new functionality is task-local. Future generalization of the certificate
or writer can reuse the tested contracts without changing shared interfaces here.
