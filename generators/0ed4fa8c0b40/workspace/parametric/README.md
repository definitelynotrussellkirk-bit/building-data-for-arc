# Proposed copy-style and gap variants — prototype only

This directory is deliberately separate from the selected canonical generator.
It does **not** change the canonical Racket rule, `RULE_HASH`, approval state, or
production sampling path.

Two bounded rule parameters are chosen once per episode:

| Parameter | Values | Canonical/default |
| --- | --- | --- |
| `copy_style` | `mirror`, `translate` | `mirror` |
| `gap` | `0`, `1` blank columns | `0` |

All settings preserve the original reasoning structure: decode the five-cell
yellow arrow, identify the cyan support and its bounding box, choose the side
from the arrow, and paint a cyan copy while retaining the input. `mirror-gap0`
exactly matches the canonical transformation on the prototype's lawful inputs.
The alternative `translate` setting preserves column order rather than reversing
it; `gap1` leaves one blank column before the copy.

Inputs use asymmetric, 8-connected 3×3 cyan supports and reserve enough margin
for every setting. Demonstration and query counts are independent (`1..8` each),
draw from separate deterministic streams, and remain distinct from one another.
The default retained evidence uses three labelled demonstrations plus four
queries under one fixed hidden setting. Every label comes from the matching exact
Racket program; the demonstrations alone eliminate the other three declared
settings, and each query is checked without using any query answer as evidence.

Run the four-setting, four-query evidence command from the outer packet directory:

```bash
python3 review.py run python3 \
  generators/0ed4fa8c0b40/workspace/parametric/prototype.py \
  --seed 760 \
  --demos 3 \
  --queries 4 \
  --out ../checks/parametric/copy-style-gap-seed760-v2.json \
  --write-public ../checks/parametric/copy-style-gap-public-v2
```

The public writer uses `reviewer_support.public_challenge_bytes` and
`public_challenge_id`. Each filename is the full SHA-256 of the exact visible
bytes it contains; batch creation rejects duplicate visible payloads and sorts by
that public ID. Hidden parameters, seeds, reference code, setting order, and query
answers cannot affect a public filename. The private evidence receipt retains the
setting map, exact Racket text and query labels.

`examples/current/` contains one current checked-in public file for each
setting from seed 760, with three demonstrations and four queries. Those four
opaque filenames disclose no setting or seed and are the only examples emitted
or referenced by prototype v1.1.0. The four prior setting-named
`examples/*.json` files remain byte-for-byte as historical baseline fixtures
because the review delta format forbids source-file deletions; they are not
current public exports and remain documented by the preserved prior manifest.
This is bounded prototype evidence, not production approval or a proof of
uniqueness against undeclared algorithms.
