# Split-motion parametric prototype

This isolated prototype keeps the original family recognizable: detect the unique
modal background, split the connected two-color shape at the floor midpoint of
its bounding box, swap the two shape colors, and use the same canonical shift
magnitude (full bbox width except for the black/nonblack-span branch).

Two episode-level parameters vary the executed motion:

- `moving_half = top | bottom` (canonical/default: `top`)
- `direction = right | left` (canonical/default: `right`)

`top + right` returns the selected canonical Racket program byte-for-byte. The
other three settings are separate, unapproved rule variants. Parameters are
chosen once from the episode seed and remain fixed across three demonstrations
and one masked query. Prototype inputs are recentered inside a 24-column grid so
all four settings are legal without clipping; dimensions, colors, and the
black-specific shift branch still vary across pairs.

From the packet root:

```bash
python3 review.py run python3 generators/3dc5b297cfa2/workspace/parametric/prototype.py \
  --out ../checks/parametric/split-motion-v1
python3 review.py run python3 -m pytest -q \
  generators/3dc5b297cfa2/tests/test_parametric_motion.py \
  --junitxml=../checks/parametric/pytest.xml
```

The prototype command executes the canonical anchors and every episode label
with the included Racket bridge, cross-checks an independent Python oracle,
materializes exact Racket for all four settings, and writes private evidence plus
public challenge files with hidden parameters and query answers removed.

This is a proposed authoring extension with finite evidence. It does not alter
the selected generator API, canonical Racket authority, approval state, or
training eligibility, and it does not establish universal identifiability or
measured data value.
