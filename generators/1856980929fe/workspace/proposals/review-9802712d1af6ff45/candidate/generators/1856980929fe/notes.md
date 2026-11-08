# Working notes: 1856980929fe

## 2026-10-23 review

A retained lawful lesson exposed a missing semantic rival: with seed `2`,
`difficulty="easy"`, demonstrations at indices `11..15` use at most two seed
rectangles while the query at index `16` uses three. The wrong rule “expand only
the first two seeds” fit every demonstration and changed the query, but
`lesson_identifiable` returned no finding.

The source-bound repair adds executable `first_two_seeds` and a `third_seed`
witness without changing `generate`, `VERSION`, `RULE_HASH`, or the canonical
Racket authority. The exact counterexample is now rejected. A 300-lesson / 1,800
grid probe found seven raw query-discriminating windows for this rival; all seven
were named by the repaired gate, leaving zero unguarded survivors and zero
invalid inputs. Raw and guarded counts are intentionally reported separately so
the probe does not misclassify an explicitly rejected lesson as a generator
failure.

A separate **proposed prototype** under `workspace/parametric/` adds one
episode-level parameter, `branch_mode in {both, left, right}`, with canonical
`both` as the byte-identical default. It exposes independent demo/query counts,
uses only unique inputs where all three settings yield different outputs, fails
rather than shortening on sampler exhaustion, materializes exact Racket for each
setting, and exports public challenges from visible bytes only. Retained evidence
uses seeds `30,31,32`, five demonstrations and four queries per setting: 27/27
Racket/Python label parity, 4/4 canonical-default checks, 12/12 identifiable
queries, and 31/31 post-write Racket replay. The verifier rejects duplicate IDs, unsafe Racket cell literals, missing
default/alternative coverage, symlink/path escapes, program/public tampering,
hidden metadata leakage, stale generator/prototype bindings, and unmanifested
private files.

Current source SHA-256 is
`280eb13ac248a89c3542aeef297db1de4fa59e245c19004f68f1da18dcd87822`.
The prototype SHA-256 is
`5a9e6bba816baec8c1f9b5adb6d6d1a10a5651c221571cceccc414a4b61c7071`.
The extension remains proposed only: no production parametric API, approval,
training admission, universal sampler claim, or model calibration is implied.

### D11 — Declare the first-two-seeds rival at the lesson boundary

**Choice.** Add the exact wrong rule and a witness requiring a third seed, then
require `lesson_identifiable` to name that rival when it survives demonstrations
but changes a query.

**Why.** The retained six-example counterexample is lawful and source-bound; the
failure was incomplete semantic coverage, not the canonical transformation or
input validator.

**Limit.** This closes one concrete hypothesis class. Future shortcut discoveries
still require new declarations or a broader structural gate.

### D12 — Keep branch direction as a separate, fixed-setting prototype

**Choice.** Preserve production and place `both`, `left`, and `right` in a
standalone episode builder whose setting is chosen once per seed and fixed across
all pairs.

**Why.** Direction changes the executed transformation while retaining rectangle
roles, stride, clipping, and composition. Pairwise-distinguishing inputs make the
parameter directly teachable from demonstrations.

**Limit.** The rejection filter narrows the input domain and the three retained
seeds are bounded authoring evidence, not a calibrated frequency model.

### D13 — Make retained evidence independently replayable and privacy-checkable

**Choice.** Ship a build/verify CLI, content-address public files from visible
bytes, keep settings/programs/answers private, reject nonempty output directories,
and allow a full Racket replay after writing.

**Why.** Future reviewers can reproduce the exact programs and labels while
public identifiers remain invariant to hidden metadata and query answers.

**Limit.** Evidence is immutable by path; reruns use a fresh directory rather
than destructive overwrite.

## 2026-10-03 review

The imported 2.2.0 sampler omitted three canonical rectangle sizes (2×4, 2×5,
4×2), kept every seed in the upper half, advertised ignored controls, silently
accepted unknown override keys, and admitted degenerate fixtures that overlapped
the lawful input domain.  Its validator accepted full-green and 2×2 impostors.

Version 3.0.0 exposes only exact controls that are honored in every difficulty
band.  Multi-seed defaults use distinct dimensions when possible; the four
scheduled placement profiles cover upper, lower, left-clipped, and right-clipped
seeds.  All seeds retain a complete visible first fan level.  `self_check` now
requires one to three separated, solid, canonical-size components and accepts all
four canonical inputs.

The canonical Racket program was not semantically changed.  Both selected
`target_code` fields were synchronized to the canonical `program_solution`, while
the shorter behavior-equivalent `raw_code` remains archival.  The generator pins
normalized rule hash `77504f6c55fa`.

