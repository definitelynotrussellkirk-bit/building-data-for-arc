# Working notes: 7a37505e7bd0

## Current review: review-3666fc75a9008d52

### Production repair and authority

The selected version remains `3.2.0`. The incoming source accepted booleans as
seeds/indices/counts, negative sample indices, invalid difficulty values, and
coercible noninteger color-count overrides. The new entry checks require exact
Python integers for seed/index (index nonnegative; signed seeds remain valid),
`None` or a literal supported difficulty string, and shared `draw_int_strict`
validation for integer `color_count` in 1..5. `None` still means no override.
No RNG key, valid draw path, palette placement, frequency template or layout
choice changed. `LESSON_SCHEDULE_PERIOD = 5` declares a semantic-observable
period; it does not claim that complete grid bytes repeat every five samples.

Final generator SHA-256:
`9e1b827924f2445dc0f57d593c04b3bb55dc0a47649ef03c276648df90d980d3`.
Original generator SHA-256:
`442a6f512121019d8b031d37a03d6e9c2f5245794610e22d91fd626d843d6151`.
Canonical/base/archival Racket authority is unchanged (`RULE_HASH=f6f5abe21d6a`).

`tests/test_controls_7a37505e7bd0.py` first produced 32 failed / 22 passed
assertions against the original source, then 54/54 passes after repair.
`workspace/probe_controls.py` compares the supplied original ZIP with current
source: all 1,680 valid calls produced identical outputs; eight exact malformed
call witnesses changed from acceptance to rejection. Inputs/results are retained
in `counterexamples/invalid-controls.json` and the return's
`checks/controls-compatibility.json`. Earlier missing-pytest and dependency
installation failures remain infrastructure receipts, not generator failures.

The original battery was 11/12, failing only strict-scalar defect lint; the
repaired battery is 12/12, including required query rotations. The randomized
lesson census materialized 300 lessons / 1,800 pairs and checked 1,800 rotations,
with no measured ambiguity, hook or scoring error against the tested rivals.
The separate period census covers all five start residues in three bands at
seed 0: 15 lessons / 90 rotations, likewise clear. Each complete lesson uses
six consecutive materialized pairs, five demonstrations and one held-out query.
Removing one pair can leave only four distinct color-count values. This corrects
the older note's mistaken five-pair/four-demo description. Neither census proves
all-seed support or unique induction against every possible rule.

### Question answer and preserved teaching limitation

The plausible canonical-fitting rival counts only nonzero colors: all seven
canonical demonstrations and the labelled query contain no zero. Ordinary
`generate(0, 1, difficulty="medium")` emits `[[5,0,5],[0,0,0],[5,5,0]]`.
The actual canonical Racket output is 6x6, while the rival yields identity 3x3.
The bounded probe found 72 such counterexamples among 180 generated cases;
zero-containing count-2 and count-4 samples provide recurring teaching evidence.
Exact grids, labels and source/rule hashes are in
`counterexamples/canonical-shortcut-witnesses.json` and the return's
`checks/canonical-review/` probes and public-apply receipts.

A different rival, identity for monochrome and otherwise scale by
`7 - modal_frequency`, fits all 180 measured generated examples because the
fixed templates correlate modal frequency with the required factor. It fails
canonical train pair 0, whose three colors each occur three times: the true
factor is 3, whereas this rival uses 4. It is therefore not a canonical-fitting
rival or an emitted-label defect. This round preserves the established profile
and valid-call output sequence rather than making an additional distribution
change. A future deliberately sampled, legal unbalanced count-2 profile could
break this shortcut; that change and its profile/lesson effects are untested.

### Parametric extension: runnable proposal, separate from production

