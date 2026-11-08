# Working notes: c5f62271ea44

## Current selected-source proposal: review-a3b91596a2979911

Version **3.3.0**; generator SHA-256
`e71a8359f0ef77c8ca881a47703ca3265ffd0d54ddc46f6309c97316dc894f03`.
Canonical rule `74e8392d1794`, its source, canonical examples, catalog and approval
records are unchanged. This remains a reviewer proposal, not approval or training
admission. The supplied review index had no unresolved audits. Prior return
`review-a81963d8ecd2a8a5:v0001` supplied leads, not current-byte verification.

### Current repair and decision reversals

All 8 labeled canonical rows (4 unique pairs) are reflections. Two declared
canonical-fitting rivals fit all rows: `blue_corner_reflection` ignores the three
non-blue marker identities and uses only the source/target blue corners;
`inverse_transform` reads the full key but applies the inferred transform backwards.
Actual canonical Racket witnesses show that old complete lessons could teach
neither distinction. Baseline blue-corner witnesses are in
`counterexamples/blue_corner_reflection_lesson.json`; the intermediate v3.2.0
inverse-rival witnesses are in `counterexamples/inverse_transform_lesson.json`.
These are teaching defects, not bad canonical labels.

The earlier eight-permutation decision guaranteed axis variety but not a
quarter-turn witness in every complete lesson. **Final reversal:** retain four
demonstrations while using a seeded period-16 cycle with Q7/D2/O7: seven quarter
turns, two diagonal reflections and seven ordinary axis-preserving transforms.
Thirty full-period cyclic class representatives × sixteen phases cover 480 lawful
class phases before label-assignment rejection. Quarter directions use a seeded
4/3 majority, both diagonals occur once, and ordinary values include all four
ordinary transforms plus three repeats. At most 64 assignments are attempted;
a separately verified fallback and seeded phase guarantee termination.

Every five-pair window has at least two quarter turns, two or three swapping
transforms and at least four distinct transforms. Any one held-out query leaves
a quarter turn refuting both canonical-fitting rivals, both axis classes and at
least three distinct demonstration transforms. The hook checks actual rival
predictions, body transport and the same teaching requirements. Three older
heuristics remain semantic/lesson rivals but are removed from CANONICAL_SHORTCUTS
because they fail stored canonical labels. There are five unique rival programs,
not twelve independent rivals from their namespace aliases.

A repeated ten-slot five-class template was rejected because demonstration class
counts plus query blue corners determined answers; a twelve-slot candidate had
a complete known-middle-holdout shortcut using exact ordered demo transforms and
query blue corners. Fourteen slots had less empirical projected-query ambiguity
than sixteen. The bounded comparison is retained in
`checks/final-review/candidate_schedule_comparison.json`; it is not a trained-model
score. The final independent review `checks/final-review/REVIEW-v3-3.json` exhausts
class completeness and all fallback windows/holdouts without claiming universal
shortcut freedom.

Exact Python integer seeds and nonnegative integer indices are required at both
public entry points; bool/float/string/None do not silently alias draws. Signed
integer seeds remain legal. The family context precedes the main per-instance
context to preserve override provenance. Versioned keyed streams deliberately
change across versions. Geometry, palettes, profile priors and authority remain
unchanged; old body-component-partition limitations remain.

### Final source-bound evidence and limits

- `checks/task-tests-v3-3/result.json`: 119 passed (92 inherited, 22 new canonical
  regressions, 5 prototype tests), no failures/skips.
- `checks/after-v3-3/result.json`: all 12 battery stages green, including required
  rotations and consumption of the final fixed-seed schedule receipt.
- Production census `checks/lesson-census-v3-3.json.gz` and companion summary:
  100 lessons per band, 300 lessons, 1,500 unique inputs and 1,500 query holdouts.
