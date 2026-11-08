# Current decisions: d48317a7c7c8

Review `review-e112c2eed9e98149`, 2026-10-08. Selected version: **3.0.0**.
Final generator SHA-256: `7f65ed5ebc7cd917e71a8c6f121bcbdd6d411a6a98bf7c2db5bb5cf69b6717e2`.
Baseline: `b5b4cb28fb8f4c150ab2c1fe7f5d0e687465eaab2321dc3ad79829e7600706ba`.
Canonical Racket authority remains `b2af6531f18d`; no canonical or base-rule bytes changed.

## Intended rule and accepted input domain

Use monochrome 4-connected components. Only a straight component of exactly three yellow (4) cells is a target. Inspect the original input independently at both endpoints: paint cyan (8) one cell beyond an endpoint only when it is in bounds and originally background (0). Other colors, longer components, bent components, off-grid caps, and occupied caps remain unchanged. Diagonal same-color contact does not merge components. Shared empty caps are legal and painted once.

`self_check` accepts a rectangular ARC integer grid with at least one such target and at least one available cap. It rejects bools, strings, floats, ragged rows, and target-free/no-actionable-cap scenes. This is the productive generator domain, not the full mathematical domain of the reference program: the latter also labels many no-op grids. It accepts all five canonical inputs. The old substring detector admitted length-four and bent-four no-op objects; the component-based validator fixes that defect (R1).

## Distribution and exact controls

The implemented controls are `grid_h=8..24`, `grid_w=8..24`, `n_bars=1..10`, and `distractor_color` in `1,2,3,5,6,7,8,9`. An exact override is honored in every difficulty band; difficulty affects unpinned distributions. Unknown keys and the former ignored palette/texture controls now fail explicitly. `None` retains the standard unpinned convention. `observe_overrides` derives actual dimensions, target count, and the nonyellow three-bar color from the returned grid (R2).

The documented rich-construction capacity is `min(10, max(2+(h-8)//2+(h//2)*((w-8)//6), 2+(w-8)//2+(w//2)*((h-8)//6)))`. This is a guaranteed supported construction, not a maximum-packing theorem. Jointly pinned geometry/count requests above it raise a structured `ValueError` naming participating axes. Unpinned counts and dimensions adapt jointly. The original advertised 5..24 geometry was not implemented; 8..24 is the honest contract for this richer constructor.

Ordinary draws have at least two targets: an edge-clipped target with a diagonal yellow singleton, and a target with one occupied nonyellow cap. Each scene also has a nonyellow straight three-bar, a yellow straight four-bar, a bent yellow four-component with a three-cell arm, and a yellow L-three. Extra targets, positions, orientations, shapes, and distractor colors vary. The blocker is 6 when the selected distractor color is 8, so occupied-cap overwriting remains an observable error. Random packing is bounded; a guaranteed fallback preserves exact counts and all promised roles. Protected cap witnesses and same-color cardinal separation prevent accidental mergers or canceled disagreements (R3).

Even requested sample indices favor canonical dimensions `(10,9), (9,8), (8,10), (10,8)` and two targets; odd indices have broader support. Color 6 has extra weight to retain the canonical palette. Other choices remain possible. The final profile check found 20/60 exact profile hits (7/20 easy, 7/20 medium, 6/20 hard), with no canonical rejection. This reports dimensions/palette overlap, not identical distributions.

An explicit `n_bars=1` control remains supported; it omits the blocked-target role and carries a weaker teaching promise. A first repair allowed one-target ordinary draws too; seed 0, sample 75, hard left the multicolor/overwrite rivals unrefuted, so ordinary counts were changed to at least two. Another first-repair defect rejected pinned 8x8 geometry after drawing an infeasible unpinned count; counts now adapt before geometry. Exact red evidence is retained under `checks/iteration-1/` in this return (R4).

## Executable competitors and reference checks

Nine distinct rivals are declared under the actual semantic/canonical/lesson namespaces: `any_color`, `at_least_three`, `sliding_triples`, `maximal_runs`, `eight_connected`, `multicolor_components`, `both_in_bounds`, `both_empty`, and `overwrite_occupied`. All fit all five canonical labeled pairs; they are executable hypotheses, not just names. `workspace/probe_review.py` discovers the declarations dynamically, uses a separately written maximal-run/external-neighbor detector, and obtains labels through public `Catalog.apply`. The generator's Python mirror is an authoring diagnostic, never the label authority.

