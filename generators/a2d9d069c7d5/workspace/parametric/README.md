# Proposed block-voting episode family

This is an opt-in prototype for `a2d9d069c7d5` (original ARC training task
`22806e14`). It does not change the selected generator's routing or canonical
Racket rule. Each episode fixes one setting and carries its materialized Racket
program, program hash, protected-runtime identity, labels and finite lesson
certificate. Status is `proposed`; `training_admitted` is false.

## Rule and parameters

The background is color 7. The less frequent foreground color is a five-cell
plus. The more frequent foreground color forms 4-connected solid squares.
Always mark the center of every odd-sided square with the plus color. Keep the
original plus when the odd squares win the selected vote; otherwise erase it.
Read roles, components and votes from the original input before recoloring.
This matters when a one-cell square disappears into a center marker or when
marking changes foreground color frequencies.

| Parameter | Values | Canonical default |
| --- | --- | --- |
| `vote_unit` | `objects`: one vote per square; `cells`: square area | `objects` |
| `keep_on_tie` | Boolean, inclusive versus strict comparison | `false` |

The default matches all three canonical train pairs and the one canonical test
pair under the protected Racket interpreter. `python_output` is a separate
mirror used for parity and rival checks. All produced episode labels come from
`RacketLabeler`, not the mirror.

## Four demonstrations that teach the setting

These side-length profiles occur once each, in a seed-shuffled order. Layout
and the two foreground colors vary independently of the hidden parameters.
For the same seed and canvas, all four settings receive exactly the same input
grids in the same order.

| Profile | Square sides | Odd : even objects | Odd : even area |
| --- | --- | --- | --- |
| A | 1, 1, 7, 4, 6 | 3 : 2 | 51 : 52 |
| B | 5, 5, 2, 2, 2, 6 | 2 : 4 | 50 : 48 |
| C | 1, 3, 2, 4 | 2 : 2 | 10 : 20 |
| D | 1, 1, 1, 1, 2 | 4 : 1 | 4 : 4 |

| Fixed setting | A | B | C | D |
| --- | --- | --- | --- | --- |
| Objects, strict | Keep | Erase | Erase | Keep |
| Objects, keep ties | Keep | Erase | Keep | Keep |
| Cells, strict | Erase | Keep | Erase | Erase |
| Cells, keep ties | Erase | Keep | Erase | Keep |

A and B distinguish object count from area in both directions. C and D isolate
the appropriate tie policy. A also distinguishes object voting from side-length
or perimeter voting and area voting from incorrectly counting the plus's five
cells. B defeats a largest-square-only decision in the area variants.

The certificate filters four lawful parameter settings and eight explicit
shortcuts using demonstration outputs only: always keep, always erase, strict
or inclusive side-length votes, largest-square parity, area including the plus,
omitting centers, and identity. A query is identifiable only if a lawful setting
survives and every surviving candidate predicts the same full output. Query
output fields are deliberately ignored by `certify`.

This is a finite rival check, not a claim of unique induction among all programs.
Four fresh query profiles cover count/area disagreement and both kinds of ties.
Additional queries reuse structural profiles with new layouts, never duplicate
the actual pair. Demonstrations and queries are all distinct by input bytes.

## Run

From the packet's outer directory, with the bundled Racket setup completed:

```bash
python3 review.py setup
python3 review.py run python3 generators/a2d9d069c7d5/workspace/parametric/prototype.py \
  --all-settings --seed 17 --demos 4 --queries 4 \
  --out ../checks/parametric/new-four-settings
```

Use a new output directory. Omit `--all-settings` and use `--vote-unit cells`
and/or `--keep-on-tie` for a single fixed setting. Independent controls are
`--demos 4..20`, `--queries 1..32`, `--height 16..30` and `--width 16..30`.
Seeds are exact integers in `0..2**64-1`. Boolean numeric aliases are rejected.
Default output is four demonstrations and four queries on 20 by 20 canvases.

The scene domain is 4..12 separate solid squares, sides 1..7, with total block
area greater than five. Placement has 80 restarts and 200 attempts per object;
distinct-input selection has 64 attempts per pair. Unsupported or crowded
layouts fail explicitly. The accepted ranges are not a guarantee that every
arbitrary side profile fits every canvas or that every seed succeeds.

Run the focused regressions with pytest installed in the chosen interpreter:

```bash
python3 review.py run python3 -m pytest \
  generators/a2d9d069c7d5/tests/test_parametric.py -q -p no:cacheprovider
```

## Export and replay boundary

`public/<sha256>.json` contains train inputs/outputs and query inputs only.
Names hash the exact bytes from the shared `public_challenge_bytes` helper;
files and the batch ID list are sorted by public ID. Hidden settings, seeds,
Racket programs, certificates and query answers live in `private/episodes.json`.
The writer rejects duplicate visible challenges before creating a destination.

`build_episode` labels every pair with Racket, checks the Python mirror and
requires demonstration-only identification. `verify_episode` checks the
parameter/program binding, distinct inputs, exact integer label types, every
label by Racket replay and the recomputed certificate. It is available for
episodes loaded from a private export:

```python
with RacketLabeler() as labeler:
    for episode in episodes:
        verify_episode(episode, labeler=labeler)
```

`write_batch` is a type-checked projection, not an attestation. Call it with
freshly built or explicitly replayed episodes. It rejects malformed private
labels, but does not independently replay semantically wrong integer labels.
Do not use a public ID as a certificate of private answer correctness.

## Evidence and next decision

The returned `checks/parametric/` evidence contains the four-setting export,
source/program hashes and certificates. Focused tests cover default labels,
hand-counted votes, same-seed parameter independence, distinct inputs,
demonstration-only selection, independent counts and a 30 by 23 canvas, export
privacy, duplicate rejection and reference-label tampering. An independent
review reproduced float/integer and Boolean/integer label aliases; exact type
validation and two regression tests now reject them.

The next useful decision is maintainer review of this small parameter family
and its curriculum coverage. Production integration, broad distribution/census
claims and training admission are separate work.
