# Current design: 03909f3e98e7, v4.0.0

Generator source SHA-256:
`00ad93e1c016bd4e496c67a4fa1149942f060037377f54faf1b16f5305820b04`.
Selected rule hash: `78ddb8aa1ad2`. Labels remain Racket-derived. The authority's
executable semantics were preserved; the bound `target_code` comment was
synchronized with the selected reference. See the final
[authority synchronization evidence](../../../checks/after-final/checks/03909f3e98e7_after_authority_sync.json).

## Intended transformation and domain

Take the bounding box of **all** nonzero cells, including every disconnected
component and internal zero row or column. Place that entire crop on a fresh
zero canvas of the original dimensions at
`((grid_h - crop_h) // 2, (grid_w - crop_w) // 2)`. Preserve colors, zero gaps and
all relative positions. Odd spare margins therefore put the extra background
row or column below or to the right. Cropping a single component, removing empty
internal axes, or centering by foreground mass changes the intended rule.

The ordinary teaching domain is a rectangular list grid, dimensions 6..14,
literal integer colors 0..9, and 3..8 nonzero cells using 2..3 foreground colors.
The crop must visibly move. Validation rejects malformed grids, empty content,
out-of-domain counts/palettes, and already-centered identities without modifying
the input. Strict canonical likeness additionally requires one of the five
public height/width/palette profiles, 4..5 cells in a 2..3 by 3 crop, eight-way
connectivity and no empty internal axis; broad lawful inputs need not meet it.

Exact controls are `grid_h`, `grid_w` (6..14), `shape_size` (3..8), and ordinary
`texture` (`blob|scatter`). All ordinary combinations work in every difficulty
band. Numeric controls and seed/index reject coercion and booleans; indices are
nonnegative, and difficulty is `None|easy|medium|hard`. Unknown controls/textures
fail explicitly. `None` keeps the no-override convention. Actual dimensions and
nonzero count are observable from returned pixels. Connected frontier growth
and exact subset sampling replace silent clipping or smaller fallback shapes.

Diagnostic textures remain outside the ordinary texture domain:
`already_centered` honors dimensions and cell count; `shape_fills_grid` honors
dimensions but rejects an explicit ordinary `shape_size`. Both deliberately
fail ordinary `self_check`. An empty input also fails this teaching validator;
the official empty-input probe returns identity, so no rule-crash claim is made.

## Current curriculum and design reversals

Uncontrolled draws repeat **core, witness, free, witness**, a period-four
schedule. Core draws use five canonical profiles and varied connected masks.
Free draws cover the full dimension/count domains with difficulty-weighted
dimension sampling and connected or scattered content. Rich witnesses use a
pool of **197 distinct immutable geometry masks**, 6..8 cells in a 4x5 bounding
box, with skewed mass, empty internal axes and disconnected content. They use
three foreground colors and a fixed 9x10 canvas; palettes, assignments and
off-center placements still vary. The pool caches geometry, not sampled grids.

With three demonstrations and one query, any consecutive default four-pair
window contains two rich witnesses. Holding out any single pair leaves a
witness among the demonstrations. Every rich mask refutes the nine declared
competitors: floor-mass centering, fixed width three, gap compaction, largest
eight-connected component, independently centered eight-connected components,
identity, crop-only, ceiling row placement and ceiling column placement. This
provides a rotation-safe guarantee for that finite rival inventory. Any
non-`None` explicit control disables the default schedule and requests a free
individual draw; the lesson guarantee does not apply to such custom lessons.

The v3.0.1 design had narrow sampling bounds that rejected advertised endpoints,
coerced sizes, unconsumed textures/unknown knobs, a three-cell fallback, and
diagnostic names mixed into the ordinary domain. These were replaced by strict
exact controls and a separate diagnostic contract. General off-center variation
was also insufficient: all five public pairs fit mass, fixed-width, gap-removal
and component shortcuts. Broad draws alone and a single indispensable witness
were therefore replaced by canonical anchors plus two redundant rich witnesses,
so rotating that witness into the query does not hide the lesson.

## Final measured evidence and remaining limits

