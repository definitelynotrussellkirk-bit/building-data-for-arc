# Three-panel voting — current decisions

Version 3.0.0 repairs review `review-40d2bd8fd0adb4ae`. The canonical Racket rule remains `92b2f8e4de94`; no reference source is changed. The previous implementation (2.0.1) used one foreground color globally. That made color frequency and tie-breaking unobservable, even though all canonical examples and the old rule smoke passed.

## Rule and input domain

The input is three equal panels of height 3..7 and width 2..6, separated by exactly two full-height gray-5 columns. Panel values are integer colors 0..9 excluding 5; booleans and other types reject. At each local position, fewer than two nonzero votes produce 0. Otherwise choose the most frequent nonzero color; tied frequencies choose the larger numeric color. Output shape is height by panel width.

The reference splits at fixed offsets rather than searching for gray. This generator deliberately retains gray separators as the canonical visual convention. A missing separator remains outside its documented input domain, even if Racket can compute an output. Blank panels and disjoint/all-overlap occupancy are lawful but need not teach the rule.

## Ordinary teaching distribution

The previous independent equal-size monochrome masks are replaced by a constructive curriculum. Foreground counts cycle `[1,2,3,3,1,1,3,3]` with phase `(seed + sample_index) % 8`; geometry repeats over the same eight slots. Three monochrome slots use 3×3 and 4×4 panels in every difficulty band, preserving both observed canonical geometry/color profiles.

Seven local motifs include a singleton, each of the three panel pairs, two distinct-color pair orders, a lower repeated-color majority against a larger outlier, a higher repeated-color majority, and a three-way tie. Motifs can coincide in the monochrome/two-color slots. Locations and the three panel positions are randomized through keyed GenCtx draws. The same-color pair now uses the second color, so the simplest easy core does not equate numeric rank with global rarity. An empty local position is reserved. Medium and hard draws add up to 3 and 12 extra random vote triples; easy adds none. These are mechanical size/clutter bands, not a measured scale of human difficulty.

Three consecutive demonstrations always include a three-color grid. Every holdout of four consecutive ordinary draws retains a three-color grid. For three-color draws, at most 64 randomized layouts/clutter draws are tried and checked against all twelve declared competitors. If none qualifies, a deterministic core-only layout is used: low/middle/high colors have global counts 7/8/1, and the low color appears first and last in row-major scanning. This explicitly refutes global rarity, global commonness, first-seen and last-seen tie preferences while retaining the original local-vote witnesses. The fallback is verified before returning and has a forced-unlucky-layout regression. Every returned three-color core refutes all twelve declared competitors, so the intended production assembly is **three demonstrations plus one query**, with all four query rotations supported against that finite rival set. Arbitrary subsets or constrained-override lessons have no such guarantee. Finite rival tests do not prove that every possible alternative rule is excluded.

The generated input distribution is still intentionally narrower than all reference-lawful grids: ordinary palettes use at most three foreground colors, seven diagnostic motifs are mandatory, and ordinary sizes follow a cycle. Overrides expose all eight foreground colors and every advertised geometry. This is an explicit teaching design, not an estimate of a natural puzzle distribution.

## Exact controls and compatibility

`h=3..7`, `pw=2..6`, and `n_cells=1..18` are exact when supplied, in every difficulty band. `n_cells` means occupied cells **in each panel**. Without it, ordinary panel counts may differ; the observer and public draw record report their common count or None when there is none. Eighteen covers the ordinary maximum occupancy (six core cells plus twelve optional extra cells), so recorded common counts remain within the advertised integer range. `palette_size` and `n_distinct_colors` are exact aliases for the number of distinct foreground colors, excluding background 0 and separators 5, and support 1..8. Conflicting aliases reject. Only `palette_size` is advertised as an independent AXES entry; `n_distinct_colors` remains an explicitly declared `COMPATIBILITY_ALIASES` entry, with the same strict validation, provenance, observer value, and dedicated alias tests. This avoids counting one degree of freedom twice in the shared override matrix.

Explicit meaningful controls use a separate constructor. It adapts only unspecified defaults to satisfy capacity. No-overlap needs `3*n_cells <= h*pw`; all-overlap needs `n_cells <= h*pw`; default occupancy reserves both a two-vote position and a singleton and needs `n_cells < h*pw`. Realizing a palette needs `palette_size <= 3*n_cells`. Infeasible joint requests raise a ValueError carrying the supplied incompatible axis names. `observe_overrides` reads realized values from the grid.