- Fixed-seed enumeration `checks/schedule-census-v3-3.json`: seed 0, all 16 starts
  in each band, 48 overlapping lessons, 240 holdouts and 60 unique inputs.
  Its display residue modulus 6 is separate from its declared/enumerated period 16.
- Both census production and rotation verdicts are `no_ambiguity_found`, policy
  `require`, against five unique rivals, with zero hook/scoring/materialization
  errors. Production is four ordered demos plus one query; each rotation holds
  out one of the five pairs and retains remaining demonstration order.
- `workspace/check_schedule_leakage.py`, final evidence under
  `checks/schedule-leakage-v3-3/`: actual seeds 0..255, medium, 5,120 inputs,
  4,096 windows, 20,480 holdouts. A lookup given known holdout position, all four
  ordered demo transforms and query source/target blue corners has collisions
  at every holdout position. Ten query witnesses were actual-Racket checked.

The schedule is finite, correlated and sixteen-periodic; accepted assignment
rejection and fixed fallback may bias support. Projection collisions refute only
the specified lookup, not every undeclared shortcut. Explicit symmetry overrides,
nonconsecutive or rejected/reassembled pairs need materialized lesson validation.
Worker hook/rival enforcement supersedes the old no-enforcement limitation below.
No universal identifiability or model-transfer claim is made.

The broad suite remains failed on interim v3.2.0 bytes: 19 failed, 1,000 passed,
3 skipped, 18 passing subtests. Bounded triage is in
`checks/repository-tests/triage.json`; affected components are unchanged, but not
every failure was rerun on a pristine baseline and no full final-source rerun is
claimed. Expected red tests, interim schedule failures and old solve revisions
remain evidence. Both audit sources remain unchanged.

### Separate proposed parametric extension

`workspace/parametric/direction.py` holds `mapping_direction=forward|inverse`
constant for each episode. Forward is byte-identical canonical source; inverse
swaps quarter-turn execution after the same key interpretation. Four demos plus
one query intentionally use distinguishable quarter turns; support is narrower
than canonical generation. Actual Racket supplies every label. Final evidence
`checks/parametric/episodes-v3-3-final/` has 8 episodes, 40 holdouts, 90 Racket calls
including 8 canonical-parity rows, exact program hashes and a same-input intervention.
Status: **prototype / proposed**, separate from canonical approval.

---

The following account is retained predecessor **v3.1.0 history**. Its eight-period
and worker-integration statements are superseded by the current section above;
its historical measurements do not describe final v3.3.0 bytes.

## Source-bound review: review-a81963d8ecd2a8a5

Review run: 2026-10-02 UTC. Candidate version: 3.1.0. The canonical Racket rule,
canonical rows, imported evidence, and approval metadata are unchanged.
The source task is 94133066; selected rule hash remains `74e8392d1794`.

### What changed and why

Version 3.0.0's `schedule_profile` discarded the seed and selected a transform
from `sample_index % 8`. Across seeds 0..127, every slot therefore had a single
transform. A key-ignoring solver that crops the panel and learns only a fixed
transform per position scored 64/64 on held-out seeds 64..127 at every position.
With three demonstrations, the query was always clockwise rotation; that rule
solves 0/4 unique canonical pairs. Pooled eight-transform coverage hid the defect.

Version 3.1.0 draws an eight-transform permutation from a family-level keyed RNG.
Every cyclic four-demo window has four distinct transforms and both axis classes.
A bounded fallback uses a seed-dependent phase of the old valid cycle. The order
is reproducible within a seed, independent of difficulty, and varies across
seeds. Generate constructs this auxiliary context before the main draw context:
the shared override checker inspects the last captured context for provenance.
The first candidate got this order wrong; its failed battery is retained in the
review return, alongside a red-then-green regression test for this exact issue.

