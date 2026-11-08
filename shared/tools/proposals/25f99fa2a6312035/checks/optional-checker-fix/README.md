# Optional shared-checker proposal: recognize newly painted colors

**Status: implemented and tested as a passive proposal only.** The selected
`shared/tools/generator_defect_lint.py` remains unchanged. The task repair delta
must not apply this shared patch. A maintainer must review and implement a shared
checker change under the repository's proposal workflow before it becomes active
(`docs/placement.md`, “Generator notes and review retention”).

## The false positive

The transformation-drift detector currently compares palette additions:
`output_colors - input_colors`. It therefore misses a real recoloring when the
destination color already occurs elsewhere in the input. The repaired task's
rich samples deliberately contain an existing 8 to teach that it remains
passable and is preserved. Zeros still become 8 in qualifying chambers.

The unchanged full battery recorded this warning in
`checks/after-v1/checks/f48cc30d7943_after_defect_lint.log`: color 8 appears to be
introduced on only 18 of 60 generated pairs. The checker labels the finding
WARN, but `shared/tools/run_generator_battery.sh` invokes defect lint with
`--strict`; the stage consequently exits 1. This proposal does not waive that
failure or change the recorded battery result.

A small existing reference-checked example is:

```text
input:  [[2, 0, 8, 0, 2]]
output: [[2, 8, 8, 8, 2]]
```

The input palette is `{0, 2, 8}` and the output palette is `{2, 8}`, so no color
is newly introduced. Nevertheless, two original zeros become 8. The retained
public Racket apply result checked this exact input with executed rule hash
`8c735fdd2a75`. This five-cell witness is the small bridge already present in
the semantic evidence; it is not a claim of minimum possible grid size. It
lies outside the sampler's teaching grammar and is lawful under the Racket
rule. The detector reproduction repeats the pair six times only to satisfy
its minimum batch size; it does not claim six distinct generator draws.

`reference_fixture.json` retains that bridge, the four canonical training pairs,
and 18 generated pairs from `checks/semantic-final-v1`. Every input and output
was matched to the saved public Racket apply result. This fixture is explicitly
separate from the battery's original 60-pair sample.

The executed `reproduction-v2.json` comparison reports an original-checker
warning of 6/18 generated pairs. Every one of those 18 labelled pairs actually
paints new 8 cells. The patched checker reports no drift finding on this saved
batch or on the repeated bridge witness.

The earlier `reproduction-v1.json` is retained. Its recorded argument list
omitted the interpreter's `-B` flag; version 2 records `sys.orig_argv` and repeats
the same saved-pair comparison. This recorder correction does not change checker
code, labels, or the focused RED/GREEN evidence.

## Proposed change

`changed-destination-colors.patch` changes only two functions in the shared
checker. `_fingerprint` additionally records the destination colors of cells
whose values actually changed. For same-shape generated pairs,
`d_transformation_drift` counts those painted colors along with palette
additions. Preserving an old 8, erasing it, changing only to a different color,
or doing nothing does not satisfy this check.

The existing canonical calibration still requires a palette addition on every
canonical training pair. Size-changing pairs retain palette-only evidence
because the input and output positions do not have an established
correspondence. The sample threshold, size-relation detector, changed-fraction
detector, and the existing ANY-of-required-colors policy are unchanged. The
proposal contains no task IDs, palette constants, exceptions, waivers, or
alternate rule labels in the shared patch.

## Executed checks

The focused tests were written and run against the original checker before the
patch was created. They load the actual whole module through `importlib`, with
its `scripts` namespace bound to this library's own `shared/tools` directory.
There is no AST extraction, copied detector implementation, external checkout,
new generator draw, or new Racket call in this test harness.

| Run | Result | Evidence |
|---|---|---|
| Original checker, genuine RED | 28 test methods; 9 failing methods and 19 passing methods; 18 failure records including 10 color-renaming subcases; zero errors or skips; exit 1 | `red-original.command.json`, `red-original.result.json`, raw log |
| Patched single-file copy, GREEN | Same 28 methods and all 10 color-renaming subcases pass; zero failures, errors, or skips; exit 0 | `green-patched.command.json`, `green-patched.result.json`, raw log |
| Patch application | `git apply --check` and application both exit 0 on an isolated single-file copy; the resulting bytes equal the tested candidate | `patch-application.command.json` |

Each focused run makes 35 counted drift-detector calls over 221 supplied pair
instances, plus one direct purity check over six pairs and one fingerprint
check. Those counts include repeated synthetic cases and are not generator
sample or unique-pair counts. The tests cover no-ops, missing triggers, target
color counts that decrease or stay constant while new positions are painted,
all ten ARC colors, threshold boundaries, weak firing, incorrect size
relations, shrink/grow/reshape behavior, and the retained Racket-labelled cases.

No patched full battery or corpus-wide checker calibration was run. The passing
focused tests show that this specific false positive is corrected while the
covered warnings remain active. They do not prove that every possible checker
false positive or generator defect is addressed.

## Source identities

| Asset | SHA-256 |
|---|---|
| Unchanged authoritative checker | `cad291fddbdfa8a48557733a565ff2d0616cf4a5b336dd58988a26e65c9f21fa` |
| Tested patched copy | `85f361a21b1e45f51f1ef5846681673db93ac3700e4d42a1ad81e38e40874bdc` |
| Unified patch | `1339811ce3b23ff8d06967409c8af7c1447d63349f0983f051e8a6a5b714cb52` |
| Focused test script | `37b63007facf88b62cf51fcfd00cc1bbf30020166aaec455cfd24a06b88fd285` |
| Reference fixture | `0bcab4baf2f014171daf8225f5bb0933693c07624dbb7c08bda1a5b2adf4fbbf` |

## Replay

The scripts need Python 3.12+ and the explicit current library's source files;
they use only the standard library. From `WORK`, choose unused result names:

```bash
.venv/bin/python3 -B checks/optional-checker-fix/run_focused.py \
  --library repo \
  --source repo/shared/tools/generator_defect_lint.py \
  --name replay-original

.venv/bin/python3 -B checks/optional-checker-fix/run_focused.py \
  --library repo \
  --source checks/optional-checker-fix/patched/shared/tools/generator_defect_lint.py \
  --name replay-patched
```

To inspect the actual warning, saved labels, and independently counted changed
destinations without running the test assertions:

```bash
.venv/bin/python3 -B checks/optional-checker-fix/reproduce.py \
  --library repo \
  --source repo/shared/tools/generator_defect_lint.py \
  --source checks/optional-checker-fix/patched/shared/tools/generator_defect_lint.py \
  --out checks/optional-checker-fix/replay-comparison.json
```

Paths can be relocated by supplying a different `--library`, `--source`, and
`--out`. Tests and fixture can travel with the proposal. The default reference
fixture is resolved beside the script, not through a predecessor checkout.