The retained final checks bind the source above; they are evidence for this
proposal, not an approval or training-admission claim.

| Check | Measured result | Evidence |
|---|---|---|
| Full battery | 12/12 stages green; no advisory or failed stages | [battery summary](../../../checks/after-final/checks/03909f3e98e7_after_battery_summary.json) |
| Task-local regressions | 21 tests passed; no failures, errors or skips | [JUnit](../../../checks/task-tests-final/checks/task_tests.xml) |
| Override contract | 23,940/23,940 draws accepted, 266 cases, three bands; unknown key rejected | [override results](../../../checks/after-final/checks/03909f3e98e7_after_override_results.json) |
| Profile support | 47/60 exact-profile hits; 51/60 envelope hits | [profile floor](../../../checks/after-final/checks/03909f3e98e7_after_profile_floor.json) |
| Strict canonical likeness | 147/600 inputs accepted by the narrower predicate | [semantic gate](../../../checks/after-final/checks/03909f3e98e7_after_semantic_gate.json) |
| Official coordinate witnesses | 23 Racket cases match independent translation; 22 ordinary-domain valid, one empty diagnostic | [witness verification](../../../checks/witnesses/verification.json) |
| Random lesson census | 300 lessons; 1,200 pairs, unique inputs and query rotations; zero measured ambiguity/errors | [census summary](../../../checks/lesson-census-final.summary.json) |
| Fixed-seed schedule census | 12 lessons, 48 pairs and 48 rotations, but only nine unique inputs; zero measured ambiguity/errors | [schedule summary](../../../checks/schedule-census-final.summary.json) |

The guarantee covers the nine named rivals, not all possible incorrect rules.
Rich witnesses are concentrated on 9x10 canvases and a finite mask pool; their
geometry is intentionally structured, and broader witness dimensions remain
untested. The fixed-seed schedule census contains overlapping windows, not 48
independent inputs. Free/control draws can individually agree with shortcuts;
they are lawful examples, not standalone identifiable lessons. Retain these
limits when interpreting green marginal checks or changing the schedule, mask
pool, rival definitions, or rule binding.

Imported associated notes remain in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-5cfca8dcaae45d15:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `00ad93e1c016bd4e496c67a4fa1149942f060037377f54faf1b16f5305820b04`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported on unchanged source 00ad93e1c016bd4e496c67a4fa1149942f060037377f54faf1b16f5305820b04. No issue within the checked scope: 21 portable tests pass; the initial audit lacks required declared-period evidence despite 12 identifiable lessons and 0/48 ambiguous rotations. A separate seed-0 enumeration covers all four schedule residues in all three bands: 12 lessons, 48 pairs/rotations, nine unique inputs and zero ambiguities. The first aggregate remains incomplete; this is a bounded follow-up, not universal random-support coverage. Retain source-bound evidence: `checks/audit/03909f3e98e7-combined/checks/03909f3e98e7_audit_battery_summary.json` `checks/audit/03909f3e98e7-combined/checks/03909f3e98e7_audit_commands.jsonl` `checks/audit/03909f3e98e7-combined/checks/03909f3e98e7_audit_semantic_gate.log` `checks/audit/03909f3e98e7-combined/checks/03909f3e98e7_audit_semantic_gate.receipt` `checks/audit/03909f3e98e7-combined/checks/03909f3e98e7_audit_summary.json` `checks/audit/03909f3e98e7-combined/checks/task_tests.xml` `checks/audit/03909f3e98e7-combined/progress.log` `checks/audit/03909f3e98e7/audit-summary.json` `checks/audit/03909f3e98e7/schedule-period-s0.summary.json`

### Assessment or prior finding

## 03909f3e98e7

**Conclusion: No issue found in the checked scope.** Audited generator SHA-256: `00ad93e1c016bd4e496c67a4fa1149942f060037377f54faf1b16f5305820b04`.

I ran the target's portable task tests and strict semantic audit without modifying its source. All 21 tests passed. The initial semantic command returned nonzero because strict audit policy required complete evidence for the declared four-residue lesson schedule; this was an evidence-completeness failure, not a reproduced ambiguous lesson. Its 12 sampled production lessons were identifiable and its 48 diagnostic rotations had 0 ambiguities.

