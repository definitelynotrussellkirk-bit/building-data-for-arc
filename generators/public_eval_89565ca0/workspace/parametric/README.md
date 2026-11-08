# Occluded rectangular partitions

This is a new, unapproved public-parent authoring workspace for ARC task
`89565ca0`. Its immutable `workspace/public-parent.json` identifies the supplied
challenge record and test outputs. Root `reference.rkt` implements the general
canonical rule; root `generator.py` is portable with the declared shared runtime.

## Rule and parameter

Recover each structural color's rectangle and partial dividing walls. Adjacent
same-color pixels identify horizontal and vertical axes. Each genuine elementary
wall interval must retain an own-color witness strictly between its endpoints.
Other colors may obscure a wall; raw zero cannot. The unique scattered color
with off-axis pixels is noise. Count the four-connected rectangular rooms in
each reconstructed wall network, then render one row per object, repeating its
color by its room count and padding to the maximum count with the noise color.

| `sort_order` | Output ordering |
| --- | --- |
| `ascending` | Increasing room count; the exact root reference source |
| `descending` | Decreasing room count; equal-count ties retain their direction |

The tie convention is bounding-box left coordinate, then top coordinate, then
numeric color. The original labels do not uniquely establish this convention:
their sole observed equal-count pair also fits numeric color order. This spatial
choice is an explicit extension, taught by generated examples that disagree with
numeric and topmost-only ordering, including an equal-left tie.

The Python adapter accepts exact integer seeds in `0..2**63-1`, 2..6
demonstrations, and 1..4 queries. Settings have exactly one key, `sort_order`.
All settings use the same complete six-demo/four-query input banks for a fixed
seed. Query ordering has its own deterministic random stream; changing a count
only selects a prefix. No generator runs the reference interpreter internally.

## Admission and limits

Every grid uses exact list rows, exact integer colors 0..9, and dimensions at
most 30. At least two structural colors and one uniquely identifiable noise
color are required. Structural bounding-box extrema, axis support and elementary
interval witnesses must survive compositing. Consecutive axes are at least two
cells apart. Every observed structural pixel lies on its recovered network;
every recovered wall cell contains a nonzero input pixel. Room counts are 1..30,
and recovered rooms are rectangular.

These constraints intentionally exclude arbitrary erasure: a wall whose every
interior witness is overwritten need not be recoverable. The generator retains
latent walls and room counts, then accepts damage only when the recovered
geometry still agrees with that construction. Python labels are claims until
the separate protected Racket execution verifies them.

## Reproduce reviewer evidence

From the outer packet folder, using its independently set up Python and bundled
Racket, run commands through `review.py run`. Payload paths are relative to
`WORK/repo`; use a fresh receipt and output destination for every run.

```bash
WORK/.venv/bin/python review.py run \
  --receipt checks/public_eval_89565ca0/tests-new.json \
  python3 -m pytest -q generators/public_eval_89565ca0/tests

WORK/.venv/bin/python review.py run \
  --receipt checks/public_eval_89565ca0/audit-new-command.json \
  python3 generators/public_eval_89565ca0/workspace/parametric/audit.py \
  --seeds 0 17 43 --out ../checks/public_eval_89565ca0/audit-new.json

WORK/.venv/bin/python review.py run \
  --receipt checks/public_eval_89565ca0/preflight-new-command.json \
  python3 -m arcpuzzles.review_public_creation preflight public_eval_89565ca0 \
  --root . --out ../checks/public_eval_89565ca0/preflight-new
```

The public-creation evidence bridge under `WORK/checks/tools/` builds a
source-bound protected causal witness from this authoring preflight and exports
verified single-query views. Its README gives exact witness/export commands.
Only a selected public JSON is a model turn: private answers, settings, programs,
source indices, seeds and future queries remain with the controller.

Authoring preflight, finite rival checks and reviewer replay do not constitute
owner registration, native qualification or acceptance. The owner must verify
and register this public-parent source, accept its source review, refresh the
native inventory, and perform unchanged native qualification and fresh
acceptance. No training admission is claimed.

## Current verified result

The retained final evidence records 103 passing task tests, 152 demonstration
refutations against the named rivals, 20 maximum-seed Racket labels, four passed
authoring-preflight jobs, two replayed causal cases and 16 verified public views.
Four deliberate export corruptions were rejected. Current command receipts and
exact cases are under `WORK/checks/public_eval_89565ca0/`; historical failed
attempts are retained separately and do not approve later source bytes.

The portable generator exposes `noise_budget=8..32`, an exact count measured by
`observe_overrides(grid)`. A completed validated damage bank is prefixed only
after construction, preserving palette and latent geometry across this override.
The generated scenes use two or three structural colors. The native parser's
broader two-through-eight-color grammar is not a claim that every such input
profile is sampled.