`texture=no_overlap` uses disjoint panel masks and produces an all-zero output. `texture=all_overlap` means every **active** local position is present in all three panels, preserving an exact requested `n_cells`; it no longer means every grid cell is filled. Both are explicitly classified as lawful edge cases. The previous `no_separators` fixture and ignored `density` control are removed and reject. Fixed `palette_kind=default` and `position_bias=three_panels_5col_split` remain validated diagnostic descriptors. These descriptors and explicit `texture=default` preserve the ordinary curriculum when no geometric/count/palette constraint is supplied. Unknown keys reject, including when their value is None. Known None values retain GenCtx's no-override convention.

An intermediate four-slot cycle `[1,2,3,3]` produced only 13/60 canonical size/color-envelope hits in the pinned profile check. The eight-slot cycle increases nominal monochrome support from 25% to 37.5%, retains two three-color draws in every four, and keeps a two-color slot. This addresses sparse canonical-scale sampling without weakening the mixed-color lesson. The previous default path also omitted `n_cells` provenance; the new record reports the true optional common count rather than imposing artificial equal masks.

Independent review found two intermediate-version teaching failures omitted by the first eight rivals: globally rarest tied color and first-seen tied color. Both exact ambiguous lessons were checked with actual Racket and are retained in `counterexamples/*_lesson.json`. Their source bytes and later reference-receipt source binding are distinguished. The final hook diagnoses these retained lessons; new three-color draws must refute both and their commonness/last-seen counterparts. An explicit neutral texture default no longer switches to weaker constrained generation.

These changes reverse unsupported or misleading controls. Earlier historical rationale was not recorded in the imported notes. Keeping silently ignored options or clamping exact requests was rejected because it conceals caller errors. The version is bumped for the changed sampling and control semantics.

## Evidence and maintenance

`counterexamples/minimal_majority.json` shows `[2,2,9] -> 2`, refuting threshold/max and last-nonzero. `counterexamples/minimal_tie.json` shows `[2,7,0] -> 7`, refuting repeated-color-only and first-nonzero. Both outputs were executed through public Racket apply; the baseline validator accepted both, but the baseline could never generate mixed foreground colors.

`tests/test_majority.py` covers literal votes, canonical pairs, structural rejection, exact controls, structured incompatibilities, cyclic lesson rotations, deterministic generation, and both canonical profiles. `workspace/probe_vote_support.py` independently prepares all 729 ordered votes from the nine allowed panel values, validates public reference receipts, and measures actual declared competitors. Its 18 packed grids also check 27 padding cells. Its tests label synthetic receipts as parser fixtures, not reference evidence.

The review return retains baseline failures, final-stage reports, actual reference receipts, wider lesson census and all cyclic starts, independent code review, and source-bound solve episodes. Consult those measured reports for counts; this note makes no unrecorded final-pass claim. Hidden solve correctness is withheld for independent maintainer scoring. No open reference-rule discrepancy is known; selected authority is synchronized, while an archival raw-code field differs and is preserved.


## Current owner acceptance

Accepted the scoped generator, portable tests and task-local authoring tools using the October 3 lightweight policy. All semantic batteries, Racket comparisons, censuses, solves and replay counts in the reviewer evidence remain reviewer-reported; no routine maintainer rerun or model training admission is claimed. Exact source/rule approval records bind the accepted bytes. Both random audits remain independent findings, and shared tool requests remain proposals unless separately implemented.
## Current reviewer considerations

Source SHA-256: `8f0694eebe24e4f3d5cce2d0d7bfa84b771bbb0952bb9da7219935bf2b4b1e09`.

# Decisions and tradeoffs

Task `2ca05c7eef24`, version 3.0.0, assignment `review-40d2bd8fd0adb4ae`. The imported notes did not record a substantive historical rationale for the original distribution and controls; that rationale is **unknown**, and the explanations below concern this repair. Actual commands and failed iterations remain in `checks/commands/`.

## Input and teaching decisions

