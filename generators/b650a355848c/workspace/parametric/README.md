# Marker-assignment parametric family

`assignment_policy=independent_nearest` is the exact canonical program: each
pink shape independently selects the nearest singleton marker by bounding-box
Manhattan distance, so one marker may color several shapes.
`assignment_policy=minimum_bijection` instead computes the unique
minimum-total-distance one-to-one assignment, then uses that input-dependent
mapping to recolor and stack the shape crops.

The generated grammar keeps 3–5 separated 6–10-cell pink polyominoes and the
same number of distinct singleton markers. Every sampled scene has unique
per-shape nearest markers, a unique global optimum, and a deliberate conflict
where independent nearest reuses a marker. Inputs are matched across settings.
The first two demonstrations are complementary constructive lessons: together
they reject nearest-occupied-cell, greedy-unused-marker, axis-order pairing,
and accidental color-order pairing without increasing the demonstration count.
Up to six demonstrations are supported. Four independently requested query
profiles include 11×17, 17×12, 24×27, and a spread 30×30 five-shape stress case
in seed-shuffled order.

The required sequential dependency is:

1. **A:** compute the input-specific nearest choices or global assignment from
   every shape bounding box to every marker.
2. **Intermediate:** the ordered shape→marker/color mapping.
3. **B:** paint each cropped shape in its assigned color and stack the crops in
   the input-orientation order. B cannot choose its colors before A returns.

`rivals.py` contains eight explicit Python/executable-Racket shortcut rules.
`audit.py` checks minimum, ordinary, and maximum demonstration counts across a
bounded sampler census, then verifies shortcut parity and lesson outcomes in
protected Racket. A survivor is reported as harmful only when it fits every
visible demonstration and changes at least one retained query.

Run the focused suite, bounded self-audit, and native qualification from the
packet outer directory:

```bash
python3 review.py run python3 -m pytest \
  generators/b650a355848c/tests/test_parametric_b650a355848c.py -q
python3 review.py run python3 \
  generators/b650a355848c/workspace/parametric/audit.py \
  --out ../checks/b650a355848c/self-audit
python3 review.py run python3 -m arcpuzzles parametric qualify b650a355848c \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/b650a355848c/qualification --summary
```

Python labels are sampler claims only. Qualification re-executes every retained
label through protected Racket. Public projection exposes all demonstrations and
one query input at a time; settings, programs, answers, future queries, seeds,
and total-query hints remain private. Passing reviewer evidence does not imply
owner acceptance or training admission.
