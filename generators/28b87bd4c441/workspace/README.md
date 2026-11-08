# Shape-teaching verification

`verify_shape_teaching.py` checks the version-2.1 ten-profile curriculum through
the public API and unchanged canonical Racket authority. It is authoring tooling;
production generation still selects `../generator.py`.

From an extracted packet's outer directory, with the prepared Python environment:

```sh
python3 review.py run --receipt checks/teaching-command/command.json \
  ../.venv/bin/python generators/28b87bd4c441/workspace/verify_shape_teaching.py \
  --out ../checks/shape-teaching --seed 17
```

Choose new receipt and output paths for a repeat. From a prepared repository
with Python 3.12+, its runtime dependencies and Racket, run the same script
directly, for example with `--out var/checks/new-shape-teaching --seed 17`.

## What it builds and checks

- One public JSON challenge with ten demonstrations and four distinct query
  inputs. Its filename is the SHA-256 of its exact public bytes. Only this file
  is intended for a learner.
- Separate `private/` inputs, source/rule snapshots, Racket results and query
  labels. Private query labels are not consulted by lesson identifiability.
- One 55-input canonical Racket batch: four original labeled cases, fourteen
  public-lesson inputs, three eleven-input ordered lessons (easy/medium/hard),
  and four hand-built U-shape boundary cases. Some medium-lesson inputs repeat;
  the report does not call all 55 inputs distinct.
- Concrete demonstration pairs with the same dimensions and direction but
  different shape offsets, refuting the fixed-template family independently
  of the generator's profile declarations.
- Exact source, canonical-program and executed-program identities; agreement
  with the Python mirror and original canonical labels; malformed-label
  rejection; and bounded query-duplicate retries with retained skipped draws.

The issued review run passed 55/55 Racket comparisons, 4/4 canonical labels,
and all three ordered difficulty lessons. Its evidence lives in the return's
`checks/shape-teaching/`; `receipt.json` identifies every retained file. The
saved public challenge passed `check_public_exports.py --queries 4 --demos 10`.
An attempted reuse of the existing output directory exited 2 and left all nine
existing files byte-for-byte unchanged.

Failures retain a failed/interrupted receipt and exit visibly. An existing output
directory is never reused. This is a one-seed, finite check of ordered lessons;
it does not establish arbitrary-shape generalization, arbitrary query holdouts,
source approval, audit closure or training admission.
