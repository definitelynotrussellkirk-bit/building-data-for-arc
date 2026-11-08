# Proposed `identity_corner` parametric prototype

This task-local authoring prototype leaves the selected production generator,
canonical Racket authority, approval hash, and production API unchanged. It
chooses one hidden setting once per complete episode:

| Parameter | Allowed values | Original/default |
|---|---|---|
| `identity_corner` | `top_left`, `top_right`, `bottom_left`, `bottom_right` | `bottom_right` |

The unchanged input occupies the selected output quadrant. Reflecting across the
horizontal seam determines the opposite row of quadrants; reflecting across the
vertical seam determines the opposite column. Thus every setting still uses the
same four transformations—identity, vertical flip, horizontal flip, and 180°
rotation—and only their natural seam-consistent placement changes. The canonical
`bottom_right` program is loaded byte-for-byte from the canonical ledger.

Every retained input comes from the selected generator and must have four distinct
reflection variants, so all four parameter settings yield different answers. Input
sampling depends on seed, split, and draw index, never on the hidden setting. The
default episode has **3 demonstrations and 4 distinct queries**, with independently
configurable positive counts and one setting fixed across all pairs.

From the packet extraction root, run the focused tests:

```bash
python3 review.py run python3 -m pytest \
  generators/90640e0e6314/tests/test_parametric_prototype.py -q
```

The Racket-backed evidence command is:

```bash
python3 review.py run python3 \
  generators/90640e0e6314/workspace/parametric/verify.py \
  --seed 20261023 \
  --out ../checks/parametric/90640e0e6314-identity-corner-verification.json \
  --artifact-dir ../checks/parametric/90640e0e6314-artifacts
```

The verifier materializes one complete episode per setting, executes every stored
label and every finite rival through the bundled protected Racket bridge, checks
Python parity, and writes answer-free public challenges under opaque identifiers
derived only from their visible bytes. Private parameter maps, Racket programs,
seeds, and query answers stay in private artifacts.

This is bounded **proposed prototype** evidence. It does not approve variant rules,
change catalog status, establish an exhaustive hypothesis class, or admit examples
to training.