I then enumerated every declared schedule residue at fixed seed 0 across easy, medium, and hard. All 12 expected lessons materialized, covering 48 pairs and 9 unique inputs; production ambiguity was 0/12 and query-rotation ambiguity was 0/48. Evidence: `checks/audit/03909f3e98e7/audit-summary.json` and `checks/audit/03909f3e98e7/schedule-period-s0.summary.json`.

This is a clean audit only for the checked contracts and fixed-seed period closure. It does not prove all random support, rejected-pair schedules, or undeclared hypotheses. The audited source remains unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `00ad93e1c016bd4e496c67a4fa1149942f060037377f54faf1b16f5305820b04`.

# Decisions for 03909f3e98e7

Assignment: `review-c787ed3190473a66`. Original generator 3.0.1, source SHA-256 `3f2ec11a46658c62379f933e9516d246f52e63a1ead7ffdf2ef96febe0ca7490`; final generator 4.0.0, source SHA-256 `00ad93e1c016bd4e496c67a4fa1149942f060037377f54faf1b16f5305820b04`.

## Authority and intended operation

The operation takes the bounding box of **all nonzero content**, keeps every value and internal gap in that rectangle, and places it on a fresh, same-size zero canvas. Its destination is `((H - crop_h) // 2, (W - crop_w) // 2)`. Disconnected content belongs to the same crop. This is not a connected-component selection task, a mass-centering task, or a gap-compression task.

The five supplied canonical pairs agree with this operation. They all have crop width 3, 4 or 5 nonzero cells, 2 or 3 foreground colors, 8-connected content, and no completely empty internal crop axis. Their profiles are: 8×9 / 4 cells / 3 foreground colors; 9×9 / 4 / 2; 10×8 / 5 / 2; 7×11 / 4 / 2; 9×10 / 5 / 3. A 4-connected restriction would reject legitimate canonical structure, so strict canonical likeness uses 8-connectivity.

R3 preserves the reference semantics. The selected bound authority differed from the canonical target by the comment `;; Crop to the non-background bounding box`. The public authority-sync proposal and apply path removed that comment from `/racket_target/target_code` only. The canonical ledger and archival raw code are unchanged. The canonical target text SHA-256 is `682457e21ca3d187d28f808a16c8b7cbcadbac72a5f34b4b4dddf084bddaaab2`; declared RULE_HASH remains `78ddb8aa1ad2`. Official Racket outputs, not Python mirrors, label the evidence.

## Input choices and alternatives

| Choice | Previous rationale or behavior | Decision, reason, and limitation |
| --- | --- | --- |
| Dimensions | The imported summary advertised random shapes at arbitrary off-center positions. The reason for silently changing exact requests is unknown. | Ordinary height and width are literal integers 6..14, honored in every difficulty band. An exact request must not silently become another request. Boundaries 6×6, 6×14, 14×6 and 14×14 have retained Racket labels. |
| Foreground cell count | Random placement could collide or constrain a requested shape and return the wrong count. | Exact 3..8 cells. Blob generation adds distinct frontier cells; scatter chooses a subset without replacement from a bounded window. This avoids rejection-loop dependence and prevents fallback from weakening controls. The window is at most 6 on each axis, so the ordinary sampler does not claim uniform support over all possible large-span placements. |
| Texture | Ordinary and deliberate-degenerate textures were mixed in the advertised axis. | `blob` and `scatter` are ordinary AXES. `already_centered` and `shape_fills_grid` remain explicit diagnostic requests in DEGENERATE_TEXTURES, outside ordinary AXES. A full-grid request with an explicit small shape_size is named incompatible. The diagnostic texture is recorded in consumed-knob provenance (R4). |
| Palette | Canonical examples use zero background and 2..3 foreground colors; 3..8 cells allow every chosen foreground color to appear. | Keep that palette domain and randomize nonzero colors. The foreground colors do not encode roles; their spatial arrangement is preserved. No color-order shortcut is relied on. |
| Placement | The old summary described any off-center position. | Draw an off-center placement that fits the crop. Centered inputs deliberately have identity output and are diagnostic rather than ordinary teaching inputs. Different rows, columns and boundary placements remain available. |
| Scalar parsing | Python coercions permitted booleans or other values to masquerade as exact numeric controls. | Reject bool, float and numeric string impostors. Seed must be an integer, sample_index a nonnegative integer, and difficulty None/easy/medium/hard. Reject unknown keys and textures. Exact dimensions and cell counts are observed from the output grid, not echoed from requested settings. |
| Canonical support | Uniformly broad generation produced only 7/60 exact profile hits, including zero in hard, in the baseline profile probe. No executable semantic contract was declared. | Include a canonical-like core draw once every four default draws. Its palette, count, dimensions and structure remain varied within the five profiles. This provides intentional support without making every example a copy of a canonical geometry. |
| Difficulty | The original details do not establish a semantic complexity ordering. | Difficulty changes free-draw size preferences, not the rule or validity of an exact override. Shared core and witness support remains present in all bands. Do not interpret the difficulty labels as measured solver difficulty. |

