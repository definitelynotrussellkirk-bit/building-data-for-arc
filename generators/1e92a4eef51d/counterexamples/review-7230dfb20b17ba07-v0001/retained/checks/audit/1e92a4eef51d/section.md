## 1e92a4eef51d

**Issue found — A2-1e92-1: generated body palettes make the corner key redundant.** This is a findings-only audit of version `2.0.0`, generator SHA-256 `f1ed850f3f0edf2de4ca7b40493df62a055a4fd45ff580fc67c5ec0f89968e7c`. No audited source or authority was edited. The selected rule hash is `bf7a0a12ef08`; exact canonical program SHA-256 is `04ac1a77166dc162f01bbd2b0e14b91b4fc4fd9b7cee8df568ec87c2e2b6ebf2`. Public Racket application records the converted callable SHA-256 `b4893ae1855a2800483c76f1714496589c3aae5069f77533a473aaf4ca115b72`. The two text hashes identify different representations of the same selected authority.

### Reproduced shortcut

The intended rule reads the corner key, removes it, crops the remaining object, then reflects horizontally for key `1` or vertically for key `2`. In the current source, `_body_palette` always includes body colour `2` for key `1`, always includes body colour `1` for key `2`, and excludes the active key colour. The other controls do not remove this mandatory palette anchor.

Consequently, **“reflect horizontally if the body contains colour 2, otherwise vertically”** ignores the key and predicts every generated output. This support-wide conclusion follows from the unconditional construction in the exact audited source; it is not an exhaustive enumeration of seeds. The simple rival matches **3/4 canonical labeled pairs**, so it is not itself a canonical shortcut.

A compact composite rival also ignores the key: **body contains 2 → horizontal; otherwise body contains 1 → vertical; otherwise use canvas aspect (landscape → horizontal, portrait/square → vertical).** This `body_palette_then_canvas_axis` rival matches **4/4 usable canonical pairs** and **48/48 generated Racket comparisons**. Its fallback is explicit; this audit does not claim it is the globally simplest competing rule.

### Exact evidence and scope

- `checks/audit/1e92a4eef51d/finding.json` binds the finding to the assigned source and includes every comparison, current declared-rival result, and schedule verdict.
- `checks/audit/1e92a4eef51d/racket.json` contains **54 independent public apply results over 34 unique inputs**: 48 generated draw records, four canonical pairs, and two counterfactual inputs. Every result matches the diagnostic Python mirror, and all 54 inputs pass the selected validator. Repeated inputs are counted as repeated comparisons, not new input diversity.
- Generated Racket inputs cover `easy`, `medium`, and `hard`, seeds `0..1`, and sample indices `0..7`: **3 × 2 × 8 = 48 draw records**. `input_index.json` records every seed, index, band, and input role; `input.json` and `rival.json` retain the grids and rival outputs.
- `diagnostic-survey.json` separately records **640 Python-only diagnostic draws over 424 unique inputs**: four bands (`None`, easy, medium, hard) × seeds `0..3` × indices `0..15` = 256 default draws; plus 384 exact-control combinations covering both keys, sizes `4..7`, body-colour counts `1..3`, component counts `1..2`, and both aspect relations at seed `17`, index `7`, in all four bands. These are not reported as 640 Racket labels.
- The public production materializer at **hard, seed 0, requested index 0**, accepts indices **[0,1,2,3]** with zero rejections. Both new rivals fit its three demonstrations and query; independent public apply outputs match all four production labels. The existing `lesson_identifiable` hook returns `[]`. See `production.jsonl`.
- All four cyclic starts in each of three bands at seed `0` were checked using the retained authoritative labels: **12 overlapping windows, 48 held-out query roles, 11 unique inputs**. The composite rival fits every demonstration and query, while all declared hooks return no errors. This is persistent shortcut support, **not** a demonstration-fit/query-disagreement finding. Existing fixed-axis and aspect rivals are correctly refuted in the production example; their success does not cover the new palette rival.

### Counterexample the sampler cannot supply

The last two entries of `input.json` (zero-based indices **52 and 53**) have the same canvas and monochrome colour-3 body; only `(0,0)` changes from key `1` to key `2`. Both pass `self_check`. The body crop is `[[3,3,3],[3,0,0]]`; Racket returns `[[3,3,3],[0,0,3]]` for key `1` and `[[3,0,0],[3,3,3]]` for key `2`. The composite key-ignoring rival predicts the horizontal result for both and therefore fails the key-2 input.

These are **validator-domain counterexamples, outside the current generated support**, because their body lacks the mandatory colour-1/2 anchor. They show a valid distinction the present sampler cannot teach. They do not establish a wrong generated Racket label.

### Suggested follow-up and reproducibility

Decouple the body palette from the key while retaining canonical colour support. Include paired examples with the same body and canvas under both keys, using body colours outside `{1,2}`, and schedule enough of these examples to teach key dependence. Add the composite rival and a genuine refutation witness to the semantic contract; merely declaring it as a lesson competitor cannot expose it while every generated query also agrees with it. Preserve the selected Racket rule.

`checks/audit/1e92a4eef51d/probe.py` is a reusable, source-bound `prepare`/`verify` probe. `commands.json` records the four actual verification commands, working directories, exit code `0` for each, and retained evidence paths. Source and rule snapshots are included. No probe run failed, no full battery or audit task-test stage was run, and no fix or universal induction claim is made. This new palette finding concerns the current source; it does not retract the earlier scoped resolution of dead-control and fixed-axis teaching issues.
