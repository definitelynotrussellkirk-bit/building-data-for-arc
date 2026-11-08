# Working notes: a7e26e20850c

## Current rule and authority

The top row is a zero-separated legend. Each run length denotes an object size and the run color is the replacement color for every gray (`5`) body object of that size. The canonical Racket rule remains unchanged and is pinned by `RULE_HASH = "704fe040d74c"`; generation never supplies labels.

## Repaired distribution (version 2.0.0)

- Every generated input has exactly three pairwise 8-separated, 4-connected gray objects, matching all three canonical inputs. The imported 1.2.1 generator instead emitted four objects.
- Public exact axes are now only `grid_h=7..13`, `grid_w=12..18`, and `n_sizes=2..4`. Every compatible scalar combination is observable through `observe_overrides`; `n_sizes=4` with `grid_w<17` is explicitly incompatible. Unknown keys, booleans, floats, strings, invalid difficulties, and negative sample indices are rejected.
- Legend sizes are unique members of `{2,3,4,5}` and colors are distinct nonzero/non-gray colors. Body object sizes must occur in the legend. Placement is constructive through three separated width slots; it has no retry cap or silent shortening.
- Shape templates are expanded through dihedral orientations. Difficulty changes deterministic height/width and layout draws without changing the rule.
- The period-4 teaching profile is `2,4,3,4` legend entries. Both four-entry positions use the fourth run, so holding out any one of the five labelled pairs still leaves a demonstration that refutes the declared `first_three_legend_entries` rival.
- Three-entry samples rotate through canonical dimension anchors `(10,14)`, `(11,15)`, and `(12,16)` so each difficulty band reaches exact canonical profile support without collapsing the broader distribution.

## Reversed choices

Imported 1.2.1 advertised controls that were ignored, silently widened narrow grids, accepted unknown overrides, allowed four body objects, and used a presence-only validator. Those choices were replaced because the baseline battery reproduced 65 defect-lint warnings, exact-control failures, a missing rule pin, and no executable semantic contract. Evidence is retained under `checks/before/` and `checks/baseline-console.log`.

## Semantic evidence and limits

The canonical pairs are also consistent with the wrong rule “ignore legend entries after the third.” `counterexamples/first-three-legend.json` is a minimum 7x17 lawful witness where the fourth run has size five and is used by a body object. The period census at fixed seed 0 covered all four declared starts in easy/medium/hard (12 lessons, 60 held-out-query rotations, no ambiguity). A wider production-sampler census covered 300 lessons, 1,500 rotations, and 1,500 unique inputs with no materialization, scoring, hook, or ambiguity errors. These are finite checks against one declared canonical-fitting rival plus shared generic rivals, not a proof of unique identifiability against every possible hypothesis or every seed.

## Reusable tooling

`workspace/reference_probe.py` independently parses legends and objects, checks canonical labels, audits deterministic samples and observable axes, and optionally compares with the real Racket authority. It deliberately does not import the generator's private semantic helper as its oracle.

## Final evidence

- Generator SHA-256: `e18c808cfb16b44c4eee6055881f9b2c4a56a6524244ea683819af395dc5b908`.
- Final battery: 12/12 green in `checks/after-final/checks/a7e26e20850c_after_battery_summary.json`.
- Task-local tests: 57/57 passed in `checks/task-tests-final/checks/task_tests.xml`.
- Independent probe: 400/400 lawful deterministic distinct samples, 19/19 Racket parity cases in `checks/reference-probe.json`.
- Canonical authority files were not edited.
## Current reviewer considerations

Source SHA-256: `e18c808cfb16b44c4eee6055881f9b2c4a56a6524244ea683819af395dc5b908`.

# Decisions for `a7e26e20850c`

## D1 — Keep the Racket authority unchanged

**Choice.** Preserve the canonical transformation and pin it with `RULE_HASH = "704fe040d74c"`.

**Reason.** All canonical labels and independent Racket probes agree with the intended size-to-color mapping. The defects were in generated inputs, controls, validation, and teaching support—not the rule.

**Rejected alternative.** Rewriting the Racket rule to match the imported generator's looser manifold would hide generator defects and alter accepted canonical semantics.

**Probe/failure mode.** Rule smoke and authority sync are green in the final battery; `workspace/reference_probe.py --racket` produced 19/19 parity matches. Archival text divergence remains reported by authority sync but selected execution parity is green.

## D2 — Generate exactly three body objects

**Choice.** Every instance contains exactly three 4-connected gray objects.

**Reason.** Each of the three canonical inputs has three objects; the imported generator's four-object default created an unnecessary distribution shift. Three objects also preserve enough variation through repeated sizes when only two legend entries exist.

**Rejected alternatives.** Keeping four objects would retain the observed canonical mismatch. Making object count another public axis would widen the task without canonical evidence and complicate lesson comparability.

**Probe/failure mode.** The independent 400-sample audit found zero count mismatches. `self_check` rejects both fewer and more than three objects.

## D3 — Use constructive separated slots, not capped retries

**Choice.** Enumerate three width slots of at least three columns, separated by one or two blank columns, and place one object in each.

