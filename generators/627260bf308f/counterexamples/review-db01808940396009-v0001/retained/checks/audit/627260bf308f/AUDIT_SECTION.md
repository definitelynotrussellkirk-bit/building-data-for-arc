## 627260bf308f

**Findings-only audit: reproduced validator defect A627-1. Audit target sources were not edited.**
Audited generator v3.0.0 SHA-256: `07ee110e1e46147138b48c2cac3c544ef628cb595a53bc5eb5955fcb58c89b1f`.
Canonical Racket text SHA-256: `088353dcd64fbbe56b9cb6ebae39e237c3fab42d17b988b8e6f64e674ce862d1`; normalized rule hash `088353dcd64f`.
The audit assignment pins those generator bytes. The current review index contains no earlier open audit; its acceptance record is reviewer-reported. This audit does not approve or modify the source.

### A627-1 — Both validators accept grids outside ARC dimensions

Starting from `generate(0, 0, difficulty="easy")`, add zero padding to make either the width or the height 31. The resulting grids are **9 rows × 31 columns** and **31 rows × 11 columns**. Palette entries, blank separator, component cardinality, distinct sizes and connectivity remain unchanged. Both `self_check` and `strict_canonical_like` return `[]` for both oversized inputs.

The selected canonical Racket rule was executed on both exact inputs. Its retained outputs have the same oversized dimensions; this confirms the reference execution without treating execution success as a lawful ARC-domain verdict. Both inputs are outside the advertised `grid_h`/`grid_w` sampler ranges and the ARC 30-cell dimension limit. No invalid size was observed among the generated cases below: this finding concerns the validator boundary, not a claim that default generation emits oversized grids.

Reproducer and full inputs/actual Racket outputs: `checks/audit/627260bf308f/probe.py`, `checks/audit/627260bf308f/counterexamples.json`. The latter binds generator/rule hashes, base seed/sample index, padding operation, command and working directory. The complete report is `checks/audit/627260bf308f/audit.json`. Suggested task-local fix: reject height or width above 30 before semantic validation, and add width-31/height-31 regression cases. No shared-runtime change is required.

### Checked scope and measured results

| Check | Actual scope | Result |
|---|---|---|
| Canonical rule replay | All 3 stored labeled canonical pairs | 3/3 matched |
| Default generation | Seeds 0–3, sample indices 0–5, easy/medium/hard | 72/72 valid; actual Racket outputs matched an independent component-rank calculation |
| Exact boundary controls | Seed 867, medium, indices 0 and 1; Cartesian product of height {8,24}, width {10,24}, count {2,3,4,5}, palette order {sorted,unsorted} | 64/64 valid; all four requested controls observed exactly; actual Racket outputs matched the independent calculation |
| Generated-input denominator | The 72 default plus 64 controlled calls | 136 calls, 97 distinct normalized input hashes; no claim of 136 independent inputs |
| Declared rival fit | All 7 actual `SEMANTIC_RIVALS` against 3 stored canonical pairs | Each rival fit 3/3 canonical pairs |
| Default witness draws | All 36 even-index default draws from the sample above | Every draw refuted all 7 declared rivals against actual Racket labels |
| Production lessons | 3 demonstrations + 1 query; overlapping windows starting at indices 0,1,2 for each of 4 seeds and 3 bands | 0 ambiguous lessons out of 36 against the 7 declared rivals |
| Query-role rotations | Hold out each pair from each of those same 36 lessons | 0 ambiguous rotations out of 144 against the same rivals |
| Malformed inputs | 14 empty, ragged, noninteger/color, short or cardinality-invalid examples | 14/14 rejected; no validator exceptions |

These are finite, source-bound checks. The 36 lessons overlap and reuse the 72 default draws; the 144 rotations reuse their existing Racket labels. They are not extra independent generation samples or all-seed proof, and no undeclared rival search or full battery was run in this audit. The direct shared `RacketBridge` avoided a copied runtime; it supplied all authoritative outputs. The independent Python calculation was only a comparison probe.

### A627-2 — Identity-type validation question

Six robustness probes were accepted without error: seeds `True`, `1.5`, and `"1"`; sample indices `True`, `1.5`, and `-1`. Their grids passed `self_check`. The public generator signature documents integer identities, while the task enforces strict integer types only for its explicit size/count overrides. The report retains the exact calls and input hashes under `invalid_identity_calls`. This is an API-hardening question for the maintainer, not evidence of an incorrect label for a supported integer call. Clarify whether task entry points must reject noninteger and negative identities; if so, validate them before schedule and RNG selection.

### Exact command and receipt

Working directory: `WORK/repo/`.

```bash
PYTHONDONTWRITEBYTECODE=1 TMPDIR=../.tmp ../.venv-review/bin/python ../run_with_racket.py ../.venv-review/bin/python ../checks/audit/627260bf308f/probe.py --repo . --out ../checks/audit/627260bf308f/audit.json > ../checks/audit/627260bf308f/probe.log 2>&1
```

Exit code: **0** (the audit probe completed and recorded findings; this is not a clean-domain verdict). Machine-readable command, source hashes, counts and evidence paths: `checks/audit/627260bf308f/command.json`. The probe refuses an existing report path; replay to a new `--out` filename. It verified that the audit generator bytes were unchanged after execution.
