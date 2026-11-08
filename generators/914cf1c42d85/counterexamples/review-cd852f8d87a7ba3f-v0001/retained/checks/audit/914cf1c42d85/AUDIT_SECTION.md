## 914cf1c42d85

**Reproduced ordinary-domain defect; audited source left unchanged.** Source SHA-256: `b3a4fbc6838bc051b5f6524f67d86820af3b079e87751acd2c854bc26a9e550d`.

The generator promises three body components with distinct sizes `{1,2,4}`, but placement can silently drop the four-cell component when its 80 attempts run out (`generator.py`, lines 141–149). `self_check` accepts the resulting scene because it only requires some legend and some body cells (lines 83–87). This is an ordinary draw without a degenerate texture: seed `0`, sample index `0`, difficulty `None`, overrides `{}`. The fresh reproduction has three legend entries `[5,4,6]`, only body sizes `[1,2]`, and validator result `[]`:

```json
[[5,0,4,0,6,0,0],
 [0,0,0,0,0,0,0],
 [3,0,0,0,0,1,1],
 [0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0],
 [0,0,0,0,0,0,0]]
```

A task-local Python census of seeds `0..999` inclusive, sample index `0`, no overrides, found missing-size-four scenes in **299/1000 default**, **544/1000 easy**, **299/1000 medium**, and **60/1000 hard** draws. All 4000 draws completed and all 4000 returned validator `[]`. The default and medium slices use the same generation branch and are not independent populations. These finite seed counts describe the tested slice, not a distribution-wide estimate.

The canonical three pairs all have sizes `[1,2,4]`. Both the executable size-rank interpretation and the natural endpoint interpretation “smallest gets the first palette color, medium the second, largest the third” reproduce all three canonical outputs. On the malformed ordinary draw, the executed canonical Racket rank loop paints the domino `4`; the endpoint rival paints it `6`. `rival_output.json` records that rival's complete grid. This illustrates why the three-component precondition matters; it is a domain/coverage defect, **not a demonstrated reference-label error**. A fixed lookup for areas `{1,2,4}` also agrees with every canonical pair, so that alone is not claimed as a meaningful separate defect.

Evidence is limited to `WORK/checks/audit/914cf1c42d85/`: `input.json`, `finding.json`, `rival_output.json`, `census.json`, `probe.py`, `probe.stdout.txt`, `racket.json`, and `apply.log`. Supported canonical Racket execution exited `0` with `valid_output: true`, no error, executed/catalog rule hash `cf323707b9f5`, and rule-text SHA-256 `c6c5c016ad64fbb78bd34ff6181fc78b2cbc60b0a9f09ee6e4f0ce0abfb87f2b`. Its exact input equals the retained witness, and its output equals the Python mirror and differs from the endpoint rival. The output has singleton `5` and domino `4`, with row 0 cleared. Input hash: `abe270a019f0554f6e853195748bb701f74bc728033754cec1b51247f97a6bc4`; output hash: `9fe2b71b5d8360e541b7a57392f7c07fa3373ae998d9c5afad34b05be93546b7`. `finding.json` records the receipt digest and comparisons. Execution on this malformed scene does not repair the three-component contract or establish a label bug.

Reproduce from the outer review directory:

```sh
WORK/.venv/bin/python review.py run "$PWD/WORK/.venv/bin/python" "$PWD/WORK/checks/audit/914cf1c42d85/probe.py"
```

Supported apply command (from the outer review directory):

```sh
WORK/.venv/bin/python review.py run "$PWD/WORK/.venv/bin/python" -m arcpuzzles apply 914cf1c42d85 --input ../checks/audit/914cf1c42d85/input.json --out ../checks/audit/914cf1c42d85/racket.json
```

The final retained probe exited `0` with 4000 draws and six canonical output comparisons (three rank-mirror, three endpoint-rival). An initial exploratory probe independently checked the same 4000-draw slice and exited `0`; its duplicate grid copies were replaced by the single retained witness. The supported apply command also exited `0`; a receipt consistency check exited `0`. No full audit battery, training run, or target modification was performed. Repair lead: retry/backtrack the complete placement or fail visibly unless all required sizes were placed, and make validation enforce the three-body-size precondition.
