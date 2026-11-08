# dc2c4869445c — current design account

## Native parametric finish for review-a84488efcfeb33e9

The promotion-ready family is now `copy_selection ∈ {all,
nearest_after_reflection}`.  `all` is the exact selected canonical Racket
program byte-for-byte.  The alternate keeps the source task's multicolor
8-connected grouping, strict-plurality main-shape selection, singleton-cue
interpretation, directional reflection and cue recoloring, but adds a genuine
second decision: first materialize every cue-directed reflected copy, then keep
only the transformed copy whose bounding-box centre is nearest the canvas
centre.

The sequential dependency is non-collapsing.  Step A produces input-dependent
transformed cells and transformed bounding boxes.  Step B ranks those transformed
centres; it cannot select the winner from the original input coordinates.  The
protected-Racket 30x30 witness replaces that intermediate with original cue
positions, selects a different cue and changes 10 final cells.  The owner-facing
witness is packaged at `checks/dc2c4869445c/sequential-witness.json` with the
exact native qualification source binding.

The adapter supports 2–6 demonstrations and 1–4 prefix-stable queries, with four
stored controller-side queries at 14x18, 20x24, 24x30 and a substantive 30x30
scene.  Inputs are setting-neutral.  The first two demonstrations
constructively reject the declared selection, color, position, direction and
per-group shortcuts; extra demonstrations extend the same lesson without
changing its first two examples.  Public projection reveals one query per turn
and hashes only visible bytes.

Fresh evidence: 26 focused tests and the complete 169-test staged suite pass;
198/198 deterministic sampled episodes succeed; 12 episodes and 56 finite rival
cases execute through protected Racket for 206 evaluations; native qualification
passes both settings at seeds 0 and 17 for four jobs and 40 evaluations; 16
qualification-derived public turns verify; the cross-artifact handoff validator
checks 19 manifest files and replays both causal programs through protected
Racket.  These are finite reviewer checks, not universal identifiability,
owner acceptance or training admission.

The older `gap_variant.py` remains as historical proposed evidence only.  It is
not the native promotion adapter because its extra displacement can be collapsed
into a direct coordinate formula and therefore does not satisfy this round's
required A→intermediate→B dependency.

## Intended rule and accepted domain

Partition nonzero input cells into multicolor 8-connected groups. In each group,
the strict plurality color is a main shape with at least four cells; the other
colors are singleton corner cues. Each cue requests a horizontal, vertical or
double reflection across the corresponding main-shape bounding-box edge, painted
in that cue's color. Preserve the input and add the copies. Color roles are local
to a group, so a color may be a seed in one group and a main color in another.

Canonical Racket clips individual cells outside the canvas. This generator
intentionally samples the narrower domain in which every whole reflection fits
and no different groups collide. All eight canonical pair records are accepted.
The prior all-or-nothing clipping audit remains an open domain question: a
reference-lawful edge witness is excluded, and no accepted example distinguishes
that rival. Neither this repair nor its lesson tools claims to teach clipping.

## Repair decisions in review-7d25a1f0d766d596

Keep VERSION 3.1.0 because it participates in deterministic seed derivation;
identify the repair by source SHA-256. Validate scalar arguments and recognized
controls before GenCtx coercion. Preserve None as an unpinned optional override.
Keep one_group/n_groups and single_seed/seeds_per_group selector conflicts
explicit. The three named textures are lawful subdomains, verified with Racket.
Malformed cell types now return a diagnostic before geometric/color helpers.

Retain successful greedy placements. Only after a placement failure, rebuild the
whole grid in disjoint four-column strips. A connected 3×2 L (or solid 3×2 for
solid_main) has room for every cue/mirror in a 6×4 footprint; at most three strips
fit the minimum 12×12 grid. This fixes a former impossible non-solid 4-cell shape
request inside 2×2 without relaxing count, separation, collision or clipping
constraints. All 235 previously successful calls in the 240-call baseline replay
are unchanged; five previously failing calls now succeed (four distinct recipes,
plus the None/medium equivalent).

Finite executable witnesses link reflection-versus-translation and local seed
roles to actual named rival disagreements. They are input-domain diagnostics,
not a vacuous lesson hook or a claim that every random lesson is identifiable.
The larger lesson census demonstrates why that distinction matters. A separate
workspace/lesson_curator.py builds canonical lessons with checked replacement
demonstrations; the default generator's assembly distribution is unchanged.

## Parametric proposal

workspace/parametric/gap_variant.py provides gap in {0,1,2}, selected once per
episode. Gap 0 preserves the exact canonical raw program. Nonzero settings shift
each reflected copy outward along the reflected axes. All labels are executed
Racket results; all-setting-safe inputs, distinct outputs, bounded search and
finite rival/holdout checks are explicit. This remains a proposed prototype;
shared inputs and ordinal filenames make --gap all a controlled comparison,
not a blinded evaluation. No approval or training state changes are included.

## Limits and evidence

