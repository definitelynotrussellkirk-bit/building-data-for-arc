# ticket-51e85f54bac307ad — completed witness

## Outcome

One lawful, directly generated `overlap_priority` scene refutes the plausible
shortcut “apply the correct bounding-box intersections with the lower numeric
color winning overlaps.” The canonical Racket output agrees exactly with the
generator's Python mirror. The rival differs at precisely the 16 overlapping
cells. This completes the witness ticket; it is not a new generator safety
finding and does not provide a general safety clearance.

## Bound identity

- Task and rule task: `3a4b67ab16ff`.
- Generator: `repo/generators/3a4b67ab16ff/generator.py`.
- Generator SHA-256: `abd406bd9626d25aba8dc67db0971b3722302a2959e2b6453dcbba2cfb431b7f`.
- Canonical record: `repo/shared/data/base/solutions/training/1c02dbbe__3a4b67ab16ff.json`.
- Record SHA-256: `b79eb6167e7c04591af80f7031f95dcb9f35ed183570e8449ef58f055afe9e6a`.
- Rule hash: `32c694357bd0`.
- Raw and whitespace-normalized program SHA-256: `32c694357bd0cf193ee8522752d4e50538cd8c33aff87788d1f1300070ae64b6`.
- Ticket seed: `4b76b33b814a3412ad779c3a4fee1171f5450fdddd5de0fedd3b35e5aa361255`, converted directly from hexadecimal to an integer.

The probe checks the pinned source and rule before importing or executing the
target. `probe.json` also records hashes of the exact executed probe and retained
witness.

## Single bounded probe

The sole generator call used `sample_index=0`, `difficulty="medium"`, and
`scene_profile="overlap_priority"`. It returned a 21-row, 20-column grid. The
generator's `self_check` returned no errors, and `observe_overrides` recovered the
requested profile. No generator or repository source was edited.

The rival independently calculates all-occurrence bounding boxes and their
intersections with the gray bounding rectangle. Its only semantic deviation is
descending color application. Canonical execution uses the existing
`strip_line_comments`, `strip_rule_wrapper`, and `RacketBridge`, with one
persistent bridge and one application of the pinned rule to the witness.

All bounds below are inclusive and zero-indexed:

| Region | Rows | Columns |
|---|---|---|
| Gray bounding rectangle | 4–17 | 4–16 |
| Color 2 bounding box | 5–12 | 5–12 |
| Color 4 bounding box | 9–16 | 9–15 |
| Overlap | 9–12 | 9–12 |

The canonical rule fills the overlap with color 4; the rival uses color 2.
The two outputs agree everywhere else. The evidence contains the complete input,
both outputs, generation arguments, validity result, and differing coordinates.

The command exited **0**. Measured probe time was **5.535660 seconds**, below the
120-second limit. The script reports eight successful behavior/structure checks,
in addition to the two pinned-identity assertions. Total ticket elapsed time is
left `null`; the measured probe duration is recorded separately.

Executed from `WORK/`:

```bash
PYTHONDONTWRITEBYTECODE=1 RACKET_PATH=/workspace/scratch/b11d575b87ec/arc_review/WORK/.review/racket-runtime/racket/bin/racket timeout 120s python3 checks/tickets/ticket-51e85f54bac307ad/probe.py
```

## Scope and disposition

Exactly one targeted probe was executed. There was no seed sweep, peer battery,
census, or model job. This witness demonstrates that the selected generated
example distinguishes the chosen rival; it does not measure the rival's frequency
of success or establish comprehensive teaching coverage.

The source already retains a separate, same-source endpoint-bounding-box audit
in `repo/generators/3a4b67ab16ff/evidence/review_index.json`. That audit was read for
context and was neither reproduced nor resolved by this different priority
witness. Its state is unchanged. No new `AUDIT.md` section is warranted for this
ticket result.

Retained files: `probe.py`, `probe.json`, `witness.json`, and this report.
