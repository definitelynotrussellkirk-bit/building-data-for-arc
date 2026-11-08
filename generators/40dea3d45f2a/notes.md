# Review implementation notes

Assignment `review-f8c4bee5b563cbd7`; selected baseline SHA-256 `66a5167f7c5d62e2494f579ab3c261f0aa06e24b0ed246390b47c1c7ed8f9c68`.
Version 3.0.0 source SHA-256 `9649550c6f0ad8b424d534135c625ae9469c86ad2f7c9b9ac24f28c6a7fdb1d1`. Canonical and selected Racket source unchanged.

The baseline uniquely sized every shape class, so count equality fit 1,800/1,800 sampled draws. It also rejected lawful equal-area negatives, clamped one class to two, and ignored palette controls. Prior review entries were leads; all reported measurements were rerun.

The repair samples free connected polyominoes fitting 4×4 and chooses class representatives by D4 identity. One of every three consecutive default draws uses two inequivalent shapes of equal size and extent, including a reflection-only positive. The other slots cover every equivalence relation on four panels. Panel order, orientation, position and colors vary independently of class identity.

The declared input domain requires four nonempty panels and zero separators. Ordinary samples are connected/monochrome and 3–8 cells, but self_check permits other nonempty masks consistent with the rule. All-equivalent is lawful; the output codomain has 15 possibilities, and low output uniqueness is not itself a defect. Fixed geometry is intrinsic, not a lack of a size axis.

All advertised controls are literal integers, exact, observable, and recorded via public named GenCtx draws. Unknown and removed decorative controls raise. Pinned overrides such as one class need not refute default lesson rivals; do not extrapolate the default guarantee to a restricted override domain or to a materializer that drops teaching samples.

Evidence in the matching review return: final battery 12/12, focused/portable 26/26, 4,140 accepted override draws, 900 local overlapping windows, and 300 public Racket episodes with zero declared-rival survivors, rejected inputs, or oracle disagreements. The local count-only accuracy drops to 432/1,800, but complete-lesson evidence is the primary measure. No Qwen capability or training gain was measured.

Tools and tests are in workspace/ and tests/. Root review reports contain the failure history, two read-only audits, exact command ledger, and fresh-patch replay. Approval remains a maintainer decision.
## Current reviewer considerations

Source SHA-256: `9649550c6f0ad8b424d534135c625ae9469c86ad2f7c9b9ac24f28c6a7fdb1d1`.

# Decisions for 40dea3d45f2a

## R1: choose shapes by D4 equivalence, not by a numeric proxy

The baseline used one distinct size (3–7 cells) for each class. Its original author rationale is not documented; avoiding accidentally equal shapes is a plausible interpretation, not an established fact. That construction made equality of cell counts sufficient and rejected exactly the hard negatives the task needs. Prior retained reviews `review-5994a478cf362114:v0001/v0002` and `review-ebc59a58d86f75c1:v0001` were leads only. All counts in this return were remeasured against the pinned source, not copied from those reviews.

I replaced the size proxy with a finite constructive bank of connected shapes fitting 4×4, canonicalized under eight square symmetries. Distinct representatives cannot accidentally merge under D4. Growing all bounded shapes is preferable here to random walks with retry caps: it avoids clipped shapes, seed-dependent failures, and silently reduced class counts. Normalized coordinates and sorted banks remove hash-seed iteration dependence. Rejected alternative: merely add random equal-area draws without ensuring their presence in complete lessons.

## R1: guarantee evidence in three-demo lessons

Exactly one of every three consecutive default sample indices is a teaching profile, selected by `(seed + sample_index) % 3`. It uses two inequivalent shapes with equal area and equal bounding-box dimensions, one chiral shape appearing in reflection-related orientations, and class-independent colors. Thus a single teaching input refutes five named rivals. Shuffling all four panels prevents the output partition from being tied to a fixed panel order.