`workspace/parametric/prototype.py` implements two episode-fixed parameters:
counting all colors versus nonzero colors, and expansion along both axes,
rows only, or columns only. The six combinations have live Racket programs;
canonical `all_colors/both` uses the exact unchanged authority text. Seed-based
selection happens once per complete episode, and all labels come from actual
Racket execution with exact program/input cache keys. The prototype keeps the
3x3 lawful input domain, one-color identity behavior and original palette roles.
It rejects incomplete lessons whose demonstrations cannot refute another
parameter setting. Public challenges contain five labelled demos and one
input-only query; private receipts hold rules, parameters and query labels.

The first complete matrix measured six settings x three bands x four seeds x
two starts: 144 episodes, 864 labelled pairs and 864 query rotations. All tested
parameter rivals were refuted, eight canonical labels matched, and one retained
lawful common input produced six distinct outputs. An intentionally ambiguous
zero-free demonstration set is labelled a teaching negative control; it is not
a natural failed solve, and the prototype creates zero solve attempts.

Independent code review found that the first matrix's numbered public filenames
revealed the hidden parameter via suffix modulo six. The revised exporter uses
the full SHA-256 of exact public JSON bytes for public filenames; numeric
order and its parameter mapping remain private. Identical public payloads may
share a file. The regression and revised matrix are retained separately; the
original leaking exports and source bytes remain reproducible evidence. The
current matrix, exact source hashes, code-review closure, test totals and fresh
patch replay are indexed in `REVIEW.md`, `RESULTS.json` and
`checks/parametric/`. Variant programs remain proposed authoring material;
this review does not approve variants or admit training data.

### Solve and audit scope

The independently drawn blind task `ad4e2cd6e3bc` was solved before opening the
selected generator/rule: one natural attempt, 3/3 visible matches, earlier
exposure declared no. The separate selected-task solve uses the final generator
hash above: one natural attempt, 5/5 visible matches, earlier repair exposure
declared yes. Execution completed for both; hidden correctness remains unknown.
Frozen notes are work logs, not token-level model traces.

Audits `635001043e0f` and `446c18f3b7f4` are findings only. Their exact source-bound
counterexamples and command receipts live in the return's `AUDIT.md` and
`checks/audit/`; no audited source or shared file changed. The broad root suite
reported 19 failed / 995 passed / 3 skipped, with 18 subtest passes; its unchanged
component failures are retained and classified. No pristine-baseline broad
rerun was performed, so those failures are not all proved pre-existing.
Focused task checks and fresh-replay results are reported separately.

## Retained historical rationale

The following prior-round account is preserved as context, including its older
source hashes and evidence paths. Its old check counts are not current results.
The one lesson-assembly arithmetic error is corrected as explained above.

## Prior review: review-0bbe1811e19d14ca (historical evidence)

The imported v3 generator already had the correct canonical-profile 3×3 shape
policy, a five-slot 1..5 distinct-color schedule, and mandatory zero-containing
multicolor examples. The retained earlier review
`external-local-random:b3647efbc34d` established those choices and synchronized
`RULE_HASH`; its notes remain in `evidence/associated_notes.jsonl`.

This review found two remaining issues.

1. `authority_sync` required the selected base `target_code` to be byte-normalized
   exactly like the canonical one-line rule. The multiline program was
   semantically identical and passed execution, so only its formatting was
   synchronized; archival `raw_code` and canonical authority were not changed.
2. Generated multicolor grids excluded colors 3 and 8 while generated identity
   grids used only 3 or 8. The wrong rule “return identity whenever 3 or 8 is
   present; otherwise use the true rule” therefore fit every old generated
   lesson. Canonical multicolor pairs already refuted it, revealing a mismatch
   between canonical evidence and generated teaching evidence.

The repair adds exactly two multicolor 3/8 witnesses to each five-demo lesson.
Their distinct-color counts rotate across `(3,4)`, `(4,5)`, and `(3,5)` by seed,
so holding out any one pair leaves at least one witness. Witness colors occupy
non-modal labels. Counts 1 and 2 are deliberately excluded: any two-color 3/8
witness would make one generic monochrome-collapse mutation a lawful canonical
identity input, defeating `defect_lint` for structural reasons rather than
teaching quality.