The retained 8x8 rich witness in `counterexamples/review-e112c2eed9e98149.json` refutes all nine using actual Racket output. The separate final probe labeled 55 inputs: five canonical, fourteen literal edge cases, and 36 ordinary draws (base seed 20261008; actual easy/medium/hard seeds 20261008/20262017/20263026, requested indices 0..11 per band). All ordinary draws refuted all nine; all literal expectations and mirrors matched the actual reference. Source-bound receipts are in `checks/semantic-probe/final/` in the return ZIP.

The lesson contract uses three demonstrations and one query. The final public census materialized 100 lessons per band, requested starts 0..99 and the documented SHA-derived seed recipe: 300 lessons, 1,200 labeled pairs, 1,200 unique grid hashes. Production: 0/300 ambiguous. Holding out each of the four labeled pairs once while retaining the other three in order: 0/1,200 ambiguous rotations. All materialization/scoring/hook error counts were zero. These are finite results against nine distinct rivals (reported in three namespaces), not universal identifiability or enumeration of every cyclic start.

## Validation and limits

Final source: twelve-stage battery 12 green / 0 advisory / 0 failed; exact-override matrix 16,290/16,290 accepted, zero findings; isolated task suite 89/89 passed. The independent implementation review checked 20,144 fallback geometry/count/color combinations and other bounded probes on the immediately preceding source. The final difference was exactly two local variable renames; normalized AST equality was checked. Its detailed source-bound report remains `checks/code-review/report.md`; the final public battery, task suite, and census were rerun on the hash above.

Fixed rich-scene role counts, protected disjoint cap positions, and the packing budget restrict support. Ordinary generation does not cover every possible target-free, overlapping-cap, or minimal scene. Shared-cap behavior is covered by canonical/reference fixtures; it is not claimed as ordinary generation coverage. No arbitrary-object, universal-rule, training-admission, or model-learning claim is made.

## Prior audit resolutions proposed to the maintainer

The current immutable `evidence/review_index.json` contains two source-matched entries still marked `needs_triage`. This return cannot edit that index under the official allowed delta. Do not infer a status change from this note. The following are explicit resolution proposals for the maintainer, scoped to this final source:

- `review-1a2617aa91d1bf57:v0001`: resolve the color-specificity coverage and false length-four acceptance findings using R1/R3, the rich counterexample, final 55-case Racket probe, and regression tests. Both original findings were reproduced on the exact baseline.
- `review-ffa6181558635310:v0001`: resolve the missing hash, impossible advertised `n_bars=10`, ignored/unknown controls, missing distractors, and absent executable lesson contract using R2/R3 and the final battery/override/census evidence. Ignored controls were retired explicitly, not silently reinterpreted.

Neither proposal resolves findings on any other task. Approval/training status and unrelated retained evidence are unchanged by this patch. See the return's `DECISIONS.md`, `RESULTS.json`, and `AUDIT.md` for the complete handoff, actual command receipts, and both separate assigned audits.
## Current reviewer considerations

Source SHA-256: `7f65ed5ebc7cd917e71a8c6f121bcbdd6d411a6a98bf7c2db5bb5cf69b6717e2`.

# Decisions and reversals — review-e112c2eed9e98149

## Scope and authority

The immutable draw selected repair task `d48317a7c7c8` and question `generator-shortcuts`; the two later audit targets are `4fd85612056f` and `f5a58a06c0b4`. Each draw was used once. Only allowed task-local implementation, tests, notes, summary, workspace, and counterexamples enter the official patch. Canonical rule `b2af6531f18d`, the canonical ledger, selected base rule, audit sources, and shared tools remain unchanged. Racket supplies every claimed reference label; Python mirrors are diagnostics.

## Distribution decisions