R1 is covered by the retained failing control tests, 3,888 joint exact-control draws inside the focused tests (9 heights × 9 widths × 6 counts × 2 textures × 4 difficulty settings), and the public override battery’s separate 23,940 accepted draws. The latter spans 266 cases × 30 seeds × 3 bands and reports zero findings. These are different probes and should not be added as a count of unique inputs.

## R2: teach the difference between the intended rule and shortcuts

Five executable `CANONICAL_SHORTCUTS` fit every usable canonical pair: `floor_mass`, `fixed_width_three`, `compact_empty_axes`, `largest_eight_component`, and `center_eight_components`. `LESSON_COMPETITORS` adds identity, crop-only output, ceiling row placement and ceiling column placement, for nine unique functions. The duplicate aliases in semantic declarations are not extra independent rivals.

The two saved `mass_and_gaps` counterexamples and official Racket outputs establish concrete differences. Their 4×5 crop has six occupied cells, empty internal axes and separated content, and is placed on a 9×10 canvas with floor destination (2,2). Uneven mass makes a centroid rule shift a row; the reflected partner reverses that discrepancy. Both examples also separate the fixed-width, component, compaction, identity, crop-only and ceiling-placement rivals. See `QUESTION_ANSWER.md`, the two task-local counterexample JSON files, and `checks/witnesses/verification.json`.

Using only those two literal stencils would be too narrow. The final witness pool enumerates distinct 6-, 7- and 8-cell masks from a small coordinate template and its reflections, retaining only masks that refute all nine rivals. There are 129 six-cell, 56 seven-cell and 12 eight-cell masks, totaling 197. Palette and off-center placement are also randomized. A reviewer independently checked all 197 masks at three placements against all nine rivals; the portable tests exercise the production path and independent coordinate oracle.

Witnesses deliberately use 9×10 canvases and 4×5 crops with three foreground colors. Those dimensions match a canonical canvas/palette profile while leaving odd margins on both axes, allowing both ceiling alternatives to be separated at once. This is a useful teaching subdistribution, not broad geometric coverage by itself. The free branch supplies the wider domain; future plausible conditional or template-recognition rivals are still a valid avenue for audit.

## Lesson assembly and query policy

`EXAMPLES_NEEDED = 3`; `LESSON_SCHEDULE_PERIOD = 4`. With no explicit non-None controls, consecutive sample indices follow **core, witness, free, witness**. Any four consecutive draws therefore contain two witnesses. Holding out any one of those four pairs leaves at least one complete refuter among the three demonstrations. This supports the production policy (first three are demonstrations, last is query) and every single-query holdout preserving the other pairs’ order, relative to the nine declared rivals.

A schedule with only one witness per four draws was rejected: holding out that one witness would remove the guarantee. Randomly hoping to draw a witness was also rejected because individual witness frequency does not establish complete-lesson support. Merely increasing the number of inference guesses would not repair missing teaching evidence.

