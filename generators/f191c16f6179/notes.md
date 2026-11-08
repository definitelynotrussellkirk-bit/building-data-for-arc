# Working notes: f191c16f6179

## Current rule and domain

Version 3.0.0 pins the unchanged canonical Racket rule `f7b2de2c3ed0`.
Process colors by first occurrence in row-major input order. Fill a color's
diagonal interior only when the color occurs exactly twice, the endpoints are
45-degree aligned with span at least two, and every interior input cell is 0.
Eligibility always uses the original input; later input-order colors win at
crossing gaps. Numeric palette order is irrelevant.

The sampled domain is rectangular integer grids in 5..16 per side, colors
0..9, at most three occurrences per nonzero color, and at least one eligible
bridge. Blocked pairs, non-diagonal pairs, singleton colors and three-occurrence
groups are lawful distractors. These are generator-domain choices, not limits
on the reference rule's mathematical domain. All three canonical inputs pass.

## Decisions changed in this review

The prior notes contained only a placeholder; original author rationale is
unknown. Baseline version 2.1.0 rejected the canonical query's non-diagonal
pairs and sampled only disjoint clear bridges. The validator now recognizes
the broader endpoint/guard domain, and mixed examples teach blocked interiors,
exact-two cardinality, alignment, original-input eligibility and crossing order.
Three consecutive default demonstrations cycle through compact bridges and
both numeric orderings of a crossing. Nine executable rivals and real
disagreement witnesses describe the finite teaching contract.

The advertised inert palette, density, position and texture controls were
removed; unknown keys now fail explicitly. The remaining exact axes are
`grid_h=5..16`, `grid_w=5..16`, and `pairs=1..5`; the last counts colors occurring
exactly twice, excluding the separate three-occurrence guard. All joint tuples
are supported in every difficulty band. `None` means unset; booleans, floats,
strings and out-of-range values are errors. `observe_overrides` measures the
contract from pixels. Five is feasible on the smallest canvas; the old clear,
disjoint domain cannot realize six gap-containing diagonals on 5x5.

Bounded geometric construction replaces attempted placement with possible
underfill. Verified transformed/scaled 5x5 fallback layouts preserve exact
counts and guard witnesses. Baseline underfill was a code-level risk, not an
observed failure in the retained 1,000-seed accepted-draw probe.

## Evidence and known limits

`tests/test_repair.py` covers canonical acceptance, independent expected outputs,
actual Racket comparisons, strict overrides, joint boundaries, witnesses and
every cyclic curriculum start for seeds 0..11. `counterexamples/guard_cases.json`
contains three Racket-labelled fixtures. `workspace/probe_contract.py` is the
reusable exhaustive dimension/count checker; it checks controls, not labels.
The review return retains before/after batteries, full control and lesson
censuses, source hashes and command receipts. See SUMMARY.md for the full API.

The lesson contract supports three consecutive demonstrations followed by a
query. Arbitrary query rotations can hold out the only example refuting a
numeric-order shortcut; they are diagnostic, not promised safe. Explicit
`pairs=1..3` simplifies guard slots and does not promise the full teaching
curriculum. Geometry constraints and the fixed three-profile schedule remain
distribution restrictions. Passing the finite rival set does not prove unique
induction or measure model accuracy, and does not grant training approval.
## Current reviewer considerations

Source SHA-256: `23e1cd94475e1a4b8ad285a8cfefbae488c04cbb1d5c4e8009472345548b83f2`.

# Decisions: review-fb297ef99ed688ab

## Scope and authority

Repair only `repo/generators/f191c16f6179/`. The original assignment, two audit
draws, canonical authority and frozen baseline tests remain unchanged. The
selected baseline notes were a placeholder and associated notes were empty;
there was no retained prior audit to treat as an established conclusion.
Original rationale is unknown where it was not explained in source.

Baseline generator SHA-256:
`db793ec7a8185cae6f2810ffe5341a874c642944b027627400193c87cebb51b3`.
Final generator SHA-256:
`23e1cd94475e1a4b8ad285a8cfefbae488c04cbb1d5c4e8009472345548b83f2`.
Canonical rule pin remains `f7b2de2c3ed0`; no reference output was changed to
accommodate the generator.

