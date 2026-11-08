# Review notes — 70a3d3e2c975

## Source and authority

Assignment `review-1cc94d24b58aa938`; baseline version2.0.1 SHA256 `1c53d4dde2205d05b0d1c6ce14a321eb618fb24d4b9836fcf7bf6d74074e971d`.
Final version3.0.0 SHA256 `5ee2601d9f361142e242d71d7c51c76c7e871975178f629d395c1dc436b3ba5a`.
Racket authority was not edited; normalized hash `740ca06f408e`.
No previous return was used as a repair lead; this task's associated-notes file was empty.

## Confirmed defects and repair

The baseline omitted RULE_HASH, swallowed palette/alias/density/position controls and unknown keys, advertised numerical values it rejected in some bands, and accepted any grid containing one full column of9 regardless of the task's other requirements. Its negative texture metadata could suppress validation. The old sampler generated unrelated scattered marks but did not produce canonical two-object scenes in either a192-input source-bound Racket probe or a600-input independent topology census.

Version3 uses typed overrides with exact foreground color realization. Alias conflicts and infeasible tuples carry structured errors. Validation checks actual pixels, including color types, geometry, a unique central9 column, no stray9s, a blank right half, and a nonempty source. The ordinary domain remains centered reflection on a zero background.

The default curriculum alternates connected object and scatter profiles, offset by seed parity. Core objects are grown within two row bands separated by one empty row, with independently selected colors and random connected shapes. Scatter reserves a corner singleton and includes a source color outside {2,3,4,6,7}. Three consecutive default demonstrations therefore include an example refuting each declared shortcut. Exact density/count/palette overrides may legitimately relax the teaching layout; the complete override domain is lawful but is not promised to teach all three rivals in every arbitrary lesson.

Independent code review found another flaw in an intermediate version: a feasible marks15/20 override could fail when free geometry was randomly too small. Geometry is now selected conditionally before placement. Full-left diagnostic requests use area equality, while ordinary requests use capacity at least marks. Eight regression cases cover feasible partial assignments and a fully specified impossible tuple.

## Deliberate boundaries

The rule and examples identify reflection about a central vertical9 axis. Horizontal/noncentral axes, nonzero backgrounds, prefilled targets, and 9-valued source marks are not included. On this domain, a center-index implementation is extensionally equal to reading the9 column; that distinction cannot be taught here and is not claimed as a refuted shortcut.

The strict canonical predicate checks two monochrome components of2..4 cells, two source colors, and one of the three canonical size profiles. It intentionally distinguishes the core from lawful broader scatter inputs. The topology probe independently computes connected components from pixels; it does not trust this predicate. All claims concern this finite source-bound review, not measured Qwen accuracy or universal rule identifiability.

## Evidence and next work

The return's REVIEW.md, RESULTS.json, DECISIONS.md, and checks/ hold exact commands, hashes, failures, censuses, optional audit findings, and patch-replay evidence. Tests live under tests/ and include the original107 defect cases plus three curriculum checks, eight scalar-feasibility cases, and five coverage-tool tests. The public task-test stage may skip the optional relocated-report fixture when not explicitly supplied; the return separately exercises that relocation.

Do not repin approval after an edit without appropriate new review. A later generator edit requires a new source-bound post-repair solve episode; retain the previous exposed solve as prior evidence.
## Current reviewer considerations

Source SHA-256: `5ee2601d9f361142e242d71d7c51c76c7e871975178f629d395c1dc436b3ba5a`.

# Distribution and implementation decisions

## D1 — Preserve the existing task and authority

The selected Racket implementation and all three canonical pairs agree with central vertical reflection. No evidence justified a rule change. The repaired domain remains zero background, one central full-height9 column, colors1..8 only on the left, and an empty right half. Wider variants such as shifted axes, arbitrary orientation, recolored backgrounds, or prefilled targets were rejected because they alter the lesson rather than repair the demonstrated distribution. This leaves center-position and axis-detection solvers equivalent on the chosen domain; no claim is made to distinguish them.

## D2 — Add the missing topology while retaining useful scatter

Canonical inputs contain exactly two four-connected monochrome source components, no singletons, and two source colors; their component sizes are3+3,4+3,4+2. Baseline scatter has useful edge/singleton/color variation, but the Racket-bound probe found0/192 canonical topology matches, and an independent600-input census found0/600. Four of the192 baseline draws matched a canonical height/width/palette profile despite failing topology. Replacing scatter wholesale with small connected motifs would remove useful counterexamples; retaining only scatter would leave the canonical structural pattern effectively uncovered.

The selected design mixes one connected-object profile with one scattered profile in alternating sample indices, offset by seed parity. Object scenes use two separate row bands, independently chosen colors, and connected random growth rather than fixed canonical templates. They have6..7 cells over two components. Scatter spans height5..14, half-width2..8, marks1..20, and foreground cardinalities1..8 subject to physical capacity and palette availability. The split is an explicit curriculum choice, not a measured optimum for Qwen. No model training or accuracy evaluation was performed.