The lesson hook checks lawful labels, a zero witness, a multicolor 3/8 witness,
and each named executable rival. Exact 1..5 schedule coverage remains a separate
generator regression rather than a hook requirement; requiring every count in
the remaining demos caused false hook warnings when any pair became the query.

Final evidence:

- full required-rotation battery: 12/12 green, `checks/after-final/`;
- portable task tests: 20/20 collected passes (10 unique source tests mirrored
  twice by the task-test stage), `checks/task-tests-final/`;
- lesson census: 300/300 materialized, 1,800 pairs, 1,800 query rotations,
  zero ambiguity/hook/scoring errors, `checks/lesson-census-final.json`;
- post-repair visible solve: 5/5 examples in one revision, prior exposure
  declared yes, `solve/summary.json`.

Known limits: declared-rival tests are finite; they do not prove unique induction
against all possible rules. The fixed five-slot schedule is intentional and is
not advertised as arbitrary-order training support beyond the tested query
rotations.
## Prior reviewer considerations (historical source)

Source SHA-256: `442a6f512121019d8b031d37a03d6e9c2f5245794610e22d91fd626d843d6151`.

# Decisions — 7a37505e7bd0

## D1 — Preserve the authoritative transformation

**Choice.** Keep the canonical rule and `RULE_HASH=f6f5abe21d6a`; change only the
selected base `target_code` spelling to the exact canonical one-line text.

**Why.** Canonical, archival, and generator-mirror behavior already agreed. The
baseline failure was exact source synchronization, not wrong semantics.

**Rejected alternative.** Rewriting or simplifying canonical/archival Racket.
That would introduce authority risk without repairing any behavioral defect.

**Probe/failure mode.** Baseline `authority_sync` failed; the focused sync stage
and final battery pass. Archival `raw_code` is preserved.

## D2 — Retain canonical 3×3 profiles and the 1..5 schedule

**Choice.** Keep fixed 3×3 inputs and one occurrence of each color count 1..5 in
every five consecutive samples.

**Why.** The earlier retained review rejected broad texture/noise sampling in
favor of canonical-profile frequency templates. The scale factor is the task's
semantic axis; larger canvases add nuisance breadth rather than missing rule
evidence.

**Rejected alternative.** Broadening shapes or randomizing the number of demos.
That would weaken the established canonical-profile guarantee and make lesson
coverage harder to reason about.

**Limit.** A fixed period can leak ordering if sample indices are exposed.
Exported lessons expose grids, not indices; the census tests actual sampled
lessons and every labelled query rotation, not arbitrary reorderings.

## D3 — Add two rotating multicolor 3/8 witnesses

**Choice.** In each five-demo lesson, place 3 or 8 in exactly two multicolor
samples. Rotate the count pair among `(3,4)`, `(4,5)`, and `(3,5)` by seed.

**Why.** The old distribution supported the false rule “3/8 means identity.” A
single witness fixed production order but disappeared when that witness became
the query. Two witnesses leave one refuting demo under any one-pair holdout.

**Rejected alternatives.** One witness (rotation defect); always the same count
(profile cue); or injecting 3/8 indiscriminately (defect-lint collisions).

**Evidence.** Red/green task tests under `checks/task-tests-palette-*` and
`checks/task-tests-rotation-*`; final census has 0/1,800 ambiguous rotations.

## D4 — Restrict witness palettes to linter-safe non-modal roles

**Choice.** Use 3/8 only on non-modal labels; for count 3 retain a lower-valued
non-modal foreground, for count 4 use zero on another non-modal label, and for
count 5 include both 1 and 2 among tied non-modal labels.

**Why.** `defect_lint` probes all-modal and minimum-foreground monochrome
collapses. If the witness becomes either selected color, the collapse may be a
lawful canonical 3/8 identity input and cannot correctly be rejected by
`self_check`.

