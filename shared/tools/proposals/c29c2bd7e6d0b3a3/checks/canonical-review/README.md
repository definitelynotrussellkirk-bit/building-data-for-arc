# Selected-source canonical and shortcut review

This directory reviews only generator `7a37505e7bd0`. It is not either later
random audit. No generator, task test, note, shared source, authority file or
review contract was edited by this reviewer.

## Retained successful evidence

- `question-answer.json`: direct answer to `generator-shortcuts` with the exact
  generated witness and source/rule bindings.
- `v3/evidence.json`: eight canonical and 180 generated pairs, each labelled by
  the real Racket reference and two executable Racket rivals. It includes the
  exact witness grids and outputs, plus generator and runtime identity.
- `v3/command.json`: argv, cwd, actual return code 0 and elapsed time.
- `public-apply.json` and `public-apply.command.json`: independent supported
  CLI execution of the two exact witness grids, with domain checks, output
  hashes and return code 0.
- `probe.py`: reusable selected-source analysis.
- `run_probe.py`: runtime preparation and process receipt wrapper.

The reviewed production source is
`9e1b827924f2445dc0f57d593c04b3bb55dc0a47649ef03c276648df90d980d3`.
The canonical rule hash is `f6f5abe21d6a`; the full canonical program-source hash
reported by the probe is
`f6f5abe21d6af7df82edda25fe3ed35b0650f04da3b55520274de3c5ced6f3c2`.
The public apply receipt separately preserves its runtime rule-text hash.

## Findings

The natural canonical-fitting rival is **count only nonzero colors, then
nearest-neighbor upscale by that count (identity for a count of one)**.
It fits all eight canonical labelled pairs because no canonical input contains
zero. The proposed generator already refutes it. Calling
`generate(0, 1, difficulty="medium")` returns
`[[5,0,5],[0,0,0],[5,5,0]]`: the true output is 6 by 6 and the rival predicts the
unchanged 3 by 3 input. Both outputs were executed using Racket. In the bounded
sample of 12 seeds, five positions and three bands, 72 of 180 generated pairs
refute this rival.

There is a separate, bounded generated-teaching limitation. All current
templates make the rival **identity if monochrome, otherwise scale by
7 minus the largest color frequency** correct. It matched 180 of 180 generated
Racket labels. This follows directly from the fixed modal-frequency sequence
9, 5, 4, 3, 2 for counts 1 through 5; rotations, shuffles and palette changes
preserve those frequencies. Canonical train pair 0 has profile `[3,3,3]`, so its
true factor is 3 and this rival incorrectly selects 4. The Racket outputs are
9 by 9 and 12 by 12. This rival is **not** an answer to the canonical-fitting
question and is **not** evidence of a wrong emitted label. It is concrete
evidence that generated lessons omit one type of canonical disambiguation.

If broader teaching coverage is desired, one small option is to occasionally
emit the already self-check-legal two-color histogram `[3,6]`, for example a
palette substitution of labels `[[0,0,1],[0,0,1],[0,1,0]]`. This preserves the
existing shape, count and special-color rules while breaking the specific
7-minus-mode rival. That proposed change was not implemented or battery-tested.
It should remain a deliberate distribution decision rather than an implied
requirement to defeat every possible arithmetic rival.

Zero presence is exactly correlated with even counts 2 and 4 in the current
generator. This is declared and confirmed by the bounded sample: 36 inputs at
each scale, with zero present in all count-2/count-4 inputs and absent in all
count-1/count-3/count-5 inputs. It is a documented restriction, not a demonstrated
labeling defect.

Every canonical input passed current `self_check`, and every canonical output
agreed with both the real Racket reference and the Python mirror. The current
focused test materializes six pairs for query rotation, leaving five demos;
the notes' phrase “five materialized pairs become four demos” should instead
refer to a unique held-out scale leaving four distinct scales among five demos.

## Reproduction from the outer packet

Use a new output path on each run:

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  ../checks/canonical-review/run_probe.py --repo . \
  --out ../checks/canonical-review/replay

WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles \
  apply 7a37505e7bd0 --input ../checks/canonical-review/witness-inputs.json \
  --check-generator-domain --out ../checks/canonical-review/replay-apply.json
```

`run_probe.py` stages the selected generator plus the ordinary shared runtime
through `prepare_runtime`, then runs the probe in a fresh subprocess. The
standard runtime includes the full canonical ledger, with the selected task's
base authority and generator. The current helper uses a temporary directory
outside `WORK/checks` and removes that copied runtime after retaining its
complete manifest, probe outputs and process receipt.

The runtime copies used by `v3` and the initial successful replay were moved
outside `WORK/checks` at the parent's packaging request. Their original command
paths and cwd are preserved in the receipts. `omitted-runtime-locations.json`
records both relocated paths and verified manifest hashes. The retained
manifests are `v3/runtime-manifest.json` and `replay/RUNTIME_MANIFEST.json`.
No unique evidence was deleted; those trees can also be rebuilt with the helper.

## Earlier probe failures

`initial/command.json`, `v1/command.json` and `v2/command.json` record return code
1 from probe setup problems: attempting `wrap_rule` directly from the library
without its staged `scripts` namespace; invoking a staged bridge without the
packet's Racket environment; and mistakenly calling the bridge's
`runtime_identity` property. The corrected `v3` run through the packet wrapper
returned 0. These were probe/infrastructure failures, not generator defects.