Explicit non-None size or texture controls disable the default schedule so they can be honored exactly. The three-demonstration rotation claim does not extend automatically to arbitrary overridden curricula, to separately reseeded pairs, or to arbitrary nonconsecutive samples. Consumers needing those assemblies should use the executable lesson hook on actual labeled lessons and retain the corresponding evidence.

The lesson hook evaluates the supplied authoritative demo and query labels against rivals; a Python translation mirror is an independent diagnostic, not a source of canonical labels. The generated reference rule is still executed by the Racket runner.

## Measured results and what they establish

All counts below use final source `00ad93e1c016bd4e496c67a4fa1149942f060037377f54faf1b16f5305820b04` unless marked baseline.

| Probe | Result | Meaning and retained source |
| --- | --- | --- |
| Completed strict battery | 12 green; 0 advisory, failed, interrupted or pending | `checks/after-final/result.json`; all required stage verdicts completed. |
| Isolated focused tests | 21 passed; zero failures, errors or skips | `checks/task-tests-final/result.json`; portable source discovery via reviewer_support. |
| Profile floor | Exact: easy 14/20, medium 18/20, hard 15/20; total 47/60. Envelope: 51/60. | `checks/after-final/checks/03909f3e98e7_after_profile_floor.json`; exact means canvas dimensions plus total distinct-color count, not shape identity. |
| Stronger canonical likeness | 147/600 (easy 49/200, medium 52/200, hard 46/200) | Final semantic report; additionally matches cell count, crop dimensions, 8-connectivity and absence of empty internal axes. |
| Fixed-seed schedule | 12/12 production lessons, 48/48 rotations; zero ambiguity/errors; 9 unique inputs | `checks/schedule-census-final.json`; starts 0..3 at seed 0 in all three bands. Its source-bound schedule_coverage period is 4. |
| Larger census | 300/300 production lessons, 1,200/1,200 rotations; zero ambiguity/errors; 1,200 unique inputs | `checks/lesson-census-final.json`; 100 lessons per band, starting indices 0..99, seeds derived by the recorded public sampler recipe. |
| Official individual labels | 23/23 match independent coordinate translation; 22 ordinary-domain valid | `checks/witnesses/racket.json` and `verification.json`; includes two authored witnesses, 12 default draws, eight dimension/texture boundaries, and one all-zero diagnostic. |

The sampler’s generic `period: 6` field in census metadata is the tool’s residue-reporting bucket; the generator’s declared schedule is bound separately as period 4 in `schedule_coverage`. The actual fixed-seed receipt enumerates starts 0..3, not six starts. The full materialized receipt is retained so this distinction can be checked directly.

These finite probes eliminate the declared alternatives in the sampled lessons. They do not prove that a learner can infer only one possible program, establish performance on every seed, or approve training admission. The catalog still reports the unapproved task status.

## Reversals, environment and unresolved limits

An early assumption that the empty all-zero grid would crash the selected Racket rule was rejected after official execution returned the same grid. It remains outside the ordinary generator domain because there is no 3..8-cell object and no foreground palette; the retained diagnostic records both facts.

The first isolated task-test invocation failed its prerequisite check because pytest was only in the user site. An independent environment with pytest in its own site-packages resolved that infrastructure problem; the final runner disabled user-site imports and executed every test. The failing preflight remains under `checks/task-tests/`. No frozen baseline test was rewritten and no missing/all-skipped test result was promoted to a pass.

The original extraction encountered ENOSPC with free bytes but exhausted inodes. Work continued in a complete separate copy, preserving assignment, frozen baseline, source and existing evidence. F1 proposes a read-only diagnostic that reports both kinds of capacity; later live readings are explicitly not a reconstruction of the historical failure.

Audit A1 remains an actionable distribution finding on `341758fa9de1`; A2 remains an actionable ambiguous-lesson finding on `b47adc50b675`. Their sources were not repaired in this assignment. The post-repair solve is an exposed visible-example exercise, with prior rule exposure declared and both masked-query correctness labels unknown. There is no claim of blind evaluation or universal identifiability.
