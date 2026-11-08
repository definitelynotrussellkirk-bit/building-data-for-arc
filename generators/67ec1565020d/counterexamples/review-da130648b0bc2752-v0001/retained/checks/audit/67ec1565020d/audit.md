## 67ec1565020d

**A67-1 — Suspected shortcut: solid-rectangle support makes mask preservation unobservable.** This is a findings-only audit of the immutable assigned baseline, not a source repair. I reproduced an accepted reference-lawful witness separating the intended recolor operation from a canonical-fitting rival. I did not find an incorrect label on a generated input and did not measure a generated lesson whose query differs under this rival.

### Finding and evidence

The canonical written rule says to recolor each monochrome object according to its bounding-box aspect: horizontal→2, vertical→3, square→4. Its Racket rule paints `obj-cells`, preserving the object's occupied-cell mask. A plausible alternative applies the same aspect classification but paints every cell inside the object's bounding box. These two operations agree on every solid rectangle.

Every canonical pair (three train and one test, **4/4**) contains only solid rectangular objects and the rival matches all four saved canonical outputs. The selected generator fixes its ordinary shapes to `SQUARE_2X2`, `H_LINE_3`, and `V_LINE_3`; its degenerate branches also use only those solid shapes. Positions and palettes vary, but geometry never supplies a distinction between mask-preserving recoloring and bounding-box filling. This conclusion follows directly from the selected source, independently of the finite census.

A direct generator census used seed **670004**, sample indices **0–99 inclusive**, empty overrides, and explicit difficulties **easy**, **medium**, and **hard**. Each band produced **100/100 unique inputs**, **100/100 validator-accepted inputs**, and **300 components**. Across **300 inputs / 900 components**, **0 components** were non-solid. Unique-input counts are per band; no cross-band unique count or production lesson materialization is claimed. The probe records every sampled input hash and identity in `probe.json`. It inspects generator outputs and the rival against saved canonical pairs; it does not independently create reference labels for the 300 sampled inputs.

### Small exact counterexample

`input.json` is a hand-built **6×9** grid with three separated monochrome blobs: a three-cell L with a 2×2 square bounding box, a horizontal three-cell bar, and a vertical three-cell bar. It has zero background, exactly three distinct nonzero colors, all three aspect classes, and no touching between separate blobs. The grid meets the declared grid-axis ranges and all listed `INVARIANTS`; `self_check(input)` returns **[]**. The L shape is outside the actual sampler's shape support, so the witness is **not sampled**; seed, sample index, and overrides are null.

Supported Racket execution succeeds with `valid_output: true`, no error, and the selected canonical rule hash. At zero-based **(row 2, column 2)** the input is background 0. The official result keeps **0**; the rival paints **4**. Every other cell agrees. `counterexample.json` retains the exact input, full official output, full rival output, one-cell difference, source identities, command, working directories, and acceptance facts. The authoritative raw apply receipt is `racket.json`, and executable rival/source-census code is `probe.py`.

The official command was run from the packet root:

```text
python3 run_with_racket.py python3 -m arcpuzzles apply 67ec1565020d --input ../checks/audit/67ec1565020d/input.json --out ../checks/audit/67ec1565020d/racket.json
```

The wrapper's actual payload working directory was `/workspace/scratch/5d8b66323a0c/work/repo`. Exit code was **0**. No private reference-runner function was imported.

### Source identity and limits

- Generator version: **1.1.1**.
- Generator SHA-256: `9352d6f059db06fd37c727cfe59a391d255b227cea45fe98ffc58a5f9e33e90b`.
- Executed/catalog rule hash: `b45100a04df9` (matching).
- Executed rule text SHA-256, copied verbatim from apply receipt: `d04c90db31adeefd20e81995f44e0a62db09191e15109de52758f44cdc706def`.
- The unwrapped canonical `program_solution` string is separately hashed in `probe.json` as `canonical_raw_rule_text_sha256` in `counterexample.json`; its digest and the executed rule-text digest intentionally refer to different serialized reference representations.
- Supporting generator-context, shape-helper, and grid-helper hashes are retained in `probe.json` and `commands.json`.

The demonstrated distribution restriction prevents generated examples from teaching preservation of absent cells inside a blob's bounding box. This is a **suspected shortcut**, with a concrete separating witness, rather than a claim that generated labels are wrong. It also leaves a **domain question**: if the owner deliberately restricts this task to solid rectangles, the rival is extensionally equivalent on that restricted support; however, no such restriction appears in the written rule or stated invariants, and the target validator accepts the witness. Sampling irregular connected objects would expose the distinction. No change is proposed or applied in this audit.

No full battery, private solve, packaging, or generated-lesson ambiguity census was run. The attempted read-only `git status --short` failed with exit **128** because the extracted packet lacks Git metadata; the failure is retained in `git-status-failure.log`. This did not block the audit or cause source edits. Exact productive commands, cwd values, exit codes, and evidence paths are in `commands.json`.
