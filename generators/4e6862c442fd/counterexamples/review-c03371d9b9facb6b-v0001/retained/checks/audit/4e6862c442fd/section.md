## 4e6862c442fd

**Classification: issue found — distribution/teaching shortcut (important); no canonical output mismatch or validator rejection defect found in this bounded audit.** Target source and shared files were left unchanged.

**Source binding.** Selected generator SHA-256 `7dc70c5bd0b0658235b73b9802bccd54610f1dfcd1b6f848e878f1795f95828b`, version 3.0.0; pinned canonical rule hash `1e279b7f949b`. Exact investigated source is `checks/audit/4e6862c442fd/source.py`. Retained ledger program is `rule.rkt`, SHA-256 `1e279b7f949ba3cd76c27bfb555539629f8754507fc3c6b20264d70d860f2d30`. The public apply command executed canonical rule text SHA-256 `8acd44ea5179ff35ccb9c17e5f05f4a132c3d4b4eb01b5385eb87a159c43c521` under the same pinned rule hash.

**Finding.** Every default `_PROFILES` entry has `motif_id == relative_transform`. This binds each of the eight source-local motif shapes to exactly one global D4 transport transform. The seed-phased source basis changes do not break that relationship. A short catalogue-lookup rival can therefore ignore both target direction markers (colours 6 and 7), recognize the source-local motif, choose the D4 transform indexed by its catalogue ID, and paint around target origin colour 5. The intended target orientation is never read. The independent implementation is `motif_lookup_rival` in `probe.py`.

All **256** checked default calls matched this rival exactly: seeds 0..7, sample indices 0..7, and difficulty None/easy/medium/hard. More strongly, equality follows directly from the default construction: its selected target basis is obtained by applying the motif-indexed transform to its source basis. No ordinary default draw can contradict this rival; explicit independent motif/basis overrides can.

**Exact lawful generated counterexample.** `input.json` is reproduced by:

```python
generate(2, 0, source_basis=0, target_basis=0,
         motif_id=0, grid_h=12, grid_w=18)
```

Difficulty is None. Both source and target frames use basis 0, so the intended relative transform is identity (index 3), whereas the catalogue rival incorrectly applies transform 0. `self_check(input) == []`, `strict_canonical_like(input) == []`, and observed overrides equal every requested value. Thus the generator can emit this counterexample when explicitly requested; the default sampler cannot emit this motif/relative-transform combination.

The intended new colour-8 cells are `(7,6),(8,8),(10,5)` (zero-based). The rival instead adds `(8,9),(10,6),(11,8)`. All three rival additions are in bounds and background in the input; this is a clean transformation disagreement, not a clipping/collision artefact. Six output cells differ.

**Actual authority check.** The supported public `arcpuzzles apply` command was run with the included Racket runtime through `review.py run`, exiting 0. `racket.json` has no error, equals `mirror.json` exactly, and differs from `rival.json`. It records the selected source hash, executed rule hash, actual reference output, and domain check. Exact argv/cwd/exit records are in `command-records.json`.

**Concrete teaching gap.** `lesson.json` has three default demonstrations from seed 0, indices 0/1/2, followed by the exact lawful override query above. The catalogue rival fits all three demonstrations and disagrees with the query; existing `lesson_identifiable` returns `[]`, because this rival is undeclared. The demonstration labels in this diagnostic are Python-mirror labels; only the counterexample query was independently re-executed with Racket in this audit. That distinction is retained in `summary.json`.

**Canonical limitation — do not overstate the finding.** The three canonical pairs have `(motif_id, relative_transform)` values `(0,6),(1,7),(2,4)`. Their Python mirror matches all three labels, but the specific default-catalogue rival above matches **0/3 canonical pairs**. This is a generator-distribution shortcut, not a claim that this rival fits the original canonical demonstrations. The existing empty `CANONICAL_SHORTCUTS` declaration is not false on this evidence. Canonical examples already contradict this particular learned default association.

**Suggested next action.** Decouple default motif choice from relative frame transform, retain repeated identical motifs under differing target directions, and add a competitor that ignores target direction markers by learning the catalogue/transform correlation. Keep the exact override witness as a regression. Changes to the target are outside this findings-only audit and were not made.

**Evidence and limits.** `probe.py`, `probe.log`, `canonical-analysis.json`, `summary.json`, `input.json`, `mirror.json`, `rival.json`, `racket.json`, `lesson.json`, `source.py`, `rule.rkt`, and `command-records.json` are retained together under `checks/audit/4e6862c442fd/`. Current notes and review index were inspected; no existing audit was resolved or approval inferred. No full battery or inherited task-test preflight was rerun. The bounded probe establishes this exact confounding and accepted counterexample, not absence of other validator or teaching defects.
