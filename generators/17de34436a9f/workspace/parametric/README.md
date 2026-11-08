# Native `rotation_sense` family for `17de34436a9f`

Status: **reviewer-ready proposal; owner qualification/acceptance pending**.
The production generator and canonical rule remain unchanged.

Each episode fixes one private rule setting:

| `rotation_sense` | Corner-to-rotation mapping |
|---|---|
| `clockwise` | Canonical: TL=0, TR=90° CW, BR=180°, BL=90° CCW. The returned program is byte-for-byte the canonical Racket authority. |
| `counterclockwise` | TL=0, TR=90° CCW, BR=180°, BL=90° CW. |

Both settings require the same sequence: locate the corner marker, derive an
input-dependent quarter-turn count, remove the marker and crop the connected
body, then rotate the crop by that count. Inputs are matched across settings.
The first two demonstrations cover both marker branches used by the four query
profiles (top-right and bottom-right). Demonstrations three and four add the
top-left and bottom-left branches; five and six add larger cases.

The sampler supports 2–6 demonstrations and 1–4 prefix-stable queries. A
one-query request has exactly the same first visible query as a four-query
request, and changing the demonstration count does not change query inputs.
The four-query profile includes a dense 30×30 input whose connected body touches
non-marker boundaries and occupies hundreds of cells rather than padded empty
space.

From the extracted packet root:

```bash
python3 review.py run python3 \
  generators/17de34436a9f/workspace/parametric/prototype.py \
  --out generators/17de34436a9f/workspace/parametric/evidence/current
```

The writer executes both retained episodes through protected Racket, checks a
32-seed × two-setting × five-demo-count finite shortcut audit, and writes public challenges using
`reviewer_support.public_challenge_bytes`. Settings, programs and query answers
remain only in private evidence. The finite rival set is not a uniqueness proof.
Training admission remains false.