| Prior choice or alternative | Current decision and reason | Evidence, cost, and limit |
| --- | --- | --- |
| One foreground color globally | Construct mixed-color local votes, including lower and higher repeated majorities and numeric tie-break witnesses | `[2,2,9] → 2` is validator-accepted but impossible for the baseline sampler. Mandatory motifs narrow the ordinary support. [Diagnosis](checks/shortcut-diagnosis/summary.json) |
| Independent random masks | Seven constructive motifs, random positions and panel permutation, reserved empty location; easy/medium/hard add 0/≤3/≤12 extra local triples | Makes relevant distinctions reliable. Geometry/clutter bands are mechanical and not human-calibrated. |
| Initial four-slot `[1,2,3,3]` cycle | Eight slots `[1,2,3,3,1,1,3,3]`, phase `(seed+sample_index)%8`, canonical 3×3/4×4 monochrome panel slots in every band | The first candidate yielded only 13/60 profile hits; final yields 24/60, including every band. Nominal monochrome support rises from 25% to 37.5%; two rich draws remain in every four. [Failed battery](checks/after-v1/result.json), [final profile](checks/after-verified/checks/2ca05c7eef24_after_profile_floor.json) |
| A small hand-picked local rival set | Declare twelve canonical-fitting rivals; test all completed three-color inputs against every rival | Review found global-rarity and first-seen ambiguous lessons. All twelve fit 3/3 canonical pairs. Finite alternatives cannot prove universal identifiability. [Review](checks/code-review/REVIEW.md) |
| Core color counts 9/6/1 | Change the same-color pair from `(0,a,a)` to `(0,b,b)` | Deterministic core now has low/middle/high counts 7/8/1. This breaks the correlation between numeric rank and global rarity. Clutter still requires a final rival check. |
| Unrestricted randomized layout acceptance | At most 64 random attempts, then a deterministic row-major core that is verified against all twelve rivals | Ensures bounded generation and supports a source-level holdout argument. Rejecting layouts changes the distribution; fallback may use less clutter. A forced-unlucky-layout regression exercises this path. |
| Any subset of examples | Intended assembly is three consecutive ordinary demonstrations and one query, with all four single-query holdouts | Every four slots contain two three-color draws. Actual production and fixed-seed phase censuses support the stated assembly. Arbitrary subsets and meaningful constrained overrides retain no equivalent teaching guarantee. |
| Remove gray separators because reference uses offsets | Keep exactly two gray-5 divider columns as the visual domain; reject panel value 5 and malformed types/geometry | The canonical reference operates at fixed offsets. A computed Racket result is not sufficient to make malformed visual inputs part of this generator's contract. Blank/disjoint/all-overlap lawful cases remain distinguishable from teaching-quality cases. |

## Exact controls and compatibility

| Decision | Reason and evidence | Cost or boundary |
| --- | --- | --- |
| Honor `h=3..7`, `pw=2..6`, count and palette controls independently of difficulty defaults | Original controls were ignored or constrained by incidental per-band defaults. The new planner adapts only unspecified values. | Exact meaningful overrides use a separate constructor and weaker teaching contract. |
| `n_cells=1..18` means occupied cells in each panel when supplied | The ordinary path can use six core cells plus twelve extras per panel. The intermediate 1..6 range and absent default provenance were misleading. | Ordinary panel counts can differ; observed/common count is `None` if no equal count exists. Recording a fake common count or forcing equal masks was rejected. |
| Palette size 1..8, excluding 0 and 5 | All eight lawful foreground colors are supported by exact overrides, while ordinary teaching uses 1..3 colors. | Exact palette needs `palette_size ≤ 3*n_cells`. Uniform use of all eight colors was unnecessary for the teaching core. |
| Keep `n_distinct_colors` as a strict compatibility alias, remove it as an independent `AXES` dimension | Final-candidate lint detected duplicate independent dimensions. API validation, conflicts, observer/provenance, and alias tests remain. | Metadata enumerators see one independent palette axis. Full final checks were rerun after this last metadata edit. |
| Structured `ValueError.incompatible_axes` for infeasible joint controls; reject unknown keys | Silent clipping or ignoring controls hides caller errors. All 32,400 pinned combinations have independently checked outcomes. | Default needs `n < area`; no-overlap needs `3n ≤ area`; all-overlap needs `n ≤ area`; palette needs `p ≤ 3n`. Only supplied keys are named in incompatibilities. |
| `texture=no_overlap` is lawful, with zero output | Disjoint occupancy does not teach color voting but is an honest edge case. | It is not promised as a standalone discriminating lesson. |
| `texture=all_overlap` means all active local positions occur in all panels | Preserves an exact requested count. Previously the texture forced every cell filled. | This changes prior texture semantics and is documented in the version bump. |
| Remove ignored `density` and invalid `no_separators` | They did not represent honest supported controls. | Callers using them now receive an explicit error. |
| Neutral `texture=default` and fixed diagnostic descriptors preserve the ordinary path | Independent review reproduced an explicit-default call switching to weaker generation. A regression now enforces no-op behavior. | Meaningful geometry/count/palette constraints still select the controlled constructor. Known `None` means no override; unknown keys with `None` still reject. |

## Tool, tests, and reference decisions

The reusable task-local tool uses an independent Counter-based expectation and public `apply` receipts. Preparation packs all 729 triples into 18 inputs; scoring checks all vote and padding outputs as well as source/rule/input/output and metadata bindings. It does not call `generator.apply_rule`. Its coverage mode reads the declared competitors dynamically and labels its results Python-proxy coverage. [Tool documentation](repo/generators/2ca05c7eef24/workspace/README.md).