The fallback introduces compact repeated geometry only for formerly failed
placements; it does not establish a general uniform shape distribution. The
curator deliberately favors evidence that separates the two declared rivals,
so its distribution differs from unfiltered lessons. Neither finite inventory
certifies induction against undeclared rivals. Exact commands, failures, Racket
receipts, source hashes and measured lesson counts are in the review return's
checks/ and REVIEW.md. Task tests use reviewer_support discovery for both source
and staged layouts. Selected target_code records were synchronized to canonical
text; canonical Racket semantics, raw archival text and RULE_HASH were unchanged.

## Current owner source and evidence limits

Accepted3.1.0 strict calls,malformed-cell diagnostics,lawful textures and compact exact-size placement fallback;235 prior successful inputs unchanged and five formerly rejected calls repaired. Canonical Racket unchanged;two selected target fields formatting-synchronized,archival raw_code preserved. Reviewer12/12 battery,141 task tests including23 curator tests;fresh closure346/99608 files,19 changed paths exact and141 tests pass. IMPORTANT:raw3-demo lesson census still has11/300 production ambiguities,44/1200 ambiguous rotations and27 further answer-equivalent bundles. Optional task-local curator refutes both named rivals on300 arrangements/1200 holdouts after71 bounded curations,all queries preserved;it is not installed into ordinary production assembly. Clipping remains an explicit reference-lawful but validator-excluded domain question. Proposed gap0/1/2 family has three3+1 comparison episodes,12 holdouts/24 gap-rival checks,exact gap0 authority and30 tests. Owner replaced ordinal setting-mapped public names and retained actual Racket export from passing tests. No raw-lesson qualification,production parameter API,variant approval,training admission or owner battery rerun.
## Current reviewer considerations

Source SHA-256: `f200365928e54477a847a8494a60c081a4428a6057d99491b1b26de34b94cda4`.

# Decisions for review-7d25a1f0d766d596

## P1 — Parametric priority: a discrete gap, with canonical default preserved

The assigned original family is training:b775ac94. Its reasoning structure is local grouping, main/seed role assignment, directional reflection, and recoloring. The prototype changes one small geometric parameter: `gap ∈ {0,1,2}`, applied outward along each reflected axis. Gap 0 preserves the exact canonical raw Racket program. A gap is selected once for an episode, and demonstrations must distinguish that setting from both alternatives. This is more interpretable than randomizing unrelated colors or silently replacing reflection with rotation.

The prototype evaluates every candidate at all three settings and retains only candidates whose entire reflected shapes fit without input or cross-writer collisions. This deliberately narrows the domain; it permits a controlled comparison with identical inputs and different rule settings. It does not assert that this is the natural distribution for each gap. It uses actual Racket labels, with a Python mirror solely as a parity diagnostic. The report preserves exact raw programs, stripped callables and bridge definitions as different hashed artifacts.

The final all-setting run has three 3-demo/1-query episodes, four distinct accepted inputs at indices [0,5,8,15], and 12 rejected candidates out of 16 attempts. All 12 single-query holdouts distinguish the intended gap from the other two settings (24 rival checks). A separate seed-selected invocation chooses its gap once and measures all four holdouts. These are finite examples, not training approval. The ordinal public filenames in --gap all disclose enumeration order; the README explicitly calls this a controlled comparison rather than a blinded challenge.

Rejected alternatives: another independent parameter would increase rule combinations and confound the first small demonstration. Allowing clipping would entangle the outstanding canonical clipping-domain question. Exporting labels from the Python mirror would fail to exercise the proposed Racket. Returning shorter episodes after failed sampling would disguise inadequate support; the implementation raises a bounded sampling error instead.

## R1 — Validate the public call before coercion

The original context coerces scalar values, allowing boolean/float/string controls to behave like integers and treating unknown difficulty values as ordinary sampling. The repair validates exact Python integer types (with bool excluded), a nonnegative sample_index, known difficulty values, known override keys and supported ranges before creating the context. Negative integer seeds remain lawful; rejecting them would be an unnecessary restriction. Optional override None remains unpinned for compatibility.

The existing one_group/n_groups and single_seed/seeds_per_group controls are competing selectors, so the original conflicts remain explicit and narrowly declared. Dimension combinations were not added to that list to hide sampler failures. The named one_group, single_seed and solid_main textures are intentional lawful subdomains; 27 Racket-executed examples support that classification. The malformed-cell validator now returns before unhashable or nonnumeric cells reach frequency and geometry helpers.

## Preserve successful draws; construct tight layouts only on failure

Canonical-shaped prior support and successful random draws were retained. In a 240-call before/after replay, all 235 successful input grids are byte-for-byte equal as JSON values: 120 ordinary draws and 115 explicit 12×12 draws. Five previously rejected calls now succeed; the None and medium calls represent the same underlying recipe, leaving four distinct failures.