| Choice | Rationale and alternative considered | Evidence / consequence |
| --- | --- | --- |
| Exact monochrome cardinal components (R1) | Substring scans confuse a valid triple with an arm of a larger component. A looser run-only detector remains a declared rival. | Length-four/bent-four baseline failures; independent reference fixtures and canonical acceptance |
| Productive validator | At least one exact yellow triple must have an available cap. Accepting every no-op reference input would weaken the generator's task contract. | Fully blocked/no-target fixtures are labeled correctly by Racket but rejected by the productive validator |
| Independent endpoint availability | Boundary clipping and occupancy must not require both caps to be available. Occupancy is checked in the original input. | Literal boundary/occupied/shared-cap Racket cases; ordinary edge and blocked roles |
| Four truthful axes (R2) | Keep geometry and exact target count; replace ignored palette/texture knobs with an observable distractor color. Inventing semantics for every dead knob would expand scope and obscure replay. | Final 16,290-draw exact-override matrix; unknown/retired keys explicitly rejected |
| 8..24 geometry and conservative joint capacity | The rich witness construction needs an 8x8 core. Earlier advertised 5..24 support was not implemented. Supporting arbitrary smallest scenes would complicate exact promises. | Documented capacity and structured pinned-combination rejections; independent full fallback sweep |
| Random placement plus guaranteed fallback | Unbounded rejection risks hangs; dropping targets violates exact counts. Bounded randomized placement varies support, then a proven construction preserves roles and counts. | 20,144 fallback cases; 1,156 bounded random-constructor cases; final reference checks |
| Every ordinary scene contrasts rule filters (R3) | Pure targets leave obvious color/length/component shortcuts indistinguishable. Randomly omitting each witness can leave whole lessons ambiguous. | Wrong-color triple, straight four, bent four, L-three, diagonal singleton, edge and occupied caps; nine declared rivals refuted on every ordinary semantic-probe sample |
| Protected, disjoint witness caps | Merely including a distractor can fail to produce an observable rival disagreement if another object already paints the same cell. | Packer protects each witness; color-8 distractors use a noncyan blocker |
| Canonical profile mixture | Larger richer grids alone caused poor canonical support. Even-index weighting favors the four actual shape profiles and two targets; color 6 is weighted. | Final exact-profile hits 7/20 easy, 7/20 medium, 6/20 hard; all five canonical inputs accepted |
| Three-demo lesson contract | Preserve the public ordinary lesson format with an executable competitor check. Correct per-grid labels alone are insufficient evidence of teaching. | 300 production lessons plus all 1,200 held-out rotations; preserve remaining demo order |

Defaults do not claim full support for all legal no-op scenes, every shared-cap collision, or arbitrary connected shapes. Fixed scene roles and capacity are explicit restrictions. The exact-color rule keeps yellow 4 and output cyan 8 fixed; distractor colors vary, so indiscriminate palette permutations are inappropriate. No color-permutation proof is claimed.

## Reversals retained

1. **R4a, infeasible unpinned count:** first repaired source `99e1312ce61674e16f3de409242180c6446a6a3627faeab1e61d0f325052bb98` drew count 5 when only 8x8 geometry was pinned, then raised a structured incompatibility. A caller had not pinned the count. `checks/iteration-1/small-board-probe.json` records seed 0, requested index 1 in all bands. The fix samples feasible unpinned counts first; no silently changed explicit override.
2. **R4b, weak ordinary one-bar scenes:** the same source allowed ordinary count 1. Seed 0/index 75/hard omitted the occupied-target witness, allowing `multicolor_components` and `overwrite_occupied` to survive. `ordinary-one-bar.json` records it. Defaults now use at least two targets; an explicit count 1 remains a legitimate exact override with a weaker teaching promise.
3. **Red tests before the fix:** `packing-regression-red.log` records four failures and one pass for the targeted selection; no manufactured solve failure was substituted for a regression. The initial baseline 61-case suite had 51 failures/10 passes; subsequent useful cases increased the final suite to 89.
4. **Lint-only final rename:** source `04a95b8d7c8dedc02acb2277426fa3df55fcb110e995acf700b8f9b64b467cb3` passed eleven battery stages, with lint objecting to the local identifier `objects`. Renaming it to `components` in two functions produced final `7f65ed5ebc7cd917e71a8c6f121bcbdd6d411a6a98bf7c2db5bb5cf69b6717e2`. The independent review confirmed exact AST equivalence after that name normalization. Final public checks were rerun.
5. **Interpreter isolation:** a user-site pytest installation did not satisfy the public isolated task-test preflight. `checks/task-tests/result.json` correctly reports infrastructure failure/no tests. An owned environment with pytest 9.1.1, NumPy 2.3.5, and Pillow 12.3.0 passed that exact preflight and ran all 89 cases. The failed prerequisite attempt remains evidence.

