# Border-thickness rule family (prototype only)

This directory is separate from the selected canonical execution path. It does
not change the canonical Racket authority, selected rule hash, or production
generator.

- Parameter: `border_thickness`
- Allowed values: `1`, `2`
- Canonical/default setting: `1`
- Episode selection: `ALLOWED_BORDER_THICKNESSES[seed % 2]`, once per episode
- Input constraint: each foreground colour forms one solid rectangle, every
  rectangle side is at least five, and foreground colours are distinct.

For thickness `t`, each rectangle retains exactly the cells whose distance from
its bounding-box edge is less than `t`. Thus `1` is the canonical one-cell frame
and `2` is a two-cell-thick frame. The probe builds two labelled demonstrations
and one query, executes exact standalone Racket programs for both settings on
every pair, checks a Python mirror secondarily, and verifies that each
demonstration refutes the alternative setting.

Run from the outer packet directory:

```bash
python3 review.py run python3 \
  generators/ec491e97a5d5/workspace/parametric/prototype.py \
  --seed 17 \
  --out ../checks/parametric/border-thickness-seed17.json \
  --write-public generators/ec491e97a5d5/workspace/parametric/examples
```

The public files omit both the hidden parameter and query answer. This is a
bounded prototype, not production approval. Its concise standalone Racket uses
one rectangle per colour; the production generator’s repeated-colour object
semantics remain covered by the canonical repair, not by this prototype.