The object placement imposes vertical separation; this limits object-layout breadth. Scatter remains available and allows adjacent/mixed components. A future extension could randomize component separation direction if a concrete learning need justifies it, with a fresh source-bound review.

## D3 — Teach complete lessons, not just individual witnesses

Three concrete rivals fit all canonical pairs: skip singleton source components; skip source column0; copy only canonical colors{2,3,4,6,7}. The ordinary scatter profile guarantees a corner singleton, a source-edge cell, and a color from{1,5,8}; each3-demo default window includes scatter. The tool dynamically reads the actual rival declarations, verifies their canonical fit, and rotates every input through the query position. The seed offset also ensures fixed-length lessons can query both object and scatter families.

The production census uses the actual sampler with100 lessons per band,3 demos and1 query; the task tool uses16 seeds per band and every rotation of a4-input cycle. These are distinct populations. Overlapping cyclic windows are not independent inputs. The declarations occur in three namespaces, but represent only three distinct competitors. Neither finite census establishes universal induction. Exact overrides can intentionally select a monochrome warm palette or a dense scene that does not satisfy all default teaching witnesses; no lesson-identifiability guarantee is made for arbitrary override combinations.

## D4 — Make every accepted exact control observable

Foreground palette cardinality counts source colors only, excluding0 and9. Every selected source color is placed at least once; sampling with replacement alone cannot fulfill an exact cardinality promise. `n_distinct_colors` remains a checked compatibility alias, while AXES advertises only the independent palette_size control. Conflicting aliases raise an explicit structured ValueError. Palette families constrain the eligible colors; requests larger than a forced family are rejected. Unknown keys, coercible strings/floats/bools, explicitNone, and out-of-range integers are rejected.

`texture` retains its existing palette-family alias for normal scenes. The former single-valued density/position controls are kept as validated diagnostic compatibility selectors, not counted as independent variation. Negative fixtures are outside the normal advertised texture domain; full_left is a declared lawful diagnostic. Empty-left/no-axis inputs are invalid even if metadata names a negative texture.

## D5 — Condition free geometry on the requested count

An intermediate version honestly counted marks but could draw a small free canvas, then reject an otherwise feasible scalar override. Independent review reproduced marks15/20 with seed2/index1. The final sampler chooses unpinned dimensions satisfying capacity before placement. If full_left and marks are both requested, it chooses dimensions whose product equals marks. Fully pinned impossible tuples retain explicit incompatibility errors. Eight focused regression cases keep this edge outside dependence on a particular fixed seed/index matrix.

## D6 — Difficulty changes sampling weights

All bands retain the same exact override domain. Easy favors lower mark counts, hard favors larger counts, and core draws retain canonical-size support. An intermediate version had identical outputs across bands and was rejected by the existing defect linter. The repaired weighting was measured independently across256 inputs per band; the retained report identifies the exact prior source bytes. The final geometry-only fix leaves those unoverridden draws unchanged; fresh final-source censuses are retained separately rather than relabeling old evidence.

## D7 — Verification and provenance

Before evidence, intermediate failures, the final battery, focused task tests, production census, cyclic probe, source-bound solves, audits, and fresh-packet patch replay are retained with commands and hashes. The public isolated task-test stage initially lacked user-site pytest; a separate local environment with the declared test dependency resolved that environment problem without shared-source edits. Optional relocation-fixture skips in normal task tests are reported separately from the explicitly exercised relocation test.

All selected-task source changes are delivered through the generated patch. Audit-only targets remain unchanged. Training approval and admission are maintainer/catalog actions; this reviewer does not mutate them.

## Native parametric review — assignment `review-691290efe138b129`

A task-local native family was added without changing the approved production
generator or canonical puzzle data. `copy_policy=all_colors` returns the exact
canonical Racket source. `copy_policy=rarest_color` first scans the source half,
counts its colors, and reflects only the unique least-frequent color. The sampler
is setting-neutral and prefix-stable, supports 2–6 demonstrations and 1–4
queries, and ends with a substantive 30×29 case; width 30 is impossible under
the task's required odd-width, single-center-axis grammar.

The complete staged task suite passed 182 tests with one optional skip. A bounded
protected-Racket audit covered 12 episodes, 92 selected labels, 276 executions,
nine declared rivals, and 48 query-separation checks with zero findings. Native
qualification passed both settings on seeds 0 and 17, and the source-bound
counterfactual replay confirmed that replacing the all-color eligible set with
the rarest-only intermediate changes the final output. Sixteen saved one-query
public projections passed structural and leakage checks. These finite checks do
not prove universal identifiability; exact-source owner acceptance and training
admission remain separate pending actions.