The prior grammar repair correctly retained disconnected canonical motifs
(GNOTE-004144), but its sampler still emitted connected bodies only. The new
`body_kind` axis samples a connected body or a main connected component plus
one/two isolated cells, giving two/three four-connected components. Diagonal
contact remains legal. Body cardinality is exact; retries are bounded, with a
constructive fallback. This is a controlled coverage improvement, not full
coverage of canonical component-size partitions such as [9,3,3]. Connectivity
remains a sampling axis, never a restriction on canonical acceptance.

The prior external key spans were only 3..5 by 3..5. Canonical spans are 7x7,
8x7, 10x8 and 8x11. The new `key_extent` axis retains compact keys and adds
extended keys with at least one dimension above five, up to eleven where the
selected grid/panel/side has room. Finite feasible options preserve a one-cell
separator. All four canonical key spans are reachable in their corresponding
canonical profile and side. Exact multi-dimensional frequency matching is not
claimed. Existing linked grid, panel and palette profiles are unchanged.

### Measured results

Default probe: seeds 0..127, sample indices 0..7, medium difficulty (1,024 inputs).
Before: 1,024 connected bodies and zero extended keys. After: 516 connected,
264 two-component and 244 three-component bodies; 514 extended keys.
Fit position-only transforms on seeds 0..63 and evaluate 64..127: held-out counts
per slot become [8,11,5,7,9,5,11,8]/64, instead of 64/64 in every slot. All eight
transforms occur at every slot in this cohort. This is not a trained-model score.

The supplied 12-stage battery passes before and after; the independent probe
exposes ten pre-existing gaps that this battery did not reject. The final probe
passes 3,240 canonical-Racket calls: eight canonical rows (four unique pairs),
1,024 defaults, 1,920 full-axis/difficulty combinations, 128 key-only interventions,
and 32 five-pair lessons. The task suite passes 92 tests; repository tests pass 132.
A two-episode public API smoke test with four demos has zero rejections and
retains `approved: false` in emitted provenance.

### Boundaries and next checks

This remains a candidate, not an independent safety promotion. Replay the
recipient's independent monitor on the exact source and authority hashes.
Use four demonstrations, consistent with `EXAMPLES_NEEDED = 4`. The single-task
CLI/API currently defaults to three; the shared worker does not call
`lesson_identifiable`. The export CLI defaults to four. No shared API change is
included in this task-scoped patch.

The schedule is still eight-periodic within a seed. This removes the observed
corpus-global position code, not every possible curriculum or long-episode
shortcut. Larger/noisier motifs, arbitrary palettes/dimensions, all component
size partitions, and downstream Qwen3.5-9B transfer remain unmeasured. Imported
notes and selected-versus-archival authority distinctions are preserved.

See `workspace/review_probe.py` and `workspace/README.md` for runnable checks.
## Current reviewer considerations

Source SHA-256: `e71a8359f0ef77c8ca881a47703ca3265ffd0d54ddc46f6309c97316dc894f03`.

# Decisions for review-a3b91596a2979911

## Final scope and authority

Task `c5f62271ea44` is the supplied original ARC family `94133066`. The final
canonical repair proposal is **v3.3.0**, generator SHA-256
`e71a8359f0ef77c8ca881a47703ca3265ffd0d54ddc46f6309c97316dc894f03`.
The starting v3.1.0 hash is
`36c7be0c8dc4b1e43b190809566505af62f88fd8fe031e5c966efea3904c8797`.
The intermediate v3.2.0 hash
`8e242979e5d7db509e8298c877fa99c8a8143505c7fb2ff74e32a0c25924aa82`
is historical evidence, not the final checked source. Selected Racket authority
`74e8392d1794`, its source, canonical examples, catalog, shared runtime and approval
records are unchanged. Review and prototype results confer no training admission.

The supplied task review index had no unresolved audit entries. Prior return
`review-a81963d8ecd2a8a5:v0001` informed the investigation; its measurements were
leads rather than verification of current bytes. The original blind solve was
finished before opening repair sources. The parametric extension remains separate
from selected canonical generation. Historical v3.1.0 notes are retained verbatim
below the current account in the task's `notes.md`.

