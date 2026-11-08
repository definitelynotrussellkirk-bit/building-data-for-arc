# Native receiver-action family for `9baf979683ef`

## Rule family

The private episode parameter is `receiver_action`:

- `preserve` executes the selected canonical divider reflection **byte-for-byte**.
- `absorb_color` first executes the same reflection, then finds the unique
  color-9 receiver component touched by a newly mirrored source cell and
  recolors the entire receiver with that cell's color.

The input stream is identical across settings for the same seed and requested
counts. Settings, programs, and query answers remain private.

## Sequential dependency

The alternate rule is deliberately non-collapsing:

1. **A — mirror:** reflect every nonzero, non-divider source cell across the
   full-height color-5 divider.
2. **Intermediate:** the new mirrored field creates exactly one contact between
   a source color and one of at least three separated color-9 receiver
   components.
3. **B — absorb:** select the contacted component and paint all of its cells
   with the adjacent mirrored color.

B cannot select a receiver or its color from the original grid. The retained
protected-Racket witness executes the canonical A program, the full A→B
program, B alone on the original input, and B on an intermediate with the
contact removed. Both counterfactual final outputs differ from the lawful one:
`evidence/current/causal-witness.json`.

## Generation contract

`adapter.py` exposes `program(settings)` and
`generate(seed, settings, demos, queries)`. `promotion.json` supports:

- 2–6 demonstrations;
- 1–4 controller-side queries, with stable prefix behavior;
- exactly two settings, with `preserve` as the canonical default.

Each full episode contains ten distinct inputs. The six constructive
training profiles swap receiver size and horizontal ranks in the first two
examples, so the minimum two demonstrations distinguish the declared settings
and seven explicit shortcuts. The four query profiles are novel; the last is a
30×30 boundary case with four receivers and at least 28 source cells.

The finite rival audit tests: recolor every receiver, recolor only the contact
cell, use fixed color 2, choose the largest/smallest/leftmost/nearest-divider
receiver. Passing this finite list is not a universal uniqueness proof.

## Retained evidence

`audit.py` is the reusable authoring check. The retained run covers seeds 0–63:

- 128 maximum-size episodes and 1,280 labeled pairs;
- 640 teaching checks across every supported demonstration count;
- all seven non-divider source colors;
- smallest, middle, and largest target-size ranks;
- leftmost and rightmost receiver positions;
- every declared dimension profile, including 128 setting-specific 30×30
  boundary queries;
- 40 protected-Racket label replays and four protected-Racket causal
  counterfactual evaluations;
- four hash-named exact public projections with no private fields or query
  answers.

The native qualification retains two settings × seeds 0 and 17, with three
visible demonstrations and four private queries. It performed 40 protected
Racket evaluations and found only the selected setting surviving each lesson.
Qualification is reviewer evidence, not owner acceptance or training admission.

## Reproduce

From the packet root:

```sh
python3 review.py run python3 -m pytest -q \
  generators/9baf979683ef/tests/test_parametric_receiver_action.py

python3 review.py run python3 \
  generators/9baf979683ef/workspace/parametric/audit.py \
  --out generators/9baf979683ef/workspace/parametric/evidence/new-run

python3 review.py run python3 -m arcpuzzles parametric qualify \
  9baf979683ef --out ../checks/9baf979683ef/qualification-new --summary
```

Use a new audit/qualification destination. The source-bound manifest is
`evidence/manifest.json`; replacing it requires the exact prior manifest hash.
