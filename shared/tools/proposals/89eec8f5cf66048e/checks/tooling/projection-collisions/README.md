# Optional projection-collision probe

`projection_gate.py` is a standalone, standard-library tool for one cheap
structural question: **can two supplied inputs have the same red-cell layout
but require different selected yellow centers or different output edit masks?**
It is a passive proposal for future review feedback. It does not modify the
shared controller, generate puzzles, execute Racket, import a generator, or
execute code supplied in JSON. The built-in color and coordinate semantics are
scoped to task `fc814cec3976`.

## Cheap rerun

From this directory, using Python 3.12+:

```sh
python3 projection_gate.py baseline_fixture.json --certify
python3 projection_gate.py baseline_fixture.json --target edit-mask --certify
python3 -m unittest -v test_projection_gate.py
```

No NumPy, pytest, Racket process, or environment installation is needed for this
tool. `--out new-report.json` writes a new report and refuses to overwrite an
existing file. Without `--out`, the complete report goes to standard output.
Receipt paths resolve relative to the input envelope file, independently of the
working directory.

The retained example depends on the existing exact receipt at
`../../canonical-investigation/structural-racket-raw-receipt.json`. Keep that
receipt with the packet. Its SHA-256 is
`f22ba6692f1826030946af6294cdd173d2aedf9f135855b4a1c7e1c4b8eb1e25`.

## What is compared

The input key contains the grid shape and all absolute, zero-based coordinates
whose input color is **2 (red)**. Shapes are included to avoid treating different
coordinate frames as the same key. The non-red context is hashed separately by
replacing red input cells with zero; within a fixed key, its distinct count is
an exact count of distinct remaining input contexts.

| Target | Definition | Intended interpretation |
|---|---|---|
| `yellow-centers` (default) | Coordinates with output color **4** and input color different from 4 | Newly selected yellow cells, used as a center proxy for this task |
| `edit-mask` | Coordinates where output differs from input | Which cells the reference changes; output color values are not part of this projection |

Both built-ins require rectangular 1–30 by 1–30 grids with literal integer
colors 0–9 and matching input/output shapes. Booleans, ragged grids, invalid
colors, duplicate case IDs, and conflicting output labels for an identical
input are rejected. Ordinary repeated inputs with identical labels remain in
the report, but do not create extra context coverage or witness pairs.

## Evidence envelope and label authority

`baseline_fixture.json` is a complete runnable example of the
`projection-cases-v1` envelope. The fields are:

| Field | Meaning |
|---|---|
| `schema` | Exactly `projection-cases-v1` |
| `task_id` | Task identity; certifying built-ins require `fc814cec3976` |
| `source.generator_sha256` | Exact generator bytes associated with the labels |
| `rule.normalized_hash` | Selected canonical rule's 12-character normalized hash |
| `rule.callable_sha256` | Public apply receipt's `rule_text_sha256`, which hashes converted callable Racket text |
| `scope` | Explicit provenance/population description, such as a baseline counterfactual |
| `label_authority.kind` | `selected_racket` for certifying mode; diagnostic mode can retain other declared kinds |
| `label_authority.receipt_path` / `receipt_sha256` | Exact public `arcpuzzles-apply-v1` receipt and its file hash |
| `examples` | Nonempty list of cases with unique `id`, `input`, and `output` |
| `examples[*].receipt_result_index` | The receipt row's actual `index`, required for certifying mode |
| Optional per-case hashes | `input_sha256` and `output_sha256`; if supplied, they must match the arrays |
| Optional per-case `scope` / `generator_domain` | Context retained in diagnostics; certifying mode obtains domain status from the bound receipt |

By default, label authority is reported as **declared only**. `--certify` refuses
missing provenance, unknown authority, and Python mirror labels. It verifies the
receipt file hash, task/source/rule identity, canonical-rule agreement, successful
reference results, and exact input/output arrays and hashes for every case.
It does **not** independently authenticate the supplied receipt or rerun Racket.
The word “certify” therefore applies only to the bounded collision calculation
and consistency with that retained authority receipt.

## Reading the result

- `witnessed_collision`: at least one input-projection key has two distinct
  contexts with different target projections. A predictor using only that key
  cannot give both observed targets on those cases.
- `unknown_no_witnessed_collision`: no such pair was found. This is **unknown**,
  not a universal pass, a universal failure, or permission to accept a generator.
- Exit **0** means a report was produced for either status; exit **2** means
  invalid input, refused authority binding, an unavailable file, or an existing
  output destination. The command never turns unknown into a failed generator.

Each key reports case counts, unique inputs, duplicate inputs, distinct
contexts, distinct targets, and an exact witness pair when present. The report
retains all case IDs and input/output hashes, projected targets, domain status,
envelope hash, and tool-source hash. Duplicate labeled cases are counted
separately. General learnability and generated support are always marked
`false` under their `*_certified` fields.

## Retained demonstration: baseline and off-support counterfactual

The fixture copies **exact receipt rows 0 and 1**, including their original
Racket labels. It is **not a final generated materialization**. The receipt
binds to baseline generator SHA-256
`a971dcfa81f9aca13cb3fa186f9600f1afdfeaaac42a1c86655a5f71f75b0ba4`, rule hash
`98e91a32d7ba`, and callable SHA-256
`c50118f2545766e6b154e05f9acc97029cb332d05984878bb2d9f0c509830529`.

The two 19×19 inputs share the same 13 red-cell coordinates and have distinct
non-red contexts. Their selected yellow centers differ at the last center:
the original has **(14,14)** and the modified case has **(14,13)**. The other
centers are **(6,5), (10,11), and (12,3)**. Both target modes witness one collision
key over two distinct inputs, with zero duplicates. The original input is valid
under the retained baseline validator, while the modified case is invalid.
`demo-centers.json` and `demo-edit-mask.json` explicitly retain that rejection
and do not claim coverage of the repaired generator's support.

## Limits and possible misinterpretations

A collision shows dependence on information omitted by this particular
projection. It does not establish that lessons teach the complete rule or
exclude other shortcuts. A dataset with no collisions may simply lack repeated
keys or sufficient context variation. Counts concern the explicit cases, not a
population prevalence estimate.

Off-support counterfactuals, mislabeled cases, mixed source/rule versions, and
incorrect target semantics can create misleading conclusions about production.
The provenance checks address several of these risks but do not prove that a
case was drawn by a final materializer. A valid `self_check` alone also does not
establish generated support. Obtain and retain that evidence separately.

The edit mask can change because an input cell already has its eventual output
color, even if selected centers are unchanged. Such a collision refutes an
edit-mask-only claim; it need not refute a center-prediction shortcut. The
yellow-center projection likewise assumes that newly yellow cells mean centers
for this task. It performs no object recognition, translation/rotation
normalization, color-role inference, or general semantic validation.

## Verification

All **15 focused unittest methods** pass in `tests-final.log`. They cover a
collision, duplicates, unknown outcomes, shape-sensitive keys, both target
projections, malformed grids, conflicting labels, and reference-provenance
requirements/binding. The unittest labels and its synthetic receipt test only
tool mechanics; the demonstration artifact uses the actual retained Racket
receipt. The expected initial test-first failure is preserved in
`tests-red.log`; `tests-green.log` and `tests-final.log` retain the succeeding
runs. Exact commands and final source hashes are in `RESULTS.json`.
