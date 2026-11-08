# 70913cf98cee parametric family

`postprocess=direct` preserves the exact canonical legend-recolor program.
`postprocess=cycle_dominoes` first performs that recolor, then inspects the
resulting four-connected destination-color components. Every exact two-cell
component is repainted with the next destination color in cyclic legend order.

The second stage consumes topology created by the first. Each minimum lesson
contains mixed source/destination neighbors that become dominoes only after A,
source dominoes that merge into nonqualifying triominoes after A, qualifying
components for every destination, both horizontal and vertical orientations,
a diagonal four-vs-eight-connectivity trap, and an unmapped nuisance component.
The first two demonstrations use seed-randomized 3- and 4-pair anchors so cycle
direction is identifiable without increasing the two-demo minimum.

Inputs are identical across settings. The generator supports 2–6 demonstrations
and 1–4 count-independent query prefixes; the complete query bank always has four
distinct inputs, including a substantive 30×30 scene with quadrant and boundary
coverage. Source query order is privately permuted by the shared sequential
projection helper, which reveals one input per turn without answers, future
queries, turn numbers, or total-count hints.

Reusable review tools live beside the family:

- `adversarial_probe.py`: checks 19 concrete rival rules against minimum lessons.
- `sampler_stress.py`: checks count bounds, bank freshness, crossed controls,
  teaching coverage, density, boundaries, and malformed calls across many seeds.
- `verify_racket.py`: executes both setting programs through protected Racket.

From `WORK/repo`, focused tests are:

```sh
python3 -m pytest -q generators/70913cf98cee/tests
```

The retained manifest and authoring preflight are reviewer evidence only. Owner
source review, native qualification/acceptance, and training admission remain
separate and were not performed here.