## P1 — One meaningful rule parameter, fixed for a whole episode

**Decision:** expose `mapping_direction` with allowed values `forward` and
`inverse`, with `forward` the original/default setting. This changes the executed
transformation while preserving the original object roles and inference problem.
The solver must still find the blue panel, infer its four logical corner colors,
read the three external dots and missing blue corner, and infer the unique D4
mapping. The forward rule applies that mapping to the entire panel; the inverse
rule applies its inverse. Clockwise and counterclockwise quarter turns exchange.
Identity, the half turn and reflections are self-inverse.

Changing only palette, panel size, placement or key extent would not change the
rule and would not satisfy this request. A larger permutation of arbitrary D4
actions would create many difficult-to-teach settings and weaken the relationship
to the original family. A second parameter is unnecessary for this bounded
prototype; two meaningful settings suffice to demonstrate the requested workflow.

`workspace/parametric/direction.py` provides a CLI, an episode generator and a
reusable persistent `RuleExecutor`. An explicit setting is held constant for all
five pairs. Passing `None` selects one setting once from a SHA-256 keyed seed.
Both programs are materialized, and every returned label is obtained by executing
the matching Racket program. An independent Python coordinate implementation
checks the result but never supplies the label. The inverse derivation replaces
only two recognized action arms and fails if the expected source text changes.
It is a guarded transformation for this exact family, not a general Racket rewriter.

The forward program is byte-for-byte canonical source, SHA-256
`c217e65e63576fc2ee080e4b04889a47c6dce128b3c897c78076a9a681ed0f0b`.
The inverse program's source SHA-256 is
`1b8145e9afea543b4c9464970c14e5792cd4a684e75831a14a5fd877c238fb1e`.
The canonical callable SHA-256, after comment/wrapper handling, is separately
`927ec0b1b71acd9b3a16daa6a08ac7ed1ccc1cb3e45f8fc1729433052406fa90`.
Source, callable and normalized short rule hashes denote different byte strings.

**Teaching policy:** four demonstrations and one query, all quarter-turn scenes,
with both turn directions present. The two settings differ on every such pair,
so holding out any pair leaves demonstrations that distinguish them. This
intentionally narrower prototype support omits six self-inverse transform
classes. It is not evidence of broad coverage of all variants or all possible
rival programs. Focused tests separately compare the settings on all eight D4
transforms and verify that only quarter turns differ.

Final evidence is `checks/parametric/episodes-v3-3-final/`: seeds 0, 17, 71 and 103
under each of two settings; 8 complete episodes, 40 held-out-query checks, 8
canonical parity rows, 90 actual Racket calls and a same-input intervention with
different outputs. Public files contain only demonstration input/output pairs
and query inputs. Hidden parameter values, seeds, query answers, code, source
hashes and rival diagnostics stay in private authoring files. Five focused tests
pass, and all 16 public/private file-byte hashes were independently checked.

The intermediate evidence is deliberately retained. A regression exposed that
the first report used canonical-object JSON digests for pretty-printed files;
the final writer hashes the emitted bytes. Other retained failures distinguish
missing pytest, a legacy wrapper import, and an incorrect test-count assertion
from rule or label defects. See `checks/parametric/execution-receipt.json` and
the prototype README. Status: **prototype / proposed**. It is outside canonical
generation and requires a separate integration decision.

## C1 — Name and teach both verified canonical-fitting rivals

The canonical ledger has 8 labeled rows representing 4 unique pairs, all
reflections. Two rivals fit every row: `blue_corner_reflection` ignores non-blue
marker identities and chooses the unique reflection carrying the source blue
corner to the missing key corner; `inverse_transform` reads the complete key
but applies the inferred transform backwards. Reflections, identity and the half
turn are self-inverse, so only quarter turns distinguish the second rival.
The previous `always_identity`, `corner_code_only` and `always_flip_ud` declarations
mismatch 8, 8 and 6 canonical rows respectively. They remain semantic/lesson
competitors but are no longer incorrectly labeled canonical-fitting shortcuts.
There are five unique rival implementations, even though their declarations
appear in multiple namespaces.