**Rejected alternative.** A count-2 3/8 witness. With only two colors, one of the
generic collapse probes necessarily selects 3/8, so the mutated grid is a lawful
identity case. This is structurally impossible to avoid without changing the
shared mutation contract.

**Evidence.** Failed intermediate after battery and focused red tests are
retained; final `defect_lint` and 20/20 task tests pass.

## D5 — Separate production schedule coverage from lesson rival checks

**Choice.** Test exact 1..5 coverage as a generator invariant. In
`lesson_identifiable`, validate lawful pairs, zero and 3/8 witnesses, and execute
named competitors against the actual demos/query.

**Why.** Under query rotation, six materialized pairs become five demos; requiring
all five counts in those demos created false hook warnings even when every named
rival was refuted. Direct competitor evaluation is the relevant teaching test.

**Rejected alternative.** Treat every hook warning as a rotation failure while
retaining the impossible all-five-count condition.

**Limit.** Named competitors are finite and do not prove unique induction against
undeclared rules.

## D6 — Make tests portable

**Choice.** Replace the legacy staged `scripts.*` helper import with
`reviewer_support.find_root(__file__)` and `canonical_pairs`.

**Why.** The test now works in source, staged, and fresh-replay layouts without a
fixed `parents[...]` guess or compatibility shim.

**Observed tooling issue.** The task-test stage mirrors the same file into two
collection roots, so 10 source tests appear as 20 executions. This is reported as
F3 rather than misrepresented as 20 unique tests.

## D7 — Leave audit targets unchanged

`f6b13494be37` and `b9d914a60205` were adversarial review targets only. Their
reproduced defects are documented in `AUDIT.md` and source-bound evidence, but no
source edits were made outside the assigned generator/base target.
## Current reviewer considerations

Source SHA-256: `9e1b827924f2445dc0f57d593c04b3bb55dc0a47649ef03c276648df90d980d3`.

# Decisions — review-3666fc75a9008d52

## D1 — Reject malformed controls before drawing; preserve valid outputs

The incoming generator silently accepted booleans and coercible numeric
strings/floats in scalar controls, negative sample indices, and unsupported
difficulty values. The original battery's strict-scalar defect lint produced
54 warnings. Focused regressions then gave **32 failures and 22 passes** against
the original source. The repair requires exact Python integer seed/index values,
a nonnegative index, supported string difficulties or `None`, and shared
`draw_int_strict` for `color_count` in 1..5. Signed integer seeds and the
`None` no-override sentinel remain valid.

The validation is intentionally narrow. It leaves RNG keys, shape, palettes,
frequency templates, transformation and layout choices intact. A task-local
replayable comparison against the original ZIP found **1,680/1,680 identical
valid outputs** across six seeds, ten indices, four difficulty choices and
seven count-control choices. Eight exact before/after malformed-call witnesses
are retained. Validation by coercion was rejected because it obscures caller
errors and made documented exact controls unreliable.

Evidence: `checks/controls-red-tests.log`, `checks/controls-green.log`,
`checks/controls-compatibility.json`; source tests and
`workspace/probe_controls.py` in the task patch. The initial missing-pytest and
restricted-network dependency failures are retained as infrastructure failures.

## D2 — Preserve version, canonical authority and palette roles

`VERSION=3.2.0`, canonical/base/archival Racket source and
`RULE_HASH=f6f5abe21d6a` are unchanged. This fixes the call contract without
changing the task or claiming a new approved distribution. The true transform
expands a lawful 3x3 input by its distinct-color count, including zero.

Existing deliberate sampling choices remain: counts 1..5, canonical-profile
templates, zero at counts 2 and 4, and two rotating multicolor 3/8 witnesses at
selected counts 3..5. Colors 3 and 8 stay in the established non-modal roles;
there is no indiscriminate recoloring of fixed identity cases. These inherited
choices are explained in the historical section of current `notes.md`.