Executable semantic checks include the wrong rules “reuse the first seed's size
for every seed” and “draw only the first fan level.”  The reusable
`workspace/review_probe.py` measures these rivals over shared-seed,
consecutive-index lessons and reads the declarations directly from the generator.
Its 100-lessons-per-band final run produced 1,800/1,800 valid unique inputs and
zero rival survivors that changed a query.
## Current reviewer considerations

Source SHA-256: `280eb13ac248a89c3542aeef297db1de4fa59e245c19004f68f1da18dcd87822`.

# Decisions for 1856980929fe

## D1 — Preserve the canonical rule; repair the input curriculum

**Choice.** Keep the canonical Racket behavior unchanged and pin
`RULE_HASH = "77504f6c55fa"`.

**Why.** All four canonical pairs and the pre-repair rule-smoke behavior supported
the same per-rectangle V-fan: retain each solid green rectangle and stamp copies
downward at multiples of its own height, displaced left/right by multiples of its
own width, with clipping. The defects were in the generator contract and input
distribution, not in the authority.

**Alternatives rejected.** Rewriting the rule to accommodate the old 2×2/full-grid
fixtures would enlarge the task around generator mistakes. Hard-coding the four
canonical examples would not define a usable training distribution.

**Probe and failure mode.** Canonical examples are mirrored in focused tests;
`rule_smoke`, `racket_lint`, `authority_sync`, and the semantic gate all pass on
the final source. A remaining limitation is that these checks prove parity on the
tested domain, not a theorem about arbitrary malformed grids.

## D2 — Replace the false eight-axis surface with four observable controls

**Choice.** Expose only `grid_h`, `grid_w`, `n_seeds`, and `rect_size`, validate
unknown/type/domain errors eagerly, and provide pixel-observable integer axes.

**Why.** Version 2.2.0 advertised ignored or singleton controls (`anchor_corner`,
`asymmetry_force`, `palette_kind`, `palette_size`, and diagnostic `texture`), used
unkeyed randomness for canvas dimensions, and accepted unknown override names.
The isolated baseline override gate found 56,538 findings over 59,850 draws.
A smaller honest interface is more useful than nominal combinatorial breadth.

**Alternatives rejected.** Keeping dead axes as “future” controls would preserve
silent curriculum drift. Marking them all diagnostic would still leave ordinary
callers with misleading knobs. Adding palette variation is contrary to the task's
fixed black/green semantics.

**Probe and failure mode.** The final official override stage passes, and focused
tests cover every legal value, invalid types/domains, and typo keys. `rect_size`
is observed structurally by tests rather than returned by `observe_overrides`;
a future refactor must retain that coverage.

## D3 — Match the canonical rectangle-size support

**Choice.** Use exactly six observed canonical sizes: `2×3`, `2×4`, `2×5`,
`3×2`, `3×3`, and `4×2`.

**Why.** Version 2.2.0 omitted `2×4`, `2×5`, and `4×2`, and introduced unsupported
`2×2`. Rectangle dimensions are causal parameters of the transformation, so
missing sizes are not cosmetic diversity loss.

**Alternatives rejected.** Arbitrary sizes might be lawful under a broad
mathematical generalization, but the small canonical set does not justify that
training-domain expansion. Retaining 2×2 solely for variety would continue the
minimal-impostor defect.

**Probe and failure mode.** Tests force each size, and the 300-lesson probe sees
all six in every difficulty band. This remains an evidence-bounded domain choice;
it does not claim those are the only mathematically valid dimensions.

## D4 — Keep one to three seeds, but make multi-seed parameters independent

**Choice.** Sample one to three separated rectangles, weight defaults toward two
or three, and choose different dimensions for later seeds when no size override
is forced.

**Why.** The authority treats each seed independently. Multi-seed examples with
different dimensions refute the plausible shortcut “reuse the first rectangle's
height and width for every seed.” Single-seed examples remain to preserve simple
instances and canonical-like support.

**Alternatives rejected.** One seed only would never teach independence. Always
three seeds would unnecessarily remove simple cases. Forcing diversity when the
caller explicitly requests `rect_size` would violate exact-control semantics, so
an override intentionally gives every seed that size.

**Probe and failure mode.** `mixed_seed_sizes` is an executable witness and
`shared_first_size` an executable rival. Across 300 shared-seed lessons / 1,800
unique inputs, the rival never fit every demo and changed a query. The result is
specific to the measured consecutive-index assembly policy.

## D5 — Schedule position coverage instead of relying on random luck

**Choice.** Deterministically cycle `upper`, `lower`, `left_edge`, and
`right_edge` placement profiles by seed, sample index, and difficulty. Keep a
blank moat between components and require at least one complete first fan level
for every seed.