The baseline v3.1.0 generator already emitted nonreflections, but complete lessons
could have four reflection demonstrations before an identity or quarter-turn
query. Exact actual-Racket witnesses remain in
`counterexamples/blue_corner_reflection_lesson.json`, with receipts under
`checks/canonical-review/`. The initial v3.2.0 eight-permutation repair ensured a
nonreflection but could still show four self-inverse demonstrations before a
quarter-turn query. Its exact inverse-rival witnesses and source snapshot remain
in `counterexamples/inverse_transform_lesson.json` and `checks/inverse-review/`.
These failures concern teaching composition, not erroneous reference labels.

The final lesson hook checks actual rival predictions on valid labeled
demonstrations, including both newly declared rivals. A quarter-turn witness
refutes both: four distinct logical corner markers make quarter-turn direction
and a competing reflection observably different on the full panel. It also
requires body transport, both axis classes and at least three distinct transforms.

## C2 — Retain four demonstrations with a sixteen-slot teaching family

**Final decision:** use a seed-keyed period-16 cycle with seven quarter-turn slots
(Q), two diagonal-reflection slots (D), and seven axis-preserving slots (O).
The source supplies 30 cyclic class representatives and a seeded phase, covering
480 possible class phases before transform-label rejection. Quarter-turn labels
have a randomly selected 4/3 majority; each diagonal occurs once; the ordinary
pool includes all four ordinary transforms plus three seeded repeats. Try at
most 64 assignments, accepting only a full cycle containing all eight transforms
and satisfying every cyclic five-pair window. Exhaustion uses an independently
verified valid fallback, followed by a seeded phase. Difficulty does not change
a seed's family order.

Every five-pair window has at least two quarter turns, two or three axis-swapping
transforms and at least four distinct transform names. Holding out any one pair
leaves four demonstrations with a quarter turn, both axis classes and at least
three distinct transforms. This preserves the four-demo budget and refutes both
canonical-fitting rivals under every holdout of a consecutive accepted window.
A uniform eight-transform cycle cannot do this: two quarter turns in every five
positions require at least 40% quarter-turn frequency, while uniform D4 frequency
provides only 25%. Final class frequencies are 7/16 Q, 2/16 D, 7/16 O; accepted
name frequencies and class weights can be biased by assignment rejection.

The independent exhaustive review, `checks/final-review/REVIEW-v3-3.json`, considered
all 11,440 seven-Q placements and 6,912 diagonal placements after quarter pruning.
It found exactly 480 lawful class phases, equal to the 30 full-period source
representatives and their rotations. It independently checked all 16 fallback
windows and 80 holdouts. This proves the stated combinatorial invariants, not
uniform accepted support or absence of all possible shortcuts.

**Rejected alternatives and reversals:**

- The earlier eight-permutation repair taught the blue-corner rival but did not
  force a quarter-turn demonstration, so it left the inverse rival unrefuted.
- A ten-slot repeated five-class template guaranteed witness counts but allowed
  a complete shortcut using demonstration class counts and query blue corners.
  Fixing the quarter-turn directions also risked revealing a missing direction.
- A twelve-slot candidate left a complete shortcut at a known middle holdout
  using the ordered exact demonstration transforms and query blue corners.
- Fourteen-slot candidates avoided some deterministic failures but had materially
  less empirical projected-query ambiguity than the selected sixteen-slot family.
  The comparison is bounded design evidence, not a model benchmark; see
  `checks/final-review/candidate_schedule_comparison.json` and its executable probe.
