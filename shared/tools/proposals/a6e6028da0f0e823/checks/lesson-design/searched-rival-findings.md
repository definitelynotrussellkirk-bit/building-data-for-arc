# Bounded searched-rival findings: b1972482cb43

## Release conclusion and scope

**The release census passes its declared-rival checks while retaining advisory spatial ambiguities: 27 scores each for first/topmost and 26 for reversed ties.** The spatial input-only realizations fit **0/3 canonical labels**. The separately discovered, canonical-fitting left-half-plane defect is refuted throughout this release census. These are bounded statements about the saved support.

This extraction is bound to generator `5de19b883ae5a9875abc09824ca005cdae155d345506898b60b2f0df382bf76d`, [the saved census](../lesson-census-release.json.gz), uncompressed SHA-256 `56f8c49c1c36a7479c0d126a91aca40dc959789e20ef997318fb189f0c49dd58`, and stored-file SHA-256 `1db52fa275009e1c2d45e7540820e8e9b5bcd18f0f1330166dc97bc679127d4a`. The extractor verifies the summary and compression manifest, diagnostic helper hash, all **1500 saved Racket-labeled pair occurrences / 1469 distinct inputs**, and every reported search count. This analysis uses saved authoritative labels; it does not generate or relabel inputs.

## What the generic diagnostics measure

[`review_diagnostics.py`](../../repo/shared/runtime/review_diagnostics.py), in `_generic_candidates`, builds a lookup from the current lesson's inputs to **known Racket outputs**. `objects` enumerates monochrome four-connected nonzero components in row/column order, including the singleton 9-anchor.

For each changed output cell, the three spatial candidates compute Manhattan distance to each input component and keep the change only when its nearest owner is component 0. Otherwise they restore the original input value. `first_object_only` and `topmost_object_only` run exactly the same branch. `reverse_position_tie` changes only the winner of equal-distance ties. These measured label mutations cannot predict unseen inputs without another rule providing the output.

There is nevertheless an executable input-only interpretation: compute point reflection from the input, then apply that same component-distance filter. The extractor implements it, using the helper's component enumeration, and verifies that it reproduces the actual measured mutations on every saved pair. Both tie variants fit **0/3 and 0/3 canonical labels**, respectively. They are residual positional restrictions admitted by some generated lessons, not additional canonical-fitting shortcuts. This establishes their behavior on measured support; it does not establish that they are natural or likely learned rules.

`search_lesson` reports **refuted** when any demonstration differs, **ambiguous** when all demonstrations agree but a query differs, and **support_equivalent** when both demonstrations and queries agree. Support equivalence is not refutation. `support_disagreements` counts differing pair predictions, not individual cells.

## Release production versus rotation counts

Entries below are **refuted / ambiguous / support-equivalent**.

| Spatial candidate | Production (300) | Rotations (1500) |
|---|---:|---:|
| `generic:first_object_only` | 294 / 5 / 1 | 1473 / 22 / 5 |
| `generic:topmost_object_only` | 294 / 5 / 1 | 1473 / 22 / 5 |
| `generic:reverse_position_tie` | 294 / 5 / 1 | 1474 / 21 / 5 |

The union of spatial ambiguity findings covers **22 distinct bundles and 22 distinct held-out queries**. Production queries are also scored in their query-index-4 rotations, so the five production findings are repeated there. First/topmost are aliases, and most reverse-tie findings overlap; adding their totals would overcount discoveries. The JSON retains every ambiguous recipe, the 1 score(s) where spatial candidates differ in ambiguity status, and every spatial support-equivalent recipe.

Support-disagreement totals are **5418** for first/topmost and **5448** for reversed ties, corresponding to 903 and 908 differing pair occurrences, each scored once in production and five times in rotations. `first_color_only` is support-equivalent in all 1800 scores because only the source color (smaller than marker 9) is added. `last_color_only`, `no_fill`, and `omit_last_changed_cell` are refuted in all 1800.

## Exact retained release lead

The first actual production finding is **easy, seed 2090446681, requested start 3, accepted samples [3, 4, 5, 6, 7]**, with query sample 7.

| Sample | Role | Component colors in order | Spatial alternative equals Racket label? |
|---:|---|---|---|
| 3 | demonstration | `[9, 7]` | yes |
| 4 | demonstration | `[9, 2]` | yes |
| 5 | demonstration | `[9, 2]` | yes |
| 6 | demonstration | `[9, 2]` | yes |
| 7 | query | `[4, 9]` | no |

The four demonstrations all agree; the query differs. The spatial mutation removes these required reflected cells: `[[3, 0], [4, 0], [4, 1]]`. The alternative equals the query input. The full labeled lesson, alternative outputs for both tie variants, exact seed/indices/input hashes, and all other leads are preserved in [searched-rival-findings-release.json](searched-rival-findings-release.json). This is a concrete remaining advisory ambiguity, not a label error.

## Exact left-half-plane rule on the release source

The input-only rival preserves the input and reflects only source cells with **`c <= anchor_c`**, including the anchor column, with normal clipping. The strict `<` variant does not fit all canonical labels. The measured `<=` rule fits **3/3 canonical labels**.

Independent rescoring of the saved release labels gives:

| Scope | Refuted | Ambiguous | Support-equivalent |
|---|---:|---:|---:|
| production | 300 | 0 | 0 |
| rotation | 1500 | 0 | 0 |

The repair therefore rejects this exact shortcut throughout the measured release lessons and all held-out rotations. This evidence remains finite; it does not claim exhaustive exclusion of arbitrary alternative programs.

## Retained d43 defect and repair evidence

The earlier source `d43f654ef0edf9295c6f1393ac5dfa885d27a1eda3025b1422bc1f39ee6505df` had **7 ambiguous production lessons and 53 ambiguous rotations** under the canonical-fitting left-half-plane solver, with 4 and 20 support-equivalent scores. These historical counts remain in [the original extraction](searched-rival-findings.json) and [the original report](searched-rival-findings-d43.md). Its three generic spatial candidates each had 4 production and 14 rotation ambiguities; those are not the release counts above.

The exact old Racket-labeled failure is [left_anchor_before.json](../../repo/generators/b1972482cb43/counterexamples/left_anchor_before.json): **easy, seed 2943442411, accepted samples 19–23**, with query 23 and agreement vector `[true, true, true, true, false]`. The generated-recipe regression [test_left_anchor_shortcut.py](../../repo/generators/b1972482cb43/tests/test_left_anchor_shortcut.py) failed on unchanged d43 (1 failed, 1 passed), then passed on the release source (2 passed). [Red](left-anchor-red.json) and [release green](left-anchor-green-release.json) receipts bind the exact commands, source, test, fixture, and logs. The old failure remains evidence for why the change was necessary; the current source is assessed by the release counts and receipts.

## Reproduction and retained scope

From `WORK/repo`, use fresh output paths (the extractor protects existing outputs):

```bash
python3 ../checks/lesson-design/extract_searched_rival_findings.py --census ../checks/lesson-census-release.json.gz --prior-findings ../checks/lesson-design/searched-rival-findings.json --out ../checks/lesson-design/searched-rival-findings-replay.json --markdown ../checks/lesson-design/searched-rival-findings-replay.md
```

The release JSON binds the source, rule, census, compression manifest, diagnostic helper, and extractor hashes. The original d43 extraction, report, and extractor copy remain available. Declared-rival success and the repaired canonical-fitting shortcut do not erase the separate measured spatial residuals described above.
