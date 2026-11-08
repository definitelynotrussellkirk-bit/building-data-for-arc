## 87aae821984d

**A87-1 — Reproduced distribution shortcut: cyan bounding-box dimensions reveal the repeat count, so an ordinary generated lesson does not require counting yellow.** Findings-only audit; the audited generator, rule, catalog, and assignment are unchanged.

The audited version is `4.0.0`, generator SHA-256 `15a3c012540738dee4d3d31f9ffe68b8eebfcdfda23836b0cc4c3be0fd9b99b8`. The executed and catalog rule identifiers are both `6f52927247b0`; the executed Racket callable text SHA-256 is `49838c7b7cd2fc04b43bb26d610337662a5403755f9d12cd00d5819faee21e8e`. These identities come from the actual public `arcpuzzles apply` receipt at `checks/audit/87aae821984d/racket.json`, and agree with the current notes/review index.

### Finding and consequence

`_profile_defaults()` always couples the cyan tight bbox to the number of yellow cells on draws without overrides:

| Cyan bbox | Scheduled yellow count |
| --- | ---: |
| 3×3 | 1 |
| 2×3 | 2 |
| 3×2 | 3 |
| 2×2 | 4 |

The executable `bbox_count_rival()` in `checks/audit/87aae821984d/probe_bbox_count.py` never reads yellow cells. It bottom/right-aligns cyan in the correct 3×3 tile, but computes its repeat count as `1 + (3 - cyan_bbox_height) + 2 * (3 - cyan_bbox_width)`. This rule agrees with the selected authority on every default-profile combination by construction. The generator's six declared rivals do not include this confound, so their falsification does not show that a lesson teaches yellow counting.

This is a **generated-distribution shortcut**, not an incorrect Racket label and not a claim that the rival fits the original task. The new rival matches only **1/7 canonical pairs**; that limitation is retained in `summary.json`. Separately, the probe iterated the actual `CANONICAL_SHORTCUTS` declaration and verified the existing `left_align_narrow_motif` rival against **7/7 canonical pairs**, using freshly obtained Racket labels.

### Concrete generated counterexample

`checks/audit/87aae821984d/counterexample.json` contains the exact input, Racket output, rival output, source/rule hashes, and public-command provenance. It is produced by `generate(87002026, 0, difficulty="medium", n_4_cells=2)`, with no other overrides. It is **generated using a documented override**, not manually authored. `self_check` returns `[]`, and `observe_overrides` reports a 9×9 canvas, two yellow counters, and `shape_kind="span_3x3"`; therefore the input belongs to the current documented and executable generator domain.

Input: **9 rows × 9 columns**. Actual Racket output: **3 rows × 6 columns**. Rival output: **3 rows × 3 columns**. The Racket rule repeats the cyan tile twice because there are two yellow cells; the rival repeats once because the cyan bbox is 3×3. Three further generated overrides, one for each remaining bbox class, also pass `self_check` and distinguish the rival. Their settings and all outputs are retained in `cases-labelled.json`.

### Bounded checks actually run

All following counts are for the exact generator and rule hashes above. Default draws use seed **87002026**, sample indices **0–6 inclusive**, and each of `None`, `easy`, `medium`, and `hard`, with no overrides.

- **39/39 Racket applications** succeeded: 28 default draws, four generated override counterexamples, and seven canonical pairs. The Python mirror matched those authority outputs, and **39/39** inputs passed `self_check`.
- The new rival matched **28/28 default draws**, representing **15 unique inputs**. Repeated inputs across difficulty bands are counted explicitly; this is not a 28-unique-input claim. It disagreed on **4/4 override counterexamples**.
- Production lessons use **three demonstrations followed by a fourth consecutive query**. At the fixed seed, the probe enumerated every declared start residue **0, 1, 2, 3** separately in all four difficulty settings. These are **16 overlapping production windows**, not independent inputs. The declared contract accepted **16/16**, while the new rival fit all demonstrations and the query in **16/16**.
- Holding out each of the four pairs gave **64/64 query rotations** accepted by `lesson_identifiable`; the new rival survived and matched the query in **64/64**. The probe iterated the current `LESSON_COMPETITORS` mapping and retained each declared rival's refuting demonstration indices. Thus declared-rival production and rotation verdicts are **pass**, while production and rotation verdicts against the additional bbox-count rival are **fail to identify yellow counting**.
- Isolated public audit-phase task tests passed **38/38**, with no failures, errors, or skips. See `checks/audit/87aae821984d/task-tests/result.json` and `checks/task_tests.xml`; the actual isolated runtime directory is recorded as `/tmp/arcpuzzles-check-uurt97pw`. No full battery or shared semantic stage was run for this audit.

The measured sample is bounded to one seed. The stronger statement that ordinary draws preserve the count/bbox dependence follows directly from `_profile_defaults()` and the exact scheduled draws; it is a source-inspection conclusion, not a claim of an all-seed census.

### Recommended follow-up and evidence

Decouple repeat counts from cyan bbox classes in ordinary generation, while retaining the intended padding/connectivity lesson coverage. Add this rival to the lesson checks and require valid count-changing examples that break its predictions. The existing exact override support already supplies lawful witnesses, so the issue concerns ordinary sampling and lesson construction rather than the domain definition.

Exact outer commands, `packet_root` working directories, payload/runtime directories, exits, and retained evidence paths are in `checks/audit/87aae821984d/COMMANDS.json`. Reusable probe: `probe_bbox_count.py`; input batch: `input.json`; actual authority receipt: `racket.json`; minimal witness: `counterexample.json`; full source-bound comparisons and per-lesson evidence: `cases-labelled.json` and `summary.json`. The 38 passing task tests do not close this new shortcut finding.