- Increasing the demonstration budget would alter the intended four-demo policy.
  IID draws could omit the needed witnesses. Unbounded rejection would make
  completion unpredictable. The selected bounded construction makes its teaching
  and support restrictions explicit.

The selected schedule is still finite and correlated. It reveals some information
about a held-out transform, and longer episodes can exploit repeated order.
No claim of universal induction, independent draws or optimal frequencies is made.
The fixed fallback may further restrict support; its occurrence frequency was not
measured by the independent static review. Explicit symmetry overrides and
nonconsecutive/reassembled lessons need their own hook/materialization checks.

## C3 — Measure actual seeded schedule leakage, not just idealized classes

The reusable `workspace/check_schedule_leakage.py` uses the selected generator and
its actual query scenes. Its information-limited lookup receives the known query
position, all four ordered demonstration transform names, and the query's source
and target blue-corner positions. An identical lookup key requiring different
query transforms refutes a complete solver using only that information.

Final cohort: seeds 0..255, medium, all 16 cyclic starts, indices 0..19 per seed:
5,120 generated inputs, 4,096 windows and 20,480 holdout events. It observed
projection collisions at all five held-out positions. Ambiguous-key event fractions
were 235/4,096, 127/4,096, 148/4,096, 143/4,096 and 229/4,096 for positions 0..4.
These describe this finite cohort; they are not solver error rates or estimated
all-seed frequencies. Ten selected query witnesses, two per position, were
independently checked with actual canonical Racket and all matched. Evidence:
`checks/schedule-leakage-v3-3/report.json`, `racket.json`, `verification.json` and
`witness-inputs.json`. The probe itself executes the generator, not Racket; do not
conflate 20,480 analytical holdouts with 20,480 reference executions.

A collision rules out only this projected-information lookup. It does not show
that all other non-blue information is necessary in every example, remove partial
correlations, or certify absence of undeclared shortcut programs.

## C4 — Keep draw identifiers strict and preserve canonical geometry

Both generation and scheduling require exact Python integer seeds and indices;
indices must be nonnegative, while signed integer seeds remain valid. Explicit
bool rejection matters because bool subclasses int. Floats, strings and None
must not silently alias keyed draws. Errors identify the argument. Auxiliary
family scheduling context is constructed before the main per-instance context,
preserving the shared override observer's last-context provenance convention.
The version participates in deterministic keyed draws; v3.3.0 intentionally changes
the stream. Earlier source snapshots and witnesses stay attached to their hashes.

The solid blue panel, three distinct non-blue inner markers, implicit blue fourth
corner, full-panel body transport and external three-dot key are preserved.
Compact/extended keys, linked shape/palette profiles and connected/fragmented body
sampling remain unchanged because no current counterexample justified a geometry
expansion. Canonical body-component partitions such as [9,3,3] are still outside
the main-plus-singleton sampler's complete support. Support checks do not establish
exhaustive coverage or calibrated frequencies over every lawful scene.

## Final measured policy and evidence

Production is four ordered demonstrations followed by one query. Rotation holds
out each of the five labeled pairs once, retaining remaining demonstration order.
Both final verdicts are `no_ambiguity_found`, with rotation policy `require`:

| Final-source check | Scope | Result / retained evidence |
|---|---|---|
| Portable task tests | 92 inherited, 22 new canonical regressions, 5 prototype tests | 119/119 passed; `checks/task-tests-v3-3/result.json` |
| Canonical battery | All twelve stages, required rotations and schedule receipt | 12/12 green; `checks/after-v3-3/result.json` |
| Production-sampler census | 100 requested starts per band; 300 lessons, 1,500 unique inputs, 1,500 holdouts | Zero ambiguity, hook warnings, scoring/materialization errors against five unique rivals; `checks/lesson-census-v3-3.summary.json` and full gzip report |
| Fixed-seed start enumeration | Seed 0, all 16 declared starts in each of 3 bands; 48 overlapping lessons, 240 holdouts, 60 unique inputs | Same clean declared-rival verdict; `checks/schedule-census-v3-3.json` |
| Parametric prototype | Four seeds × two settings; 8 episodes, 40 holdouts, 90 Racket calls including 8 canonical-parity rows | Passed; `checks/parametric/episodes-v3-3-final/report.json` |