Independent review showed that Python dict equality treated `False`, `0`, and `0.0` as interchangeable. Four type-corrupted sidecars passed despite an unchanged invalid digest. The repair recomputes the digest of received metadata and compares type-sensitive canonical JSON with reconstructed metadata; all eight stale/recomputed-digest mutation regressions pass. An unsigned consistency-checked receipt is still not authenticated. Deliberate same-size/same-mtime cache replacement in a long-lived process is outside the tool's claimed coverage; ordinary CLI preparation/scoring use separate processes.

The selected canonical rule, selected base source, and canonical ledger remain unchanged. Authority synchronization found a divergent archival `raw_code` field, but selected authority equality and actual execution parity pass; editing unrelated archival text was rejected. No test that acts as a frozen packet fixture was edited. New tests use portable `reviewer_support` helpers and run through the public isolated `task_tests` stage.

## Preserved failures and review rulings

The baseline generator regressions first yielded 75 failed/13 passed; literal majorities then exposed further missing behavior. The first integrated candidate passed 127 tests but its battery had two failures: profile support and default-count provenance. The next regressions reproduced those gaps before their correction. Actual intermediate global-rarity and first-seen ambiguous lessons are retained, as are tool parser red cases and the final-candidate duplicate-alias lint failure. These are historical failures bound to their own source hashes, not remaining failures of the final source.

The independent reviewer inspected initial checkpoint `04faae860803cb2899d9fe779d2f9ca69332d2f4`, then corrected generator `eceab1ffd0c9487dc64e28b34b9e724049db31e2530a389f6c28ecfbd1b90b25` and final probe `b47e286bed56bb3f37cb94eeb15d06a14ee5a5cc21c9c37d398d283ca283b747`. Three important issues and one neutral-default compatibility issue were reproduced and corrected; focused correction verification was 14 passed/131 deselected. The later alias metadata change and all final source verification are parent-owned. [Full independent review](checks/code-review/REVIEW.md).

The reviewer explicitly declined to claim universal identifiability, human difficulty calibration, hidden solve success, other-task repair, unsigned receipt authentication, or final parent-owned verification before its execution. These are appropriate limits, not unfixed source blockers. The two audit targets remain audit-only, as assigned. The blind episode records no earlier exposure; the main episode honestly records earlier exposure and no reference consultation during solving. Neither hidden-query correctness nor training approval is inferred from visible-example success.

## Reproduction and stopping condition

The original ZIP and both prior-round return ZIPs are preserved. This round independently installed Python dependencies and the bundled Racket runtime; previous outputs were not used as new measurements. The return builder checks the selected-task delta and all other issued repository files. The final gate applied the exact source patch to a new extraction of the original ZIP with its own verified Git root and independently rebuilt runtime: 145 portable tests, all 729 actual-reference votes plus 27 padding cells, and three generated lessons with twelve query rotations passed. [Fresh replay](checks/replay/summary.json) retains the source and patch hashes. The final return's patch is checked byte-for-byte against the replayed patch; report/evidence edits after replay do not alter generator source.

Completion means the requested repair, question, feedback, both solves, both audits, final-source checks, exact patch replay, and validated compact return are delivered. It does not change admission metadata, promise correctness for undisclosed hidden labels, or claim all possible alternative rules have been excluded.

## Native parametric family — review-6577472d8bd4ca54

The accepted production generator and canonical voting rule remain unchanged. The task-local native family adds `finish_rule=vote_only` as the byte-exact default and `finish_rule=vote_then_keep_output_mode` as a composed alternative. Stage A applies the canonical local three-panel vote; Stage B computes the unique nonzero mode of the completed voted grid and erases every other voted color.

Inputs are matched across settings and deliberately make the raw-panel global mode differ from the voted-grid mode, so Stage B cannot be replaced by a pre-vote frequency shortcut. The minimum two-example curriculum also rejects largest/smallest voted color, rarest voted color, first/last seen color, identity, and the opposite setting in a finite protected-Racket audit covering seeds 0 and 17. This audit is finite and does not prove uniqueness against arbitrary programs.

The family supports 2–6 demonstrations and 1–4 prefix-stable queries. Its largest lawful stress case is 30×29 because three equal panels plus two separators have width `3*pw+2`; exact width 30 is impossible. Native qualification and byte-identical replay passed on both settings and seeds 0/17. The retained wrong-intermediate witness substitutes the raw-input mode for the voted-grid mode and changes 15 output cells. Owner integration, fresh acceptance replay, and any training-admission decision remain pending.