## Lesson claims and schedule policy

Final census: three demonstrations, one query, 100 requested lessons per easy/medium/hard band, requested starts 0..99. Seed is the first eight hexadecimal digits of SHA-256 of `lesson-census:v1:TASK:BAND:INDEX`, interpreted as uint32; exact accepted indices are in the report. All 300 materialized, yielding 1,200 unique input hashes and no production ambiguity. Rotations hold out each of four labeled pairs once and preserve the remaining order; all 1,200 rotations had no declared-rival ambiguity or hook/scoring errors.

The census's reporting modulus 6 is not a declared exhaustive deterministic schedule. Random draws vary by seed and start; no complete cyclic-window enumeration is claimed. The three namespaces refer to nine distinct callables. Results apply only to this finite population and declared rivals; the audit findings on other tasks demonstrate why this qualification matters.

## Existing audit status and scoped resolution proposals

The immutable `evidence/review_index.json` on the repair task retains `needs_triage` for two exact-baseline findings. Its separate `triage.status=accepted` on one record is not an explicit resolution. Official patch scope excludes the index, so the following are maintainer actions proposed for this final source, not status edits already performed:

| Prior return | Explicit proposal | Resolving evidence |
| --- | --- | --- |
| `review-1a2617aa91d1bf57:v0001` | Resolve color-specificity coverage and length-four false acceptance on final version 3.0.0 | R1/R3 tests, rich actual-reference counterexample, 36 ordinary reference probes and larger lesson census |
| `review-ffa6181558635310:v0001` | Resolve missing hash, exact-count/ignored-key defects, absent distractors, and missing executable lesson contract on final version 3.0.0 | R2/R3, 12-stage final battery, 16,290 accepted matrix draws, strict key tests, 300/1,200 lesson results |

Unrelated audit findings are unaffected. In particular, the two newly drawn audit targets remain findings-only, with source hashes unchanged and no approval/training-admission decision implied.

## Audit and tooling decisions

A1/A2 identify a source-supported unique-irregular-shape shortcut, rejection of a canonical rectangular winner, and an ignored legal height override in `4fd85612056f`. A3 identifies an orientation-conditioned endpoint rival in `f5a58a06c0b4`: twelve ordinary probes fit, six accepted four-demo lessons fail to eliminate it, and two valid actual-reference queries separate it. Canonical data also separates both audit rivals. Complete minimal inputs, actual Racket/rival outputs, domains, hashes, and commands are in their audit evidence.

F1 proposes an opt-in conditional-competitor shared check, motivated by A3. F2 proposes testing free-axis feasibility, motivated by R4a. F3 proposes narrowing a lexical lint false positive, already resolved locally. No generic shared checker was patched without task-family semantics; the reusable task-local probe and regressions are implemented now.

## Solve exposure and handoff

The blind task was solved from visible examples before generator/rule/notes access; first genuine revision matched all three visible examples. The post-repair task is explicitly exposed due to prior repair/reference work and a delayed helper summary; source remained closed while authoring that later program. Its first revision also matched three visible examples. Both programs execute their two queries, whose correctness is not disclosed by visible-only feedback. Frozen final notes and every real revision remain intact; no intentional negative is represented as a naturally failed solve.

A fresh packet was independently extracted, with an isolated Git root at `WORK` to match the official `repo/` patch paths. The exact official patch `97d1706be0ccf7de8e6ccf62900025a110a14f941a930e2b77546e6f8de7057e` passed `git apply --check`, applied successfully, and matched all eight reviewed source-file hashes. The fresh isolated task suite passed 89/89 tests, with no failures/errors/skips; receipts are in `checks/fresh-replay/`. Disk pressure required deduplicating identical already-verified Racket dependency files; repository source files remain independently extracted. No source or failure evidence was removed to save space.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-b31280cb8de4a416:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `7f65ed5ebc7cd917e71a8c6f121bcbdd6d411a6a98bf7c2db5bb5cf69b6717e2`. At disposition, audited bytes match the current source.

