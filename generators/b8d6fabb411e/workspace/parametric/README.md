# Proposed `alignment_scope` extension

Status: **verified, unapproved prototype**. The selected canonical rule remains
`alignment_scope=span`; this workspace does not change canonical authority,
approval, catalog kind, or the production generator API.

The hidden episode-level parameter is chosen once from:

- `span` — canonical/default: markers fire from any row or column inside the
  color-3 square's full span.
- `boundary` — proposed alternative: markers fire only from the square's top or
  bottom row, or left or right column.

Both settings preserve the original reasoning structure: find the solid green
square, classify singleton markers by alignment, preserve diagonal decoys, and
paint a firing marker's color through the gap to the nearest square edge. The
only changed predicates are the two row-span and two column-span tests in the
exact canonical Racket source.

Retained inputs are lawful side-4 examples from the selected generator. Every
pair contains at least one interior-aligned marker and at least one
boundary-aligned firing marker, so both rules are nontrivial and disagree on
every retained pair. Three labeled demonstrations precede one masked query.
Public challenge JSON omits the setting, seed, source, hashes, rival metadata,
and query output.

## Run

From the extracted packet root:

```bash
python3 review.py run \
  python3 generators/b8d6fabb411e/workspace/parametric/prototype.py \
  --seed 0 --out ../checks/parametric/alignment-scope-v1
```

Equivalent from `WORK/`:

```bash
python3 run_with_racket.py \
  python3 generators/b8d6fabb411e/workspace/parametric/prototype.py \
  --seed 0 --out ../checks/parametric/alignment-scope-v1
```

Focused tests:

```bash
python3 review.py run \
  python3 -m pytest -q \
  generators/b8d6fabb411e/tests/test_parametric_alignment_scope.py
```

The retained evidence is under
`WORK/checks/parametric/alignment-scope-v1/`. It includes exact Racket text for
both settings, private labeled episodes, redacted public challenges, all eight
canonical-pair checks, a setting-difference witness, source snapshots, file
hashes, and a report. A second fresh run at
`alignment-scope-v1-replay/` produced the same semantic SHA-256
`bff86e7c76b137e89d369e2fc22e9bf4adc38c209d66c7227b72fbdb6683126c`.

## Limits

This is finite evidence for two settings and four deterministic fixtures per
episode, not proof of universal identifiability. The `boundary` rule fits all
supplied canonical pairs because their squares are side 2; larger-square
examples are therefore an explicit dependent input constraint. The alternative
is proposed only and is not selected, reviewed-safe, approved, or admitted for
training.
