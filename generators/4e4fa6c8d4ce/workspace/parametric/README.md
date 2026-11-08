# Proposed `mask_mode` rule parameter

This directory is a **task-local prototype** for ARC family `6ecd11f4`
(review task `4e4fa6c8d4ce`). It does not change the selected production
Racket authority or the canonical `generate(...)` path.

## Parameter

`mask_mode` is chosen once per episode from the episode seed and remains fixed
for every demonstration and query.

| Value | Transformation |
| --- | --- |
| `filled` | Canonical/default: copy a palette cell when the corresponding large block is filled; otherwise write `0`. |
| `empty` | Proposed alternative: copy a palette cell when the corresponding large block is empty; otherwise write `0`. |

The reasoning structure is unchanged: identify the uniquely most-common shape
color, recover its logical block mask, recover the dense palette, align their
coordinates, and select palette cells. Only the selected mask polarity changes.
Inputs must contain both filled and empty logical mask cells and a nonzero dense
palette; the selected generator already enforces those conditions.

## Files

- `prototype.py` builds complete episodes, executes both exact Racket programs,
  checks Python parity and parameter-rival distinguishability, and emits redacted
  public challenges.
- `rules/filled.rkt` is the exact canonical program. Its normalized hash is
  `adb72b5aa400`.
- `rules/empty.rkt` is the proposed complement-selection program.
- `examples/episode-a.json` and `examples/episode-b.json` contain public-form
  challenges: demonstrations include labels, queries omit labels, and neither
  file contains the hidden parameter or reference program. The private mapping
  is retained only in the evidence report.

Do not distribute this README, the rule files, or the private evidence alongside
a challenge whose parameter is meant to remain hidden.

## Reproduce

From the outer extracted packet directory:

```bash
python3 review.py run python3 \
  generators/4e4fa6c8d4ce/workspace/parametric/prototype.py \
  --seed 20261023 \
  --difficulty medium \
  --start-index 0 \
  --n-train 3 \
  --n-test 1 \
  --out ../checks/parametric/mask-mode-evidence.json \
  --public-dir generators/4e4fa6c8d4ce/workspace/parametric/examples
```

The retained run checks four Racket-labeled pairs for each setting. Both
complete episodes refute the alternative setting in their demonstrations, both
Racket sources match their Python mirrors on all eight applications, and the
same lawful input produces different outputs under the two settings.

Focused tests live in
`generators/4e4fa6c8d4ce/tests/test_parametric_mask_mode.py`.

## Limits

This is bounded evidence for two values and one four-pair episode per value. It
is not a production parametric API, approval, training admission, or proof over
all seeds. The variant relies on mixed masks; an all-filled or all-empty mask
would make one side degenerate and is intentionally outside the prototype input
domain.
