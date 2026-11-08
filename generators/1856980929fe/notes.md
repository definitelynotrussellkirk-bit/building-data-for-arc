# Working notes: 1856980929fe

## 2026-10-23 review (current)

Current generator SHA-256: `cf6e08b5e647f09dd3011b3d7ad3652e37df3f7ec354a7a1ba07bb570df22636`.
The canonical Racket authority and normalized rule hash `77504f6c55fa` are unchanged.
`VERSION` intentionally remains `3.0.0`: it participates in keyed sampling, so a
metadata-only bump would replace the previously reviewed input schedule.

A retained lesson shortcut was concrete: seed `2`, difficulty `easy`, sample
indices `11..15` have seed counts `1,1,2,2,2`, while query index `16` has three
seeds.  The rival “expand only the first two seeds” fits every demonstration but
omits the third query fan.  The generator now declares executable rival
`first_two_seeds_only`, witness `third_seed_expansion`, and the corresponding
witness-to-rival binding.  The large source-bound replay found seven such raw
query-discriminating lessons in 300 lessons and confirmed `lesson_identifiable`
rejects all seven with zero misses.  Evidence:
`checks/repair/1856980929fe-first-two-gate-v1.json`.

A separate, unapproved task-local parameter prototype now lives under
`workspace/parametric/`.  Parameter `fan_stride` is fixed once per episode and
allows `1` (canonical) or `2`; only horizontal displacement changes from
`k*rw` to `k*rw*fan_stride`.  Stride 1 is byte-identical to canonical source SHA
`d57dfba75662273fbbd5aced174f3a28831099169574954cffd383ff42478ccf`.
The retained evidence has two deterministic episodes, three labeled demos and
four distinct queries each, six demos/eight queries total, both settings, exact
Racket labels, demonstration-refuted alternative settings, private metadata, and
opaque public IDs derived only from visible bytes.  Independent replay checks 14
labels, 28 rival predictions, and eight canonical pairs:
`checks/parametric/1856980929fe-fan-stride-v1/verification.json`.  Prototype SHA
`9f53c0933af1006db7b5e93cf01adcfbe387b014110fe889d30a79ee0e0a1e8d`.

The parameter work is a proposal only: no production API, catalog approval,
canonical rule replacement, or training admission follows.  Evidence is finite
(two seeds/settings and the explicit lesson assembler), not a universal proof.

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

Historical 2026-10-03 source SHA-256: `513b681db0dfd9c530f867d70905b082bd14353d2d2c4b77484b2bbe529da7ea`.

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

## D11 — Close the third-seed lesson shortcut without perturbing sampling

**Choice.** Add the `first_two_seeds_only` executable rival and
`third_seed_expansion` witness, but retain `VERSION = "3.0.0"`.

**Why.** A source-bound lesson window proved that five demonstrations can contain
at most two seeds while the query contains three.  The rival therefore survives
the demonstrations and changes the query.  Changing `VERSION` would also change
every keyed random draw, conflating this semantic-gate repair with a new sampler.

**Probe and failure mode.** The exact window is a focused regression.  A separate
300-lesson replay found seven raw survivors and confirmed all seven are rejected
by `lesson_identifiable`.  This remains finite evidence for one assembly policy.

## D12 — Keep the `fan_stride` extension separate and episode-fixed

**Choice.** Prototype `fan_stride in {1,2}` under `workspace/parametric/`, fixed
for every labeled and query pair in one episode, with canonical stride 1 as the
default and byte-identical authority.

**Why.** The extension preserves object discovery, per-seed dimensions, vertical
level spacing, symmetry, and clipping while varying one causal nearby choice.
Separate Racket programs and private metadata prevent accidental replacement of
the canonical execution path.

**Probe and failure mode.** Two retained episodes exercise both settings with
three demos and four distinct queries each; the alternative setting is refuted by
every demonstration and independent replay passes.  The finite two-setting sample
does not grant production or training approval.

## Current prototype public emission-order follow-up

The selected stride writer now collects the complete public batch and emits files in visible-ID order. A focused physical-write-order regression passed against these merged bytes. Earlier static inspection remains prior-source evidence; variants remain unapproved and inherited audits remain explicit.

<!-- arcpuzzles-current-conflict-reconciliation:start -->
## Current proposal reconciliation

The current first_two_seeds_only/third_seed_expansion repair already implements the returned first_two_seeds/third_seed law. Kept its names, source and VERSION. Ported guarded/unguarded probe accounting, retained branch_mode as a distinct sibling to fan_stride, and sorted the selected stride public writes by visible ID.

Current source-bound disposition and focused checks: [evidence/conflict-reconciliation.json](evidence/conflict-reconciliation.json). All proposed variants remain unapproved and training_admitted=false. Existing audits/failures are preserved; this reconciliation does not resolve an audit or refresh an exact-source safety approval.
<!-- arcpuzzles-current-conflict-reconciliation:end -->

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/1856980929fe/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