The final profile-floor check accepted **8/8 canonical inputs** and found
**60/60 exact-profile generated hits**, with no envelope-only fallback, crash
or opt-out. Exact canonical execution agreed on all eight stored labels.
Evidence: `checks/after/checks/7a37505e7bd0_after_profile_floor.json` and
`checks/canonical-review/`.

## D3 — Declare the existing semantic period honestly

`LESSON_SCHEDULE_PERIOD = 5` describes the periodic semantic observations used
by the lesson contract. Whole grid bytes need not repeat. The count, zero role,
witness-count selection and frequency profile repeat by residue at a fixed
seed, while layout/palette draw details can vary.

Six consecutive examples form five demonstrations and one held-out query.
The default production query is last; the diagnostic also makes each of the
six examples the query while preserving the remaining demonstration order.
This corrects an earlier note that said five examples became four demos.
Five remaining demos can nevertheless contain only four distinct count values.

The random census checked **300 complete lessons, 1,800 pairs and 1,800 query
rotations**. The separate fixed-seed schedule census enumerated **all five
start residues x three bands**, for **15 lessons and 90 rotations** at seed 0.
Both had zero measured ambiguity, hook warnings or scoring errors. The after
battery additionally required its rotation smoke test: **12 lessons and 72
rotations** passed. The seed-0 enumeration is complete only for the declared
residues at that seed; it is not all-seed certification.

Evidence: `checks/lesson-census.summary.json`, `checks/schedule-census.json`,
and `checks/after/checks/7a37505e7bd0_after_semantic_gate.json`. The full random
census is retained losslessly in `checks/compressed-evidence/`; restoration is
documented in `checks/EVIDENCE-TRANSPORT.md`.

## D4 — Keep a concrete teaching gap visible

The canonical-fitting nonzero-count rival is already refuted by normal
generation: 72 of 180 probed cases are counterexamples. The separate
`7 - modal_frequency` rival fits all 180 generated cases but fails canonical
training pair 0. This is a preserved histogram restriction, not an emitted
label defect. It survives changes of palette and geometry because they leave
frequencies unchanged.

An occasional lawful `[3,6]` two-color histogram is a concrete future option.
It was not added: that would change the established sampled distribution,
invalidate exact valid-call compatibility and require a separate assessment
of canonical profile and lesson behavior. The review prioritizes the exact
control repair and a runnable parametric proposal. This decision does not
dismiss the gap or claim the present tests establish unique induction.

Evidence: `QUESTION_ANSWER.md` and the exact Racket outputs in
`checks/canonical-review/`. This is the highest-priority shared diagnostic
recommendation in `FEEDBACK_TO_CODEX.md`.

## D5 — Two bounded, episode-fixed semantic parameters

The task supports a useful prototype with counting policy
`all_colors/nonzero_colors` and expansion axis `both/rows/columns`. All six
settings preserve the same object correspondence: each input cell contributes
a rectangular region of its own color. The semantic changes are explicit and
small enough to compare on identical lawful inputs. Shape and arbitrary palette
noise were rejected as the main extension because they add nuisance variation
without changing what operation must be inferred.

The canonical `all_colors/both` setting uses exact canonical Racket text. Each
alternative is a closed Racket program, materialized under
`workspace/parametric/rules/`. The factor is at least one. The input grammar
stays 3x3 with 1..5 colors, existing palette rules and no all-zero input.
Parameters are selected once from the episode seed or supplied explicitly,
then held fixed across all six labelled pairs. They do not drift per sample.

Labels come from the live Racket bridge and are cached only by exact program
and input hashes. The report records cache reuse separately from actual grid
applications. An episode is rejected if its five demos fail to distinguish
the intended setting from another declared setting. No Python mirror supplies
variant outputs. A lawful common input produces six different output shapes,
so the parameter choices are not cosmetic.

