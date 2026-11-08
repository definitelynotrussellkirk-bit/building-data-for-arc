# Working notes: 7494855fa379

## Selected repair state

Version **3.2.0**, generator SHA-256 `e8a0b3d73133b90b1fb605adc877d638413533391b8994e9891355425403985f`. Racket authority is unchanged and pinned as `RULE_HASH=856baaecfaa1`: fill a zero center with 6 only when all eight surrounding cells are 4. Python mirrors and rival predictions are diagnostic.

Current controls are exact `grid_h` 4..18, `grid_w` 5..20, positive-ring `n_blocks` 1..6, and supported texture. Numeric controls override automatic curriculum texture selection unless a texture is explicitly requested. Unknown controls, strict-type violations, and unavailable supported combinations raise explicit `ValueError`; no count clipping. Removed `palette_kind`, `palette_size`, `n_distinct_colors`, `density`, and `position_bias` had no honest observable control. Fixed semantic colors 4 and 6 cannot be permuted.

Canonical singleton rings are valid in every difficulty. Canonical diagonal contacts require four-connectivity: component validation recognizes separate complete/occupied yellow rings, monochrome non-yellow hollow rings, and one-missing-corner yellow rings. A lawful no-action motif can stand alone. `solid_squares` and `center_already_filled` preserve dimensions and pass validation; blank `no_blocks` preserves dimensions as a negative fixture, fails validation, and is absent from advertised valid textures. Positive-count requests with a zero-positive fixture are incompatible.

Packing chooses spaced pitch-four motifs or alternating three-cell checkerboard positions, including diagonal contact. Supported capacity is constructive, not globally optimal. Exact 6×6/2, 6×9/3, and 9×9/5 layouts now have regression coverage. The generator deliberately does not sample arbitrary damaged shapes or the entire domain on which the Racket local predicate can execute.

## Current lesson decision

Declared period **2** alternates canonical-size core (5×7, 8×8, 9×9; one/two targets) and contrast (two targets plus missing-corner, non-yellow-ring, and occupied-center counterexamples). Three demonstrations and one query are intended. Finite tests cover both period starts, four seeds, four difficulty settings, the seven declared rivals, and all four single-query holdouts per four-pair lesson. Their labels come from an independent oracle checked against all three labeled canonical pairs. This is finite rival evidence, not universal identifiability; controlled overrides may opt out of the curriculum.

## Reversals retained

The imported 2.1.1 notes gave no current rationale; historical reasons beyond its clipping comment are unknown. `checks/regression-before/` retains exact baseline bytes and 19 failed/27 passed tests showing canonical rejection and exact-control defects. Intermediate 3.0.0's broad ARC validator conflated total Racket domain with sampled grammar; `checks/grammar-before/` retains 8 failed/87 passed cases and `checks/after/` retains mutation/minimal-impostor findings. One early damaged-ring test incorrectly rejected a single missing corner; that lawful template is now accepted separately and the malformed case removes a cardinal side. `checks/grammar-mid/` preserves that intermediate work. Early 3.1.0 special-case diagonal capacity was insufficient for checkerboards; two exact packing failures remain in `checks/packing-before/`.

Contrast originally used a larger target range and a period-three schedule. Period-two alternation restores canonical morphology more frequently; two default contrast targets suffice to refute first-only while avoiding unnecessary extra positive objects. Exact explicit counts 1..6 remain available. All current choices and rejected alternatives are detailed in `DECISIONS.md` in this return.

## Source-bound verification and remaining handoff

On the final hash above, `checks/focused-final/` records **98/98 passed** and `checks/task-tests-final/result.json` independently records **98/98 passed** in the isolated runtime, with no skips/errors/failures. Counts are parametrized pytest cases. `checks/after-packing-final/result.json` records **12/12 battery stages green**, no advisories/failures/interrupted/pending stages, exit 0, with rotations required. Selected authorities synchronize and execution parity passes; archival raw-code divergence remains explicitly reported by authority-sync diagnostics.