## R1: Accept lawful inactive pairs

**Before:** the validator required every colored pair to be a clear diagonal.
The canonical query contains non-diagonal pairs of colors 2 and 4, so one of
three canonical inputs was rejected. The before battery reproduced this.

**Now:** require at least one eligible bridge, while allowing non-diagonal
pairs, blocked pairs, singletons and triples as inactive distractors. Eligibility
is exactly-two cardinality, 45-degree alignment, span at least two, and an empty
interior in the original input. The validator still checks rectangularity,
integer pixels, palette bounds and the declared sampler domain.

**Alternative rejected:** remove self-check or accept every grid. That would
hide malformed and empty inputs and provide no executable task-domain account.
The size limit 5..16 and occurrence cap three are deliberate sampler limits;
they are not asserted to constrain the full reference program.

**Evidence:** baseline selfcheck; final selfcheck accepts 3/3 canonical inputs
and 60/60 default draws; focused canonical/guard/malformed-input tests. Mutation
acceptance is not automatically a defect: adding a singleton or swapping colors
can preserve this task's lawfulness.

## R2: Make the exact-control API truthful

**Before:** controls advertised palette, density, position and texture variation
without implementing their ordinary values. Diagnostic textures also returned
fixed shapes. Size/count bounds varied by difficulty, unknown controls were
silently ignored, and integer coercion accepted values such as floats or
strings. These were observable API defects, not hypothetical style complaints.

**Now:** expose only `grid_h=5..16`, `grid_w=5..16`, `pairs=1..5`. Every tuple is
supported in every band. Count paired colors directly from the pixels, with a
three-occurrence guard excluded from `pairs`. `None` means unset; unsupported
keys, booleans, floats, strings and values outside the range fail explicitly.
Removed controls and the reduced pair range are an intentional version-3 API
change, documented in SUMMARY.md.

**Alternative rejected:** leave dead aliases or pretend they mean approximate
preferences. The existing interface declares exact observables. Implementing
all palette/density controls would add unnecessary coupled constraints and
make the guard curriculum less clear. Likewise, accepting up to eight pairs
on every 5x5 clear-disjoint canvas is impossible: an exhaustive search of the
18 minimal diagonal segments finds a maximum of five disjoint paths.

**Evidence:** `checks/diagnosis/f191c16f6179_probe.json`; before override logs;
focused type/boundary tests; `checks/joint-controls.json`. The full grid covers
all 12x12x5 shapes/counts, three bands, seeds 0..1 and indices 0..2, for
12,960/12,960 accepted draws. These contain 4,320 exact unique inputs; repeats
across bands are expected under fully pinned controls. This probe does not
verify labels. Actual Racket comparisons and the semantic battery do that.

## R3: Construct complete geometry with a checked fallback

**Before:** a bounded placement loop could terminate without meeting the
requested count. The retained 1,000-seed accepted 8x8/pairs=4 search did not
observe that failure, so it remains a code-level risk rather than a reproduced
baseline count failure. Impossible tuples were a separate proven problem.

**Now:** enumerate immutable diagonal geometry once per shape, use keyed
streams for geometry and palette, and construct complete layouts. If bounded
search fails, verified 5x5 layouts are transformed, scaled and translated into
the requested canvas. All outputs are checked for exact paired-color count
and meaningful active/guard structure before return. Failure raises instead
of silently weakening the sample.

**Alternative rejected:** unbounded rejection sampling, or merely increasing
the attempt count. Neither establishes termination and exact joint support.
Fixed pictures alone would also impoverish the distribution; ordinary draws
vary endpoints, lengths, dimensions and palettes before falling back.

**Evidence:** exhaustive control probe; targeted fallback check covers 216
layouts across eight transforms and scales 1, 2 and 3, for five compact counts and both comprehensive profiles at counts
four and five. The implementation
report gives the exact command and scope; this count is not 216 independent
Racket executions. Geometry caching does not cache sampled outputs.

## R4: Teach the guards and reading-order semantics

**Before:** clear disjoint diagonals let several plausible wrong rules fit
all canonical pairs. Ignoring blockers, ignoring exact-two cardinality,
testing progressively painted output, and either numeric color order all fit
3/3 canonical pairs. A correct label by itself does not make the demonstrated
lesson distinguish these rules.