**Reason.** Every supported shape fits a 3x3 box. Slot separation makes 8-neighborhood isolation structural, eliminates stochastic placement failure, and supports the minimum 7x12 compatible canvas.

**Rejected alternative.** Retry loops can silently shorten the requested object set, as independently reproduced in audit target `508ae94c035c`.

**Probe/failure mode.** Exhaustive task tests cover every compatible profile on minimum canvases. A future larger shape template must either fit the slot contract or make the supported width bounds explicit.

## D4 — Narrow public axes to observable exact controls

**Choice.** Expose only `grid_h`, `grid_w`, and `n_sizes`, validate exact integer values, reject unknown keys, and provide `observe_overrides`.

**Reason.** The imported metadata named controls that did not affect generation. Exact controls are useful only when returned pixels can verify them.

**Rejected alternatives.** Cosmetic palette/density/texture axes were not retained because they either described fixed grammar or would not be independently observable. Silent grid widening was rejected because it falsifies caller intent.

**Compatibility.** Four distinct sizes 2,3,4,5 plus three separators need 17 columns. Therefore `n_sizes=4` with widths 12–16 is declared incompatible. A narrow width without an explicit `n_sizes` override adapts the unspecified schedule count to three rather than rejecting a valid scalar request.

## D5 — Preserve the canonical envelope while broadening shapes

**Choice.** Legend sizes are unique values from 2–5, colors are distinct members of 1–9 excluding gray 5, dimensions are 7–13 by 12–18, and object templates use all dihedral orientations of several connected seeds.

**Reason.** This keeps run lengths inside the canonical semantic envelope while adding position, orientation, shape, size-use, palette, and dimension diversity. No new output operation is introduced.

**Rejected alternatives.** Sizes above five have no canonical support. Arbitrary polyomino enumeration adds complexity without evidence that it improves the lesson. Fixed gray rectangles would make object extraction and size mapping too stereotyped.

**Probe/failure mode.** The 400-sample probe observed all size counts 2–4, object sizes 2–5, and a broad dimension set. Semantic equivalence classes are not exhaustively measured; exact-grid uniqueness is only a lower-level diversity check.

## D6 — Anchor three-entry samples to canonical profiles

**Choice.** Three-entry scheduled samples rotate among dimensions `(10,14)`, `(11,15)`, and `(12,16)` across seed/start/band, while other profiles draw the full supported envelope.

**Reason.** The strict profile floor requires exact canonical support in every difficulty band. Anchoring one schedule profile satisfies that without collapsing all lessons to canonical dimensions.

**Rejected alternative.** Rejection-sampling until a canonical profile appears is less transparent and can bias or fail unpredictably.

**Probe/failure mode.** Final profile floor is green. The anchors deliberately constrain one quarter of default starts; other starts supply broader width/height support.

## D7 — Teach and test the fourth legend entry

**Choice.** Declare `first_three_legend_entries` as a canonical-fitting rival. Use period-4 profiles `two_sizes`, `four_sizes_a`, `three_sizes`, `four_sizes_b`, and ensure every four-entry input uses the fourth run in at least one body object.

**Reason.** All three canonical examples have at most three legend runs, so the shortcut fits them. One four-entry witness per lesson would fail when that pair becomes the query; two witnesses ensure every one-of-five holdout leaves a refuting demonstration.

**Rejected alternatives.** Merely increasing four-entry frequency does not guarantee lesson-level support. A single fixed witness position only protects ordered production. Forcing every legend entry to be used would contradict canonical examples that permit an unused entry.

**Probe/failure mode.** The minimum counterexample is retained and tested. Fixed-seed period enumeration passed 60/60 rotations; a 300-lesson random census passed 1,500/1,500. These results cover one declared canonical-fitting rival and shared generic rivals, not all possible rules.

## D8 — Make validation describe the true manifold

**Choice.** `self_check` verifies rectangular literal ARC colors, dimension bounds, blank separator row, 2–4 zero-separated unique-length/unique-color legend runs, body palette, exactly three 4-connected objects, legend membership of each object size, and pairwise 8-separation.

**Reason.** A generator validator is useful only if it rejects inputs for which advertised semantics or object parsing are ambiguous.

**Rejected alternative.** Presence-only checks let malformed examples enter training and can make semantic probes certify the wrong domain.

**Probe/failure mode.** Mutation tests independently break each major invariant. The validator intentionally does not require all legend entries to be used because canonical data includes an unused legend size.

## D9 — Add an independent authoring probe

**Choice.** Build `workspace/reference_probe.py` with its own legend parser, component extractor, Python oracle, deterministic sampling audit, and optional real-Racket comparison.

**Reason.** Reusing generator-private helpers would let one bug validate itself. The CLI gives future agents a small, reproducible source-bound audit instead of requiring the whole battery for every iteration.

**Rejected alternative.** A Python fallback masquerading as Racket parity was rejected; `--racket` fails closed if the authority cannot run.

**Limit.** The default finite sample is not exhaustive. Exact commands and hashes must accompany any broader claim.
