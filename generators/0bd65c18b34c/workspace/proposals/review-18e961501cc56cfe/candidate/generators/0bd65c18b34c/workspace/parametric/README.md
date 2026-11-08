# Proposed nearest-square tie-break prototype

This task-local prototype keeps the original object detection, Chebyshev
nearest-square calculation, alignment test, source clearing, and target painting.
Only the equal-distance reducer varies:

- `tie_break=first` is the exact canonical/default Racket program and keeps the
  first square in row-major order.
- `tie_break=last` is proposed and replaces the single `<` comparison in the
  nearest-square reduction with `<=`, so the last row-major square wins a tie.

The hidden setting is selected once from the deterministic episode seed and is
fixed across every pair. Each retained episode uses three demonstrations and
four distinct queries generated from the lawful `large_four_balanced` profile;
every pair contains a same-row tie that distinguishes both settings. Labels are
executed by the matching Racket source. The Python implementation is only a
parity mirror. Public challenge files contain visible demonstrations and query
inputs only, and their 64-hex filenames are SHA-256 hashes of those exact visible
bytes.

From the outer packet directory:

```bash
python3 review.py run python3 \
  generators/0bd65c18b34c/workspace/parametric/prototype.py \
  --out ../checks/parametric/0bd65c18b34c-tie-break/evidence.json \
  --public-dir generators/0bd65c18b34c/workspace/parametric/examples \
  --demos 3 --queries 4
```

This is a **proposed prototype**. It does not change the production parametric
API, canonical Racket authority, approval state, or training admission.
