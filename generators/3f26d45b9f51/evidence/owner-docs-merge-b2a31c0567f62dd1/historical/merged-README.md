# `connection_axes` prototype

This directory contains an isolated **proposed, unapproved** extension for generator `3f26d45b9f51`. It does not modify `generator.py`, the canonical puzzle ledger, approval state, or shared runtime code.

The hidden episode parameter is `connection_axes`:

- `both` — byte-exact canonical rule and default behavior;
- `horizontal` — fill same-color intervals only within coarse rows;
- `vertical` — fill same-color intervals only within coarse columns.

One setting is chosen for the complete episode. The deterministic chooser cycles settings every seed while difficulty changes only after a complete three-setting block, so setting and difficulty are balanced rather than aliased. The default evidence build aligns to one such block and creates one same-difficulty episode per setting, with three labeled demonstrations and four unlabeled public queries. Every retained label is executed by the packet's protected Racket runtime and compared with the independent Python mirror.

From the extracted packet root, build evidence once with:

```bash
python3 review.py run python3 \
  generators/3f26d45b9f51/workspace/parametric/verify.py \
  --out ../checks/parametric/connection-axes-v1 \
  --start-seed 20261023 \
  --demo-count 3 \
  --query-count 4
```

The builder refuses to overwrite an existing output directory. `private/` contains rule sources, selected settings, query labels, and all-setting disagreement evidence. `public/` contains only demonstration inputs/outputs and query inputs; filenames are SHA-256 identifiers derived from those visible bytes. Duplicate visible payloads are rejected and report rows are sorted by public ID. `report.json` records source/runtime hashes and bounded conclusions, while `manifest.json` hashes every retained evidence file.

Run the focused regression from the packet root with:

```bash
python3 review.py run python3 -m pytest -q \
  generators/3f26d45b9f51/tests/test_parametric_connection_axes.py
```

Passing this prototype evidence is not production approval. Promotion would require an explicit review decision and a separate change to the production generator.


## Additional proposed implementations

[Additional lattice-axis and separate occlusion prototypes](README-b2a31c0567f62dd1.md) preserve the exact reviewer-authored instructions. The existing connection_axes writer follow-up remains unresolved. Both alternatives remain unapproved; occlusion is a separate inspired family with no verified lineage or admission.
