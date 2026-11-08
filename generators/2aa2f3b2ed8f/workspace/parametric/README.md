# Proposed mover variants for the tailed-rectangle task

This task-local prototype consumes a creature's straight tail, then moves one
rectangle across the gap until the two rectangles touch. The episode-fixed
parameter `mover` has two values:

| Setting | Transformation |
|---|---|
| `body` (canonical default) | Erase the creature, then translate its rectangular body toward the solid target. |
| `target` (proposed alternative) | Erase the tail and target, then translate the target toward the stationary body. |

The default `canonical.rkt` is byte-for-byte the unique selected canonical
program. `target.rkt` changes which object is erased and translated while
retaining body extraction, tail direction, gap measurement, and contact geometry.
The unchanged production `generator.py` and canonical authorities retain their
existing status. This prototype does not grant variant acceptance or training
admission.

## Runnable export

From the packet's **outer directory containing `review.py`**, with its declared
Python dependencies installed and bundled Racket selected:

```bash
source WORK/.venv/bin/activate
python3 review.py run python3 generators/2aa2f3b2ed8f/workspace/parametric/export.py \
  --seed 17 --demos 3 --queries 4 --out ../checks/my-mover-example
python3 review.py run python3 generators/2aa2f3b2ed8f/workspace/parametric/export.py \
  verify ../checks/my-mover-example
```

Use a new output directory. Both settings are exported. The native protected
Racket worker executes every demonstration and query label and fits the two
candidate programs to demonstrations alone before the exporter publishes files.
The second command checks the serialized bundle; it does
not independently rerun Racket or authenticate a rewritten untrusted receipt.

Only a single selected file from `public/` is a model-facing turn. Each contains
all demonstration input/output pairs and **one query input**. Names are hashes
of the exact public bytes using `reviewer_support`, without seeds, settings,
answers, turn numbers, or total-count hints. The private controller mapping
stores the ordered query IDs, four labels, programs, and setting. The existing
consumer selects the next ID only after the preceding answer; do not give the
model the directory listing or private controller data. One-query evaluation
and four-query training have identical first-turn bytes for the same
seed/settings/demo count. This artifact does not implement a turn controller.

## Domain and reproducibility

`adapter.generate(seed, settings, demos=3, queries=4)` supports exact integer
seeds in `0..2**63-1`, 2–6 demonstrations, and 1–4 independently selected queries.
The ordinary command uses three demonstrations and four queries. Invalid keys,
parameter types, counts, and seeds fail explicitly. Output pairs carry Python
claims until checked by the protected Racket worker.

Both settings use identical inputs at the same seed/counts. Independent
seed-derived input streams keep the rule setting out of the sampler; adding
queries never changes demonstrations or earlier queries. Inputs must be distinct
across all pairs; a bounded 32-attempt duplicate guard fails instead of silently
shortening an episode. The current geometric profiles have distinct dimensions,
so ordinary generation does not rely on retries.

Two constructive demonstrations suffice to identify the declared setting: each
has a positive gap, so moving the body and moving the target give different
outputs. The first two demonstrations use perpendicular directions, reverse
which role is larger, and reverse body/target color order. This exposes
fixed-direction, size-only, and lower/higher-color choices without adding demos. Body
extraction, tail removal, direction recovery, and full-gap motion remain causal
steps. Finite-rival identification is not a uniqueness proof against arbitrary
programs.

Four queries exercise all directions, with seed-dependent rotations of these
profiles:

| Base canvas | Body | Target | Tail length |
|---|---|---|---|
| 2×4 | 2×2 | 1×1 | 1 |
| 16×22 | 7×8 | 10×8 | 6 |
| 24×29 | 12×8 | 20×14 | 7 |
| 30×30 | 9×11 | 30×11 | 8 |

The 30×30 case has 437 non-background cells, spans the full canvas, and contacts
all four boundaries. The larger cases extend body/target sizes and tail lengths
beyond the unchanged canonical sampler; they are not padded small puzzles.
The minimum 2×4 case (or its rotation) is the compact rectangular-body grammar
boundary. Arbitrary scene sizes are not advertised as controls. Two objects are
essential to the selected canonical rule, so extra distractor objects are outside
this proposed grammar. Colors, transverse offsets, tail attachment, and direction
vary deterministically with seed.

## Verification and owner handoff

Focused tests live in `../../tests/test_parametric.py` and
`../../tests/test_parametric_export.py`. The core suite checks literal minimum
labels in four rotations, all available canonical labels for the default,
matched-input/count/prefix contracts, invalid controls, and protected Racket
parameter identification at seeds 0 and 17 with 2, 3, and 6 demos and four queries.
The export suite checks actual publication and adversarial serialized changes.
Current source/evidence hashes are recorded by the native manifest under
`evidence/manifest.json`; see `evidence/current/` and the packet's `checks/` for
executed results and their stated limits.

`promotion.json` and the thin adjacent-path adapter follow the native contract.
After integrating the source delta and reviewing the parameter semantics, the
owner may use the existing `parametric qualify` and `parametric accept` workflow
in `docs/parametric-promotion.md`. Those separate actions were not performed by
this reviewer. Broad production batteries, unassigned families, and training
runs are outside this prototype's verification scope.
