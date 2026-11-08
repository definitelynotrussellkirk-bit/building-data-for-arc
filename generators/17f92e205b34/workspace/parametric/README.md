# Complete reflection, then select components

## Design and implementation contract

This separate native prototype preserves the exact canonical default. Its one
episode-fixed parameter is `selection=all|largest|smallest`. All inputs share
the collision-free square reflection grammar. `all` is the selected canonical
program byte-for-byte. The alternatives first complete main-diagonal reflection,
then discover same-color four-connected components in the completed grid and
retain every component tied for the selected positive cell-area extremum.

Reflection can connect fragments and change their relative areas. Selection
therefore consumes the completed scene; selecting input fragments first is a
different executable rule. Neither a color remapping nor a fixed paint mask can
replace this input-dependent intermediate. A protected-Racket wrong-order
witness will bind the distinction to native-qualified source.

The supported API uses exact integer seeds 0..2**63-1, 3–6 demonstrations and
1–4 queries independently. The sampler constructs its full six-demo/four-query
bank before slicing. All settings use the same inputs, and one-query use has
exactly the first query of four-query use. A controller holds the other queries;
each public view contains only the demonstrations and one query input.

Implementation is split into `native_family.py` (semantics and exact programs),
`sampler.py` (constructive inputs), `adapter.py` (native API), and `audit.py`
(protected labels, declared rivals and public projections). Focused tests cover
typed boundaries, literal semantic cases, deterministic sampling and export
rejection. The audit uses three demonstrations, four queries, seeds 0 and 17,
and all settings; native qualification independently checks the declared family.
Substantive 30×30 queries supplement smaller scenes.

The production generator and reference authority remain separate. Its retained
scalar-call audit and lawful-short-line gate question are not resolved by this
prototype. Native qualification is reviewer evidence; owner acceptance and any
training admission are separate decisions.

## Verification and use

From the outer packet directory, run the complete bounded label/rival audit in
a new destination:

```sh
WORK/.venv/bin/python review.py run python3 \
  generators/17f92e205b34/workspace/parametric/audit.py \
  --out ../checks/17f92e205b34/audit-new
```

The native adapter can be loaded by exact path and called as
`generate(17, {"selection": "largest"}, demos=3, queries=4)`. It supplies
deterministic Python claim labels; the separate protected worker verifies them.
Omitting settings selects `all`, `largest`, or `smallest` deterministically from
`seed % 3`. `program(settings)` requires an exact one-key settings dictionary.

Native qualification of the frozen inventory is:

```sh
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  17f92e205b34 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/17f92e205b34/qualification-new --summary
```

After a source edit, refresh the native source inventory with its guarded
replacement command before qualifying again. Use the exact three native test
files as explicit includes. Existing output directories are refused.

For the retained qualification, the packet's existing exporter creates the
controller bundle without accepting the family:

```sh
WORK/.venv/bin/python review.py preview-public export \
  --qualification ../checks/17f92e205b34/qualification/qualification.json \
  --out ../checks/17f92e205b34/preview-new
WORK/.venv/bin/python review.py preview-public verify \
  --bundle ../checks/17f92e205b34/preview-new
```

Give the model one selected `public/<sha256>.json` at a time. The directory
listing, full bundle and `private/` stay with the controller: they reveal future
inputs, order, settings and answers. IDs hash only exact visible bytes. The
verifier checks current source and serialized projections, not another Racket
replay or authenticity of privately rewritten receipts.

## Current bounded result

The final check set passes 121 focused tests and all six native qualification
jobs (78 protected executions). `checks/17f92e205b34/audit-r2/audit.json` records
all 120 declared rival comparisons refuted by demonstrations, 369 unique
protected executions, 42 generated labels and three canonical pairs. Native
causal construction/replay proves changed final labels for selection before
reflection: 8 cells for largest and 10 for smallest in the chosen qualified
example. Twenty-four single-query exports verify; three corrupted-copy cases
are rejected. Source and execution hashes are retained in the native receipts.

The original sampler had coordinate-zero and prefilled-pair teaching gaps.
Required opposite-boundary examples and a matching pair in a winning object
repair both within the existing three demonstrations. Exact failed original
lessons and executable rivals are retained privately; early audit/test records
are explicitly superseded. Both repaired rivals are refuted by demonstration
zero for every audited setting and seed. Sampler regressions also cover seed
`2**63-1`; these additional Python checks are not another protected label census.

Core completed areas are `[3,3,4,4,4,4]`, then five ones/six twos/two threes,
then `[5,5,5,5,6,6]`. These teach merging, same-color separation, ties, area
versus bounding box, four versus eight connectivity, and color-sensitive
components. Additional demonstrations include a hollow shape, three colors
and further prefilled partners. Query sizes are 14, 24, 28 and 30; the 30-square
input contains 126 occupied cells and completes to 198. The grammar consists of
finite constructive templates with varied colors, size, orientation and scale.
It does not enumerate arbitrary shapes or prove universal learnability.