**Why.** Version 2.2.0 put seeds only in the upper half and did not guarantee edge
clipping. Lower starts and both clipping directions are causal behaviors of the
rule. A deterministic schedule gives every band stable coverage while retaining
random positions within each profile.

**Alternatives rejected.** Pure random placement made small profile-floor checks
flaky. Pinning exact coordinates would create repeated templates. Allowing merged
seed rectangles would make the intended independent parameters unobservable.

**Probe and failure mode.** The task-local probe records all four profiles in each
band, plus left/right clipping and lower seeds. The schedule guarantees the first
seed's profile; later seeds are constrained mainly by separation and visibility.

## D6 — Make `self_check` a structural domain validator

**Choice.** Require a 25–29 by 22–29 rectangular grid, colors `{0,3}`, one to
three separated solid 4-connected rectangles, canonical dimensions, exact area
agreement, and visible first-level support.

**Why.** The old validator accepted full-green and 2×2 impostors and did not prove
that every component was a solid rectangle. Those inputs can make a rule execute
without teaching the intended object parameterization.

**Alternatives rejected.** A permissive “contains a 2×2 green block” check is too
weak. Treating negative fixtures as lawful texture values conflates diagnostics
with the training manifold.

**Probe and failure mode.** Defect lint, strict profile, semantic census, and
focused malformed-grid tests pass. Separation is deliberately stronger than the
Racket parser strictly needs; it avoids ambiguous merged components in training.

## D7 — Require deeper-level and per-seed semantic witnesses

**Choice.** Declare two competitors: `shared_first_size` and
`single_fan_level`; declare corresponding witnesses; set `EXAMPLES_NEEDED = 5`;
and implement `lesson_identifiable` against the source-bound Python rule mirror.

**Why.** Canonical-scale examples can still be solved by drawing only the first
fan level or by sharing dimensions across objects unless demonstrations expose
both behaviors. Executable rivals turn this concern into a repeatable lesson test.
Five demos fit the worker contract and provide enough scheduled variation without
requiring oversized records.

**Alternatives rejected.** Natural-language invariants alone are not machine
checkable. Testing only individual witness frequency does not prove a complete
lesson refutes a rival. More than five demos would conflict with the worker schema.

**Probe and failure mode.** The official semantic gate passes its 600-draw census.
The larger task probe uses 100 lessons per band, five demos plus one query, and
reports zero query-changing survivors. It uses the Python mirror; separate Racket
checks bind that mirror to the authority on the tested domain.

## D8 — Synchronize selected rule text without changing semantics

**Choice.** In the two selected base solution records, set `racket_target.target_code`
to the canonical `program_solution` and retain the shorter behavior-equivalent
text in `raw_code` with status `canonical_program_solution_selected`.

**Why.** Defect lint reported source divergence even though sampled behavior
matched. Selected execution text should be the canonical authority; archival
provenance should remain available rather than be discarded.

**Alternatives rejected.** Editing canonical to match the archival beautification
would change the authority for no semantic benefit. Deleting `raw_code` would
lose provenance.

**Probe and failure mode.** Final `defect_lint`, `rule_smoke`, and
`authority_sync` pass; rule hash remains `77504f6c55fa`. The authority-set hash
changes because selected source text is now synchronized.

## D9 — Add focused regressions and a reusable curriculum probe

**Choice.** Add 31 portable tests plus
`generators/1856980929fe/workspace/review_probe.py`.

**Why.** The general battery does not discover task tests automatically, and its
small lesson sample is a smoke check. The source-bound probe reads competitors
and witnesses directly from the generator to avoid a stale duplicated rival list.

**Alternatives rejected.** A one-off notebook would be hard for future agents to
rerun. Calling Racket for every one of 1,800 grids would add cost without changing
the role of the probe; parity is checked separately.

**Probe and failure mode.** Portable task tests pass 31/31. The final probe covers
300 lessons and 1,800/1,800 valid unique inputs. It is finite sampling, uses one
explicit lesson assembler, and does not establish universal induction.

## D10 — Preserve interrupted evidence and rerun cleanly

**Choice.** Keep the incomplete before battery and first interrupted after run,
then perform a clean official after battery instead of rewriting partial results.

**Why.** Checkpoint evidence is useful, but an interrupted/running aggregate is
not a pass. The clean terminal run gives a simple acceptance record while the
partial runs document what happened.

**Probe and failure mode.** `checks/after/result.json` is terminal with exit 0,
and its summary is 12/12 green. `checks/before/result.json` remains honestly
running/incomplete with 2 green, 2 failed, and 8 pending. Passing checks do not
change catalog approval or training admission; both remain false/unsafe in the
solve provenance.