The remaining slots sample all 15 equivalence relations, including one class and all distinct. A wholly adversarial sampler would overrepresent 2+2 partitions and become another template; the broad component avoids that restriction. A wholly independent random lesson sampler can omit its only decisive example. The lesson guarantee assumes consecutive accepted indices and no constraints that remove the witnesses; the actual Racket materializer retained all indices without rejection in the 300-episode probe. Artificial override domains such as all-equivalent shapes legitimately do not carry the full default teaching promise.

## Shapes, bands, placement, and colors

The 9×9 grid, separator at row/column 4, four 4×4 panels, and 4×4 output are intrinsic to this selected rule and canonical task. Enlarging the canvas would require changing the rule's geometry, so I did not add fake size diversity. Ordinary shapes are connected and monochrome, with 3–8 cells. Easy broad sizes are 3–5 and teaching sizes 4–5; medium broad 4–7 and teaching 5–7; hard broad 5–8 and teaching 6–8. D4 transforms and arbitrary fitting translations apply in every band. Color values are sampled from 1–9, with exactly 1–4 foreground colors; the output's 8 remains a rule-defined relation marker.

This distribution is not exhaustive over disconnected, multicolor, singleton, large dense, or empty panel shapes. Its finite support is intentional and explicitly documented. Self-check is broader than ordinary sampling: nonempty disconnected and multicolored masks remain valid because the actual rule ignores color and operates on nonzero panel masks.

## R2: domain validation is not an output-diversity test

The old equal-count rejection was removed. A line and an L with three cells are both admissible and inequivalent; the retained witness gives a 2+2 matrix, not solid 8. One class is also lawful and produces solid 8; I restored it rather than suppressing a correct answer to satisfy a generic diversity heuristic. `EXPECTED_OUTPUT_CODOMAIN=15` and the named solid-output justification explain the finite output domain.

The first repair accepted empty panels because the total Racket function can evaluate them. That was broader than this task's documented four-visible-shape domain, and the generic mutation test exposed the mismatch. I added a failing nonempty-panel test, then required all four panels to contain foreground. I did not reject color permutations or other lawful mutations simply to inflate mutation-rejection statistics.

## R2/R3: observable, exact controls only

The supported exact axes are `grid_h=9`, `grid_w=9`, `n_classes=1..4`, and `palette_size=1..4`. Every pair of class/palette counts is constructive. Observers recover their actual values from the returned grid. Removed texture, palette-kind, and redundant color-count knobs had no honest realized semantics; unknown/removed keys now raise instead of silently being ignored. This is an intentional override-interface tightening, not backward-compatible acceptance of decorative knobs.

Type and range validation precedes named public GenCtx draws. Fixed-range keyed draws record actual derived curriculum values, including dimensions. The provenance regression failed before this final fix and passes afterward. Rejected alternative: overwrite the context's private stores or record an axis value different from the grid's actual class/palette count.

## Testing and independent checks

Production generation supplies inputs only; canonical Racket supplies labels. `workspace/probe.py` uses cropped binary arrays and matrix rotations, independently of the generator's coordinate-orbit representation. It tests all three cyclic starts and distinguishes a rival surviving demos from that rival also failing a query. `workspace/lesson_probe.py` checks the public Racket materializer, dynamically reads the generator's actual declared rivals, records rejections/indices, and treats an absent contract as an error. Neither probe measures Qwen accuracy or proves universal identifiability.

The older baseline census returned exit 0 with empty declaration dictionaries; its report remains useful for the explicit count-only statistic, not as a semantic certificate. The public probe has a regression test against that vacuous-pass failure. All real failures, both solve exposure declarations, and the original and final solve notes are retained.

## Scope and authority

Only selected task source, notes, summary, workspace, and tests are patched. The two audits are evidence only. Canonical and selected Racket bytes are unchanged. Root-suite results are auxiliary because that run crossed the final provenance edit; acceptance instead uses the final-source battery, portable tests, public lessons, and exact-patch fresh-copy test replay.
