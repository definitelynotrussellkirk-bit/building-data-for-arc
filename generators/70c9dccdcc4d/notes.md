# Working notes: 70c9dccdcc4d

## Selected generator and exact axes

The canonical source origin is color **2**, with the color-3 and color-4 arms
defining its two axes. Target origin 5 and arms 6/7 define the destination.
Only source-local color-8 points within Chebyshev radius 3 are reflected by
swapping local coordinates. The selected sampler keeps every mark in this
radius and reserves a distinct blank, in-bounds reflected destination.

The three advertised axes previously had no effect: seed 17, sample 3 with
`grid_h=9, grid_w=12, n_marks=1` returned a 12×16 grid with five marks. They now
set exact observable dimensions/count, with integer domains `9..18`, `12..24`,
and `1..6`, respectively. The shared strict draw validates and records explicit
pins. Pins override difficulty; `None` retains the existing default behavior.
Unknown keys, booleans, floats, strings and out-of-range values fail visibly.
The placement loop also refuses a short marker count instead of returning it.

Default layout draws are still consumed in their original order. `VERSION`
remains `1.2.0` because the unpinned seed stream is preserved; the source SHA
changes to bind the repaired pin behavior. The canonical rule, normalized
`RULE_HASH=06513d532f1c`, and base authorities are unchanged. Summary prose now
agrees with the actual source-corner color and difficulty bands.

## Focused verification

`tests/test_axis_contract.py` reproduced **33 failures / 1 pass** on source
`97603e47d5c8498bedc8b79d9e5d5e0974d4aa6338c274d0f0fa0a8ecce8c781`;
the staged task test runner then passed **34/34** on source
`d4d476d5da10cd22b82a61a8f5e5db425abc6b8a954e4c683a8b344212e8a667`.

`workspace/verify_axes.py` is a reproducible, source-bound check for later
agents. It retained 32 unpinned before/after fingerprints, all unchanged, and
exercised two bounded edge surfaces: all 32 combinations of axis endpoints
and difficulty bands; and all 64 source/target orientation pairs on 9×12
grids with six marks (found within 241 deterministic draws). Independent
coordinate calculations matched actual canonical Racket outputs for those
96 generated inputs and all three canonical pairs, **99/99** total. The
adversarial/parity probe completed in 7.395 seconds. Evidence and exact command
receipts: `checks/70c9dccdcc4d/{before,defaults-before,task-tests,edges-after}/`
in the review return. The executed normalized rule is `06513d532f1c`; its
callable text SHA is `ea11f4252c354f92b4450da85b4c05c2c73f245732b09d604c5d2d250f80c8d2`.

This is a focused repair of existing controls, not a complete learnability or
all-seed certification. Full batteries and unrelated tests were not run.
The sampler still emits only near-source marks, so it does not demonstrate
the rule's radius cutoff with distant distractors. The existing `self_check`
is intended for this generated subset and was not expanded into a strict
validator of arbitrary ARC grids or the full canonical domain.

## Pending source-bound repair

A previously retained repair proposes six axes and radius/transpose teaching
witnesses. It remains unselected because source packet
`1a7aa457628d3113328f40f429862b00b963f84fddffaf8fbb95a135dbaee7b6` is unavailable.
Its original [proposal](workspace/proposals/ef84ba81213c8af96746596d221a57f855143a1edd54eff4d74b944f86c890d3.json)
and supporting files are not shipped in this packet, and there is no shipped
`evidence/review_index.json` for this task. The current three-axis repair was
derived and verified independently; it does not select or validate that
broader proposal. Its reported 97 tests, 300 lessons and 900 rotations remain
unverified here. Next work on the broader proposal requires recovering its
source-bound assets or independently constructing its teaching witnesses.