`checks/lesson-census-final.json` records **300/300 production lessons**, **1,200/1,200 single-query rotations**, **809 unique inputs** across 1,200 pair occurrences, zero production/rotation ambiguity, zero materialization/scoring errors, and zero hook warnings. It covers easy/medium/hard, 100 lessons per band, requested starts/indexes 0..99, with seeds derived from `sha256('lesson-census:v1:TASK:BAND:INDEX')[:8]` as uint32. `checks/schedule-census-final.json` enumerates declared starts 0 and 1 at fixed seed 0 in all three bands: **6/6 lessons, 24/24 rotations, 11 unique inputs**, the same zero-ambiguity/error/warning verdicts, and `complete_fixed_seed` coverage.

Both reports use **three demonstrations and one query**, holding each labeled pair out once while preserving remaining order. Production and rotation verdicts are separately `no_ambiguity_found` under required rotation policy. There are seven underlying rival functions represented by eighteen namespace entries; duplicated declarations are not new hypotheses. These are finite source-bound measurements. Rotations reuse labels, overlapping windows are not unique inputs, and accepted positions must be read from the recorded sampling metadata. Random support, undeclared hypotheses, the period declaration, and every possible rejected-pair schedule are not exhaustively certified. The post-repair solve uses these exact bytes, matches all three visible examples on its first actual program, and declares earlier rule exposure; masked-query correctness is unknown. Exact delta replay is reported in the return RESULTS.json. Audit acceptance must remain source-bound, and unrelated open audits are not resolved by this repair.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`; reviewer evidence is retained by precise source identity rather than replacing prior failures.
## Current reviewer considerations

Source SHA-256: `e8a0b3d73133b90b1fb605adc877d638413533391b8994e9891355425403985f`.

# Repair decisions: 7494855fa379

## Authority and final source

The selected Racket rule remains unchanged: a zero center becomes color **6** exactly when all eight cells in its surrounding 3×3 perimeter are color **4**. Every other cell remains unchanged. Version **3.2.0** pins `RULE_HASH = 856baaecfaa1`; final generator SHA-256 is `e8a0b3d73133b90b1fb605adc877d638413533391b8994e9891355425403985f`. Python predicates and rivals are diagnostics and independent test oracles, not replacement label authorities.

The imported version 2.1.1 notes contained no current design explanation. Its capacity-clipping comment explained a local small-grid failure, but the historical rationale for its difficulty minima, no-op axes, and exclusively positive-ring distribution is **unknown**. This return does not invent a predecessor justification.

## Canonical acceptance and exact controls

Canonical inputs include a singleton target and diagonally touching rings. Difficulty minima cannot define validity: the first canonical singleton was rejected by the old default/hard validator, despite being a legitimate canonical input. Final validation accepts all three labeled canonical pairs in every supported difficulty setting. Diagonally touching rings are separate under **four-connectivity**, so the validator and constructive placements use that relation instead of merging them by eight-connectivity.

Only four supported controls remain: `grid_h` (4..18), `grid_w` (5..20), `n_blocks` (1..6 positive rings), and `texture`. Exact numeric controls take priority over automatic curriculum selection: without an explicit texture they choose the default positive-ring texture. An explicit `texture='contrast'` also requires its three distractor motifs. Requests are honored exactly or rejected with an informative `ValueError` naming incompatible axes; counts are never silently clipped. Numeric values must be Python integers, excluding booleans, floats, and strings. Unknown and removed controls fail explicitly.

The old `palette_kind`, `palette_size`, `n_distinct_colors`, `density`, and `position_bias` were advertised without controlling observable pixels. They were removed rather than preserving misleading exact-control promises. Colors **4** and **6** have fixed semantic roles; arbitrary palette permutation is not a lawful augmentation of this rule. Color variation belongs only to the unchanged distractor motifs.

## Supported layouts and geometric limits

Two constructive placement families are supported: spaced pitch-four rows/columns, and alternating checkerboard positions on a three-cell lattice. Checkerboard motifs may meet at diagonal corners while remaining separate under four-connectivity. This restores canonical diagonal arrangements and exact 6×6/2, 6×9/3, and 9×9/5 positive-ring controls.

The capacity calculation is the largest available count in **these two supported construction families**, not a theorem about globally optimal packing. A refusal describes unavailable supported slots. Other legal arrangements may exist beyond these constructions; the implementation makes no global impossibility claim. This bounded constructive approach replaces retry-starvation and silent count reduction with deterministic realizability checks.

## Sampler grammar and lawful boundaries

The selected Racket program is defined on a broader domain than the generator's motif sampler. `self_check` validates the sampler grammar: nonempty rectangular integer-color grids whose nonzero four-connected components are recognized 3×3 motifs. It accepts positive yellow rings, complete yellow rings with occupied centers, same-color non-yellow hollow rings, and one-missing-corner yellow rings. A single lawful no-action motif is accepted even without a positive target. Arbitrary scattered pixels, short lines, 2×2 blocks, full canvases, and damaged unsupported perimeters are rejected.

`solid_squares` and `center_already_filled` remain lawful opt-in no-action boundaries and honor exact dimensions. `no_blocks` remains callable for backwards-compatible **negative-fixture** testing and preserves requested dimensions, but fails `self_check` and is excluded from the advertised valid texture list. Any of these zero-positive textures combined with explicit positive `n_blocks` is incompatible. No-action fixture labels do not imply ordinary production membership.

## Distribution and finite lesson policy

Uncontrolled production alternates two profiles by sample index, with declared period **2**: canonical-size core examples, then comprehensive contrast examples. Core draws use canonical shapes 5×7, 8×8, and 9×9 and one or two positive rings. Contrast draws use exactly two positive rings plus three counterexamples: a yellow ring missing one corner while all cardinal neighbors remain yellow; a monochrome non-yellow ring with zero center; and a yellow ring with occupied center different from zero and six. Positions, dimensions, missing corner, and distractor colors vary. Difficulty biases dimensions and counts only within applicable choices; it does not narrow exact controls or canonical validity.

The deliberate target count reduction from earlier broad contrast counts limits unnecessary object-count drift while retaining the witness for filling every target. Explicit positive-ring counts 1..6 remain supported, including explicit contrast counts when geometry permits. This is a distribution choice, not a change to the rule.

The intended lesson contains **three demonstrations and one query**. Alternation ensures each consecutive three-demo window contains contrast support. The declared finite rivals are identity, fill-yellow, orthogonal-only, seven-of-eight, any-color-ring, overwrite-center, and first-only. Tests derive labels with an independent predicate already checked against all three canonical labeled pairs, then inspect every declared period start, four seeds, and four difficulty settings. They check production three-demo refutation and **all four single-query holdouts**, preserving the order of remaining demonstrations. This finite seven-rival scope does not prove identifiability against undeclared hypotheses, arbitrary lesson assembly, or all seeds. Exact geometry/texture overrides can opt out of this uncontrolled curriculum guarantee.

## Reversals and retained failures

| Iteration | Decision reversed | Retained evidence |
|---|---|---|
| Imported 2.1.1 | Difficulty minima as validity, ignored controls, clipped counts, and hardcoded degenerate dimensions | `checks/regression-before/`: preserved source/test bytes, red replay script, report, log and JUnit; 19 failures / 27 passes |
| Intermediate 3.0.0 | Accepting any well-formed ARC grid as sampler membership | `checks/grammar-before/`: 8 failures / 87 passes; intermediate battery mutation/minimal-impostor findings under `checks/after/` |
| Grammar refinement | Initial damaged-ring test removed a corner, but that is an intentionally lawful near miss; it now removes a cardinal side and separately accepts a missing-corner-only motif | `checks/grammar-mid/` retains the intermediate run; no earlier failure was deleted or relabeled as a natural solve failure |
| Early 3.1.0 packing | Supporting only spaced motifs and a special two-ring diagonal layout overlooked larger valid checkerboards | `checks/packing-before/`: both exact 6×9/3 and 9×9/5 requests failed; source/test snapshots, report, log and JUnit retained |

The earlier period-three, larger-target contrast design was changed to period-two alternation and two default contrast targets to retain canonical morphology more often without losing the declared semantic witnesses. Current generator `notes.md` and `SUMMARY.md` describe only the selected final behavior; historical failures remain source-bound evidence.

## Verification available at this document revision

Final source has **98/98 focused pytest cases passing**, with zero failures/errors/skips, in `checks/focused-final/`. The separately prepared isolated task-test runtime also has **98/98 passing**, zero failures/errors/skips, in `checks/task-tests-final/result.json`; its runtime manifest binds the final generator hash. These are parametrized case counts, not 98 unique test functions. Exact commands, interpreters, runtime paths, exit statuses and evidence are retained in receipts and `RESULTS.json`.

The final after-repair battery in `checks/after-packing-final/result.json` is **all green: 12/12 stages, zero advisories, failures, interruptions, or pending stages**, exit 0. It binds the final source hash above and ran with `require_rotations_identifiable=true` and compact receipts. The green authority-sync result reports selected authorities synchronized and execution parity passing; retained archival raw-code divergence is reported in its diagnostics rather than silently cleared.

| Final source-bound lesson check | Production | Single-query rotations | Exact unique inputs | Evidence |
|---|---|---|---|---|
| Larger census: 100 lessons per easy/medium/hard band | 300/300 materialized; 0 ambiguity | 1,200/1,200 scored; 0 ambiguity | 809 across 1,200 pair occurrences | `checks/lesson-census-final.json` |
| Declared period enumeration: fixed seed 0, starts 0 and 1 in all three bands | 6/6 materialized; 0 ambiguity | 24/24 scored; 0 ambiguity | 11 across 24 pair occurrences | `checks/schedule-census-final.json` |

Both census reports have production and rotation status `no_ambiguity_found`, required rotation policy, zero materialization/scoring errors, and zero hook warnings. Each lesson has **three demonstrations and one query**; each rotation holds out one of its four labeled pairs and preserves the order of the remaining three. The larger census requests consecutive starts/indexes **0..99** per band and derives each seed as the first eight hexadecimal digits of SHA-256 of `lesson-census:v1:TASK:BAND:INDEX`, interpreted as uint32. The retained report records accepted sample indices and rejections, so requested start numbers are not substitutes for actual accepted positions. Fixed-seed enumeration has `complete_fixed_seed` coverage of both declared starting residues and all four query positions in easy/medium/hard at seed 0.

These reports evaluate **seven underlying rival functions**, exposed as **18 namespace entries** across semantic rivals, lesson competitors, and canonical shortcuts. Namespace duplicates are not eighteen independent hypotheses. Rotations reuse retained materialized labels and are not independent new draws. Exact input hashes distinguish unique grids; overlapping lesson windows are reported separately as pair occurrences. Neither census exhausts random support, proves the period declaration, certifies globally all accepted-pair schedules, or proves identifiability against undeclared hypotheses.

The post-repair solve is finished on the final source: first actual program, 3/3 visible examples, both masked queries executed, earlier exposure yes, no reference consulted during the solve. Hidden correctness remains unknown. Exact patch replay is complete in a freshly extracted original packet: independent Git root, clean patch check/application, all seven source paths hash-matched, 98/98 focused tests passing, and actual generated-witness Racket execution from the fresh checkout. RESULTS.json and checks/fresh-replay/replay.json retain commands and exact source identity. The repair adds distractors and varied placement but retains a deliberate 3×3-motif grammar with fixed 4/6 roles. Those constraints are stated rather than presented as coverage of the broader total-rule domain.
