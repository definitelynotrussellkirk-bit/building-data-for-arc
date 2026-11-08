# Counterexample: swap versus descending color sort

Assignment: `review-86f9efd9c687c23d`  
Task: `42a28f889145`  
Final generator SHA-256: `b2cadd67ac405bbcf3a5ffba4fda02d6c483c1a028d760830fa74c91f38ac5a6`  
Canonical rule hash: `57cc84264d9e`

The strongest canonical-only rival paints the numerically larger color on the
left and the smaller color on the right. It fits all 3/3 labeled canonical pairs
because each canonical input starts with the smaller color on the left.

The retained witness was generated with seed `9`, sample index `1`, no difficulty,
and overrides `grid_h=7`, `grid_w=9`, `shape_pair=0`, `color_pair=0`. The selected
validator reports it valid.

## Input (left color 2, right color 1)

```text
000001100
000000100
220000000
020000000
000000000
000000000
000000000
```

## Intended swap output (independent oracle and Racket agree)

```text
000002200
000000200
110000000
010000000
000000000
000000000
000000000
```

## Descending-sort rival output

```text
000001100
000000100
220000000
020000000
000000000
000000000
000000000
```

The rival leaves this input unchanged, so it disagrees on all six occupied
cells. `python_probe.json` records canonical fit, the independent oracle, rival
output, object cells, and exact generator provenance. `racket_apply.json` records
the selected Racket output, matching rule hashes, grid hashes, and generator
domain result. `input.json` is the supported `arcpuzzles apply` payload.

Reproduce the Python evidence from `WORK/repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/42a28f889145/workspace/probe_shortcut.py \
  --out generators/42a28f889145/counterexamples/review-86f9efd9c687c23d-v0001/python_probe.json \
  --input-out generators/42a28f889145/counterexamples/review-86f9efd9c687c23d-v0001/input.json
```

Reproduce the authority evidence from `WORK/` using a fresh output filename:

```bash
python3 run_with_racket.py python3 -m arcpuzzles apply 42a28f889145 \
  --input generators/42a28f889145/counterexamples/review-86f9efd9c687c23d-v0001/input.json \
  --check-generator-domain --timeout 120 \
  --out generators/42a28f889145/counterexamples/review-86f9efd9c687c23d-v0001/racket_apply-replay.json
```
