# Crop-contract probe

`probe_crop_contract.py` is a reusable diagnostic for the selected `../generator.py`. It imports the current `CANONICAL_SHORTCUTS` declaration, checks each rival against every labeled canonical pair, validates generated inputs, counts disagreements and exact unique inputs, and records the first counterexample for each rival. Reports include generator and canonical-data SHA-256 values, seed/index ranges, command and working directory.

From the extracted outer packet root, after its documented runtime setup:

```sh
python3 review.py run python3 generators/b8aea529acfd/workspace/probe_crop_contract.py --seeds 7301 91327 --per-band 200 --out ../checks/crop-contract-new.json
```

Use the interpreter configured for your packet if its dependencies are installed in a virtual environment. Choose a new output path for each run; the probe refuses to overwrite existing evidence. It uses portable `reviewer_support` root and canonical-data helpers.

Canonical comparisons use retained labels. Generated comparisons use the task's Python `rule_mirror`; the probe does not execute the reference and must not be cited as a Racket label check. Use the public `arcpuzzles apply` command for exact authoritative witnesses, and `arcpuzzles lesson-census --rotate-query` for actual assembled lessons and query rotations. A raw draw frequency does not establish lesson coverage after rejected duplicates.

The final review probe used two seeds × three difficulty bands × 200 indices: 1,200 draws, 1,160 unique grids and 600 joint witnesses, with no validator errors. The return retains that report at `checks/crop-contract-final.json`. Regression tests are in `../tests/`; exact reference-checked fixtures are in `../counterexamples/`.