The matrix covers six settings, three bands, seeds 0/1/2/17 and starts 0/3:
144 complete episodes and 864 rotations. The canonical parity, full labels,
program hashes, rival disagreements and negative control are retained. Final
post-review evidence and exact counts are in `checks/parametric/final-v2/`.
The earlier matrix remains losslessly available and is not relabelled as final.
This proposal is not production parametric support, training admission or
approval of alternative authorities.

## D6 — Fix public export metadata as well as JSON fields

Independent review showed that the first matrix's sequential public filename
suffix modulo six predicted all 144 hidden settings. Clean JSON bodies alone
were insufficient when filenames were challenge-visible. The revised export
names public files by the full SHA-256 of the exact canonical public JSON bytes.
The identifier therefore contains only information derivable from the public
body, independent of private episode numbering or metadata. Identical public
bodies share a file; private records still retain one receipt per episode.

The public surface is an individual content-addressed file containing only
train input/output pairs and an input-only query. Matrix order, parameter
mapping, full programs, source receipts and query labels remain private
authoring evidence. This does not provide general resistance to arbitrary
side channels or exposure of the private manifest. The regression changes
private IDs while holding public content fixed and checks exact content hashes.
Original source and leaking exports are retained for honest review provenance.

Evidence: `checks/code-review/`, `checks/parametric/v2-filename-red.log`, revised
test receipts and the `final-v2` report. The single-setting CLI uses the same
export boundary as the matrix.

## D7 — Retain genuine solve history and intentional negatives separately

The blind solve used task `ad4e2cd6e3bc`, before repair-source exposure, and
passed 3/3 visible examples in one natural attempt. The post-repair solve
used the final selected generator and passed 5/5 visible examples in one
natural attempt; earlier repair exposure was explicitly declared. Both
executions completed; hidden correctness is unknown. Neither is a fabricated
negative or an undisclosed blind evaluation of the selected task.

The prototype's zero-free demonstration example intentionally leaves two
counting policies indistinguishable until a zero-containing query. It is
recorded as one ambiguous teaching control and creates zero solver attempts.
Frozen solve notes are human-readable work logs, not token-level model traces
or log probabilities. Evidence: `solve-blind/`, `solve/`, and the prototype's
private negative-control record.

## D8 — Keep audits and broad-suite failures within their evidence scope

The two journaled audit targets are findings only. Their canonical domain gaps
and exact-control counterexamples are recorded without source edits. The
full root repository test command reported 19 failures, 995 passes, 3 skips
and 18 passed subtests. These failures lie in unchanged components, but no
pristine-baseline broad run was made, so they are not all proved pre-existing.
Direct sandbox restrictions are identified only where the evidence supports
them; other failures retain their concrete assertion/fixture mismatch.

Only the selected task has source edits. Repairing shared process supervision,
root fixture assumptions or another generator would violate the packet's
delta scope. Focused selected-task tests, battery results and fresh patch
replay are independent evidence and are not presented as a green repository
suite. Exact identities and classification are in
`checks/repository-test-summary.json` and `checks/repository-tests.xml`.

## D9 — Deliver a small, replayable delta with complete decisive evidence

The official builder creates the source patch and intake index. Fresh replay
must check Git's exact WORK root, patch inventory and every changed file hash,
then run focused tests with that fresh checkout's own Python and Racket
environment. The final solve generator hash must equal the replayed generator.
The reviewer-owned receipt is indexed in `REVIEW.md` and `RESULTS.json`.

Copied runtime trees and virtual environments are reproducible intermediates
and stay outside the return. Large raw census and superseded export evidence
are losslessly gzipped using the packet's existing transport tool; every
restored byte was compared before relocating the local raw copies. The return
retains the decompressor, per-file sizes/hashes, all failures and exact command
receipts. No only copy of a failure was discarded to meet the ZIP budget.