The fixed-seed report explicitly declares `enumerated_schedule_period=16` and
complete fixed-seed coverage. Its separate display residue modulus is 6; that
reporting histogram is not the schedule period. Census seeds, accepted indices,
exact instances, source bindings and outcomes remain in the full reports. The
large production report is retained as `checks/lesson-census-v3-3.json.gz`, with
uncompressed/compressed hashes and restoration details in its compression manifest.
Overlap means 240 pair occurrences in fixed-seed windows are not 240 unique inputs.
Finite rivals and one fixed schedule seed do not establish all-seed or universal
identifiability. Worker materialization and the hook must still validate actual
accepted lessons when assembly policy changes.

## Honest retained failures, solve provenance and handoff

The baseline battery passed 10/12 stages, failing defect lint and semantic
declarations. Expected red regressions, the initial v3.2.0 checks, its inverse-rival
failure, rejected schedule candidates and prototype infrastructure/hash failures
remain source-bound evidence. The eight-period v3.2.0 measurements are intermediate,
not the final-source results in the table above.

The broad repository suite ran on interim v3.2.0 bytes and remains failed:
19 failures, 1,000 passes, 3 skips and 18 passing subtests. It was not rerun wholesale
on v3.3.0. `checks/repository-tests/triage.json` distinguishes environment process/
socket limitations, interpreter-path sensitivity, unrelated archival expectations
and original fixture expectations. Those affected files match the original packet,
and focused baseline checks support part of the triage; not every failure was
reproduced on a pristine whole baseline. No claim of an entirely green repository
suite or proof that every failure was previously known is made.

Both assigned audits are findings-only; their sources are unchanged. `AUDIT.md`
contains exact current-source findings and bounded Racket counts. Neither audit
acceptance nor these repairs automatically resolves unrelated task audits.

The original blind solve finished with 5/5 visible examples and declares no prior
exposure and no reference consultation. The final v3.3.0 post-repair episode is
finished, has 4/4 visible examples and unknown masked-query correctness, and honestly
declares prior exposure plus consultation of the reviewer's own prior Python
solution. The earlier v3.2.0 episode and all actual revisions remain separate
source-bound records. These authored solves are work logs, not model-training or
generalization measurements. Final patch replay and fresh-environment focused
regressions are reviewer-owned handoff checks recorded separately in `RESULTS.json`.

## Final solve-record disposition

The final return uses a source-consistent repeated execution of the same exposed
final episode: one retained current revision, 4/4 visible pairs passed, program
SHA-256 `79f29bfc4ecb0c58a98eca676dbb798fd4e8348f2e37f0cede9a94f51856e6cb`,
finished-notes SHA-256
`b6ef4f790159460e8487316e5b2f743b8336eca9037f72e1ce5e6f87d6f16224`.
Earlier exposure and own-Python consultation both remain declared. The previous
mixed-source revision2 and repeated revision3 records remain unedited under
`checks/prior-solve/v3-3-mixed/` and `checks/prior-solve/v3-3-retry-mixed/`.
They are earlier execution evidence, not the current aggregate attempt count.
After preparation, stale files were byte-compared to retained copies and removed
from the prepared folder before the supported check/finish sequence. Static
complete-payload validation then passed. The reason old files reappeared after
removal/preparation is not established; do not attribute it to a shared helper
without evidence. See `checks/final-solve/clean-record-receipt.json`,
`checks/handoff/mixed-solve-retention.json` and
`checks/handoff/solve-retry-retention.json`. This repeat execution makes no new
independent-induction or private-query-correctness claim.