**Now:** three consecutive default demonstrations include a compact core and
two comprehensive guard profiles. Each guard contains crossing eligible paths,
a blocked pair, a clear non-diagonal pair, and a triple whose third occurrence
is off the line between its clear diagonal endpoints. That third point blocks
a different color, avoiding a cardinality/blocker confound. The two crossing
profiles make opposite numeric color orders fail. At a shared gap, the later
color in original row-major input order wins; all eligibility uses the input.

**Alternative rejected:** identity-only diagnostic cases or predicates that
merely say a pattern occurred. These can miss meaningful output differences.
The nine witnesses require actual disagreement with their named pure rivals.
The five canonical-shortcut claims are checked against every canonical pair.

**Evidence:** three actual-Racket fixtures in `counterexamples/guard_cases.json`;
66 focused tests including every cyclic start for seeds 0..11; the semantic
battery's 600 input draws and real rival checks; a larger source-bound census
of 100 production lessons per band. All 300 ordered lessons materialized without
rejections, with 1,200 unique inputs and no surviving query-changing declared
rival. Seeds are the census SHA-256 recipe, requested starts 0..99 per band;
accepted pair indices are retained rather than inferred from requested starts.

## R5: Keep the lesson policy explicit

The production hook checks the actual labelled demonstrations and query. It
returns a reason when a declared rival fits every demonstration and changes
the query. `EXAMPLES_NEEDED=3` matches the default schedule. The census tested
three consecutive demonstrations and the following query, using the production
sampler. The finite rival set is not a proof against all alternative programs.

Arbitrary query rotations are not part of this promise. The extended diagnostic
found 398 ambiguous rotations among 1,200 held-out positions: easy 132/400,
medium 136/400, hard 130/400. They reuse the same 1,200 inputs, so they are not
1,200 fresh lessons. Holding out the only crossing of one numeric ordering
removes its sole refutation. The production hook reports these cases; the
ordered production verdict remains separate. No model-training accuracy was
measured. A downstream pipeline that shuffles query roles must change the
curriculum or enforce resampling before treating those lessons as admitted.

Pinned `pairs=1..3` deliberately simplifies guard profiles to honor the requested
count, and therefore does not guarantee the full default teaching curriculum.
Those are valid control draws; the hook still judges any assembled lesson.

## Shared proposal and audit disposition

F1 is an optional patch under `checks/proposals/`, not an applied shared edit.
It makes the existing production worker check declared rivals even when a
generator omits the handwritten lesson hook. Nineteen isolated tests pass on
the proposal, including a parent rerun. The selected repair has its own hook
and does not depend on accepting that proposal. This recommendation answers
`qwen9-data-value`; no model benchmark is claimed.

The assigned audit targets are unchanged and their findings are in AUDIT.md.
They are follow-up evidence, not repairs or approval decisions. Earlier failed
batteries, regressions and the missing-pytest task-test attempt are retained.
The successful isolated task-test rerun (66/66) uses a dedicated virtual environment
because the worker's sanitized Python environment ignores user-site packages.

## Final self-review

The new tests and mixed guard examples refute the nine declared shortcuts, but
compact core shapes, paired/triple counts, and the repeating three-profile
schedule remain exploitable distribution correlations that this finite review
does not prove harmless. Small-count overrides and arbitrary query rotations
remain restricted as documented; the retained rotation counterexamples make
the latter limit concrete rather than presenting correct labels as universal
lesson identifiability.

## Final handoff disposition

The independent code review found no source blocker. Its declined universal,
rotation and private-scoring claims are accepted as explicit limits, not implied
passes; the parent completed both solve episodes and the fresh patch replay.
The exact `patches/source.patch` SHA-256
`744ad4af3c8a01ffb7ce6d8b0b8cbc933e27c01bfedd83ec7baf11a15ffb26bf`
applied after `git init -q` in the fresh WORK root, every selected file matched,
and 66/66 focused tests passed there. The unrelated archival digest test also
failed on that fresh extraction before patch application; no selected-task
blocking failure remains. Exact receipts are in `checks/fresh-replay.json` and
`checks/repository-baseline-command.json`.