### Current decision

Audited source is repo/generators/d48317a7c7c8/generator.py,unchanged SHA256 7f65ed5ebc7cd917e71a8c6f121bcbdd6d411a6a98bf7c2db5bb5cf69b6717e2. No issue found within bounded current-source audit:89 portable tests and semantic gate pass,600/600 strict samples,5 canonical inputs,nine declared witness/rival pairs verified;12 lessons identifiable and0/48 rotated ambiguities. Finite source/rival scope,no universal correctness or new target approval. No owner audit rerun or new target approval. Target-local receipts: `checks/audit/d48317a7c7c8-combined/checks/d48317a7c7c8_audit_battery_summary.json` `checks/audit/d48317a7c7c8-combined/checks/d48317a7c7c8_audit_commands.jsonl` `checks/audit/d48317a7c7c8-combined/checks/d48317a7c7c8_audit_semantic_gate.json` `checks/audit/d48317a7c7c8-combined/checks/d48317a7c7c8_audit_semantic_gate.log` `checks/audit/d48317a7c7c8-combined/checks/d48317a7c7c8_audit_semantic_gate.ok` `checks/audit/d48317a7c7c8-combined/checks/d48317a7c7c8_audit_semantic_gate.receipt` `checks/audit/d48317a7c7c8-combined/checks/d48317a7c7c8_audit_summary.json` `checks/audit/d48317a7c7c8-combined/checks/task_tests.xml` `checks/audit/d48317a7c7c8-combined/progress.log` `checks/audit/d48317a7c7c8-combined/result.json`

### Assessment or prior finding

## d48317a7c7c8

**No issue found in this finite audit.** I reviewed current source SHA-256
`7f65ed5ebc7cd917e71a8c6f121bcbdd6d411a6a98bf7c2db5bb5cf69b6717e2`, focusing
on exact target counts, independent endpoint availability, component/color
filters, fallback packing, override validation, and declared rivals.

The strict combined audit passed 89/89 portable task tests and the semantic gate.
The semantic report accepted 600/600 sampled inputs as strict, all 5 canonical
inputs, observed and verified all 9 witness/rival pairs in every sampled draw,
found 12/12 lessons identifiable, and found 0/48 rotated ambiguities. Evidence is
`checks/audit/d48317a7c7c8-combined/`.

This conclusion is limited to the inspected source, tests, canonical fixtures,
600-draw semantic sample, and nine declared rivals. It is not a universal proof or
new approval. The target was not modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->

## 2026-10-24 proposed target-length parametric family

A task-local native adapter now exposes one meaningful episode-fixed parameter,
`target_length ∈ {3,4}`. The default `3` returns the canonical Racket program
byte-for-byte; `4` changes only the exact straight yellow-component length while
preserving 4-connectivity, color specificity, independent cap availability and
cyan cap painting. Inputs are setting-independent and support 2–6 demonstrations
and 1–4 queries. Retained examples use three demonstrations and four distinct
queries, including a substantive 30×30 case.

Bounded self-review found and repaired two authoring defects: small canvases were
incorrectly required to place an extra bar outside their candidate region, and
the evidence runner initially bound a private grid name even though this
canonical non-lambda rule reads `g` directly. Regressions cover count limits,
matched inputs, finite-rival teaching from demonstrations only, Racket/Python
parity, 30×30 action density, strict public/private projection, and public IDs
that do not depend on private query answers. A final packet-level export audit
also caught pretty-printed/truncated public identities and then the nonconforming
`arc-` prefix; the writer now emits exact `public_challenge_bytes` under
`challenge-<full-sha256>.json`, and the official helper passes all ten retained
public episodes across the three assigned tasks. The full task-local suite passed
96 tests. Native qualification passed all four setting/seed jobs for seeds 0
and 17 with 3 demos and 4 queries. Evidence is under
`WORK/checks/parametric/d48317a7c7c8-target-length-v1/` and
`WORK/checks/parametric/d48317a7c7c8-qualification/`; the source-bound inventory
hash is `a71357e5a75e79dfb686b9506a4768ce53c63cc28d554aa9f960cfb1977cb072`.
This remains a proposed prototype, not acceptance or training admission.