The old last-resort shape request attempted a nonsolid connected four-cell object in a 2×2 box, an impossible request. The replacement constructs a 3×2 connected L, or a solid 3×2 shape when requested, with each group's full original/reflected footprint inside a disjoint 6×4 area. At most three four-column strips fit a 12-wide canvas. The construction preserves exact group/seed counts, strict main-color plurality and zero-background majority, with no clipping or paint collisions.

A strip layout creates a regular fallback subpopulation with top-left cue rings and repeated main geometry. The design accepts that limited cost to make advertised tight overrides reliable, while leaving all prior successful greedy placements unchanged. It does not claim uniform polyomino sampling. A broader random packing rewrite would disrupt the established seeded distribution for no demonstrated benefit. Increasing dimensions or lowering group counts would violate exact overrides. Bumping VERSION would change the seed stream, so VERSION 3.1.0 is retained and the exact repaired source SHA binds the result.

## R2 — Finite semantic witnesses, followed by actual lesson checks

The selected generator declares two executable input witnesses and their named rivals: reflection versus translation, and group-local seed colors versus globally unique seed colors. Both predicates require an actual distinguishing input property. Executed Racket checks verify their rival disagreements. No always-empty lesson hook was added to produce a misleading green status.

The 12-stage battery passes these input-domain checks, but its semantic report has `lessons: null` because no lesson hook is declared. Consequently it does not certify the demonstrations. The separate source-bound census checks 100 production-shaped lessons per band with three demonstrations and one query, including all four query holdouts, against the two declared rivals. Its exact failures are preserved. The raw generator and production assembly remain unchanged; the new task-local lesson curator supplies a distinct, bounded export policy that checks demonstrations and rotations and selects replacement demonstrations when needed. Its query is preserved and labels are re-executed with canonical Racket. The final measured before/after counts and limitations are in REVIEW.md and checks/lesson-curator/.

This is resampling for an explicitly finite rival inventory, not universal identifiability. It favors color-role witnesses and therefore changes the lesson distribution. Any downstream adoption must choose this checked assembly path or enforce equivalent checks; raw randomly assembled lessons retain the observed ambiguity. The excluded clipping rival cannot be separated inside either accepted domain.

## Preserve canonical authority; synchronize only selected text fields

The before battery found exact-text drift between canonical `program_solution` and two selected `racket_target.target_code` fields. Execution parity and normalized rule identity already agreed. The supported authority-sync proposal was reviewed and applied only to the two assignment-authorized training/augmented records. The canonical ledger and archival raw_code were not changed. This is text synchronization, not a changed puzzle rule. The selected normalized hash remains f9fbf72b057d.

The command created recovery receipts under repo/var and a new coordination lock. Their hashes were checked and the newly created artifacts were moved to checks/authority/recovery and checks/authority/coordination.lock, preserving their bytes; the packet builder rejects undeclared new repository paths. recovery-relocation.json records the exact mapping. No baseline source or old evidence was removed.

## Portable tests, genuine failures, and solve provenance

Only the task-local inherited test file was migrated to reviewer_support.find_root/load_selected_generator/canonical_pairs. Its assertions remain intact. The baseline root test fixture is frozen and unedited; the standard task-test collector selects the authorized task copy once. recorded_draws() replaces a deprecated private observer field. New regression tests cover coercion, lawful textures, malformed cells, formerly rejected placements, real parametric writing and lesson selection.

The initial missing-pytest environment failure, selected-test fixed-depth path failure, fail-first regressions and real prototype writer failure are retained. The Racket runtime is the packet's pinned offline binary, and Python dependencies are pinned in review-environment.txt. The final handoff is replayed into a fresh runtime-closure extraction with its own virtual environment, not the working copy's import paths or installed environment. The replay is explicitly partial, not a whole-library test.

The independent blind solve preceded source/rule inspection; the later solve declares earlier authoring exposure. Both use only visible examples during the solve, each has one genuine attempt and 3/3 visible matches, and both query sets execute. Hidden-query correctness is unknown. Notes are concise work logs, not token-level traces or log probabilities. No artificial failed solve was manufactured.

## Q1, A1, A2 — Outstanding domain and adoption decisions

The prior clipping audit, review-5e3868cd57b705df:v0001, remains a domain question. Its witness was independently rerun against current canonical Racket, but the accepted generator domain still excludes it. The two newly assigned audits are findings-only and their sources were not edited. Their concrete API/coverage findings are documented in AUDIT.md with rerunnable probes and exact labels. No existing audit resolution, source approval, variant approval or training-admission metadata was changed.

Owner source-closure resolution: the return added
`workspace/parametric/validate_handoff.py` after its recorded qualification.
All previously qualified source bindings, the contract and both program hashes
match. Fresh native qualification and acceptance over the complete final source,
plus protected-Racket causal-witness replay, passed. The helper was preserved.
Current evidence: `evidence/owner-source-closure-requalification/current.json`.
This closes the admission mismatch only; inherited production audit decisions
and training admission remain unchanged.
