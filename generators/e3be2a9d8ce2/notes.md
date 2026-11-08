# Working notes: e3be2a9d8ce2

## Current rule and authority

Version `3.1.0`; generator SHA-256 `ef670abf4cb698782bf304b172a771ce2103487f52c966897e01e5067aea2392`; canonical `RULE_HASH` remains `116a1aaf2218`. Every isolated nonzero emitter keeps its color and emits an inclusive vertical arm to the nearer top/bottom border plus a horizontal arm to the nearer left/right border. Exact center ties use bottom/right. Generated complete ray footprints remain pairwise disjoint, so examples do not teach undocumented row-major overlap precedence.

The accepted associated notes from `external-local-random:2033b17098fe` (accepted source `b59275205e0f788e67b3e971fb70372f46650fc473ef3c0d880a7d8bcc4beafe`) were used only as leads for tie handling, disjoint footprints, and authority history. All measurements in this review were rerun against the packet baseline/final source.

## Decisions in review-ab00916a5eb26a16

1. **Reject scalar coercion.** Seed, sample index, difficulty, integer axes, and enum overrides are now validated before `gen_ctx`. Floats, strings, and booleans no longer silently become legal integers. Exact public overrides remain supported.
2. **Restore joint canonical support.** Every fourth unpinned sample cycles through the five observed canonical `(height, width, emitter count, palette size)` profiles. This raises support without narrowing ordinary draws or changing explicit overrides.
3. **Declare executable semantics.** `diagnostic_transform`, `strict_canonical_like`, witnesses, and identity/vertical-only/horizontal-only rivals now provide a task-domain teaching contract. The Python mirror preserves first-emitter precedence for malformed overlaps while generated inputs remain disjoint.
4. **Repair the lesson schedule.** An intermediate four-pair lesson at easy seed `24303300002611`, start `33`, had three single-color demonstrations and a four-color query. A generic first/last-color-only rule fit all demonstrations. Unpinned residues 1 and 3 now require at least two emitters and two colors; thus every four-pair window and every three-demo query rotation retains a multicolor counterexample. Explicit `n_pixels`/`palette_size` overrides take precedence over this curriculum schedule.
5. **Keep rule variation isolated.** `workspace/parametric/` proposes episode-level `edge_mode=near|far`. `near` is byte-identical to the canonical program; `far` chooses farther edges with up/left ties. It is a runnable prototype only, not part of canonical production or approval.

## Evidence and known limits

- Focused task-local tests: 35 passed, including all four schedule start residues, three bands, three seeds, and all held-out query positions (`checks/tdd/final-focused-prepackage.log`).
- Production census: 300 lessons / 1,200 labelled pairs / 1,200 query rotations; zero declared-rival ambiguities and 1,171 unique inputs (`checks/lesson-census.summary.json`). This is finite evidence against declared and built-in rivals, not a proof against all hypotheses or all seeds.
- Parametric evidence: both settings executed through Racket for four pairs each; all labels matched and every demonstration/query distinguished the alternate setting (`checks/parametric/edge-mode-7319/report.json`). The prototype deliberately uses one emitter and does not study overlap.
- The canonical Racket rule was not changed. Selected archival `target_code` is execution-equivalent but exact-text divergent from canonical; the required sync would edit shared files outside this assignment's patch scope.
- Aggregate test collection remains blocked by the inherited frozen fixture: direct repository collection imports a staged-only private alias, while portable preflight finds two fixed-depth canonical paths. The new task-local tests pass directly; the frozen fixture was not edited as required.
## Current reviewer considerations

Source SHA-256: `ef670abf4cb698782bf304b172a771ce2103487f52c966897e01e5067aea2392`.

# Decisions — review-ab00916a5eb26a16

## Scope and baseline

The assigned object was generator `e3be2a9d8ce2` for original ARC family `training:705a3229`. I edited only the selected task's `generator.py`, `notes.md`, `tests/`, `counterexamples/`, and `workspace/parametric/`. The canonical Racket authority and shared archival solution files were left unchanged. Baseline source SHA-256 was `b59275205e0f788e67b3e971fb70372f46650fc473ef3c0d880a7d8bcc4beafe`; final generator SHA-256 is `ef670abf4cb698782bf304b172a771ce2103487f52c966897e01e5067aea2392`.

The prior associated-note lead was the accepted `external-local-random:2033b17098fe` review, which described down/right tie handling, disjoint complete ray footprints, and selected-rule sync. I did not treat those claims as current measurements: the before battery and all final checks were rerun on this packet.

## D1 — strict call and override validation

**Choice.** Validate literal scalar types and ranges before creating the generation context. Accept only exact `int` values (not bool/float/string) for seed, sample index, and integer axes; require a nonnegative sample index; restrict difficulty and `palette_kind` to declared values; reject unknown axes.

**Rationale.** The before defect linter found 120 coercion cases. For example, `palette_size=6.75` was truncated to 6 rather than rejected. That makes saved generation metadata misrepresent the actual request and permits accidental duplicates in data pipelines.

**Alternatives rejected.** Normalizing strings/floats was rejected because the public schema already distinguishes types. Letting `gen_ctx` perform partial validation was rejected because the observed truncation occurred before a loud failure.

**Failure modes and limits.** This intentionally breaks callers that depended on permissive coercion. Exact integers and all advertised enum values remain accepted. Tests cover seed/index/difficulty and every public integer axis.

## D2 — deterministic canonical-profile anchors

**Choice.** On unpinned samples with `sample_index % 4 == 0`, cycle through the five canonical joint profiles `(height, width, emitter count, palette size)`. Other residues retain difficulty-biased generation.

**Rationale.** The before profile floor had only 1 exact hit in 60 draws: easy 1/20, medium 0/20, hard 0/20; pooled exact 1/60 and envelope 17/60. Independently varying dimensions and colors did not preserve observed joint profiles. The final schedule guarantees at least one exact profile in every band without reducing general support.

**Alternatives rejected.** Widening all defaults toward canonical dimensions did not guarantee joint matches. Making every sample canonical-shaped would overfit the five examples and remove useful variation. A random low-probability anchor would remain flaky under a 20-draw gate.

**Failure modes and limits.** The deterministic residue is visible in sample-index statistics, though the five-profile cycle and ordinary residues retain diversity. Explicit overrides disable the anchor. The rule itself does not depend on dimensions or palette size.

## D3 — executable semantic contract

**Choice.** Add a Python mirror, strict validator hook, witnesses, and three task-domain rivals: identity, vertical-only, and horizontal-only. `lesson_identifiable` checks demonstrations without requiring a private query answer.

**Rationale.** The baseline had no semantic contract, so a runnable generator could not show that lessons teach both L-ray arms. Each retained generated pair now individually refutes all three declared rivals, and the contract can be reused by the semantic battery and census.

**Alternatives rejected.** A prose-only declaration was rejected because it cannot score generated lessons. Comparing solely to canonical examples was rejected because lesson quality depends on generated demonstrations, not only rule parity.

**Failure modes and limits.** The declared rivals are finite. Passing them does not establish unique induction against arbitrary geometric or color-conditioned hypotheses. Generic shared rivals remain important supplemental probes.

## D4 — multicolor witnesses in every four-pair window

**Prior choice.** The first semantic repair relied on random palettes and the declared task-domain rivals. It passed those rivals but left an intermediate lesson where all three demonstrations were single-color.

**New choice.** For unpinned samples at residues 1 and 3 modulo 4, require at least two emitters and two colors. Explicit `n_pixels` or `palette_size` overrides bypass this schedule and remain exact.

**Reason and evidence.** At easy seed `24303300002611`, start sample 33, palette sizes were `[1, 1, 1, 4]`. `generic:first_color_only` and the analogous last-color shortcut fit the three demonstrations and differed on the query. The retained witness is `repo/generators/e3be2a9d8ce2/counterexamples/review-ab00916a5eb26a16/teaching_shortcut_before.json`; the failing test is `checks/tdd/semantic-red.log`. The final focused test enumerates all four cyclic starts, all four held-out queries, three bands, and three seeds.

**Alternatives rejected.** Merely increasing average palette size does not guarantee a witness in every query rotation. Forcing all samples multicolor would eliminate the canonical one-emitter branch. Resampling whole lessons would make reproducibility and schedule coverage harder to reason about.

**Failure modes and limits.** The schedule specifically refutes color-subset shortcuts; it does not exhaust all object-subset rules. The 300-lesson census samples production broadly but is not an all-seed proof.

## D5 — exact overrides outrank curriculum shaping

**Choice.** Apply the multicolor lower bound only when both `n_pixels` and `palette_size` are absent.

**Rationale.** The first schedule implementation overrode explicit `n_pixels=1,palette_size=1` requests on residues 1 and 3. That contradicts the advertised exact controls. A failing regression (`checks/tdd/override-schedule-red.log`) forced the precedence rule.

**Alternative rejected.** Declaring single-emitter overrides incompatible with those residues was unnecessary and would make the API surprising. Exact controls can be honored without weakening unpinned curriculum windows.

## D6 — isolated `edge_mode` parametric prototype

**Choice.** Prototype one episode-level parameter: `near` (canonical/default, ties down/right) versus `far` (proposed, ties up/left). Use exactly one lawful interior emitter per pair, choose the setting once from the episode seed, and expose neither setting nor programs in public challenges.

**Rationale.** This changes only the edge-selection relation while preserving the original object role, L-ray construction, color preservation, and inclusive arms. One emitter makes both settings distinguishable without introducing undocumented overlap precedence. The `near` program is byte-identical to the canonical `program_solution`.

**Alternatives rejected.** A tie-direction-only parameter would be invisible on even dimensions and weakly demonstrated. An overlap-precedence parameter was rejected because the canonical examples do not establish that behavior. Per-example parameter changes were rejected because demonstrations would not define a coherent episode rule.

**Evidence and limits.** `checks/parametric/edge-mode-7319/report.json` records Racket/Python parity for four pairs in each setting, alternate-setting refutation by every demonstration and query, canonical program hash `add3f20b3828e8797f662ded438a062002ae971ea77d7e310611afefdedea5f7`, and proposed far program hash `0c5bf47687120919ef6bf5e5c6a918a96bb0a3e691dab304ab5d4f7027089b01`. This is a proposed isolated prototype, not production integration, training admission, or universal identifiability evidence.

## D7 — blockers left outside scope

1. **Frozen task-test portability.** Direct repository collection fails because inherited `test_generator_e3be2a9d8ce2.py` imports a staged-only private alias. The portable `task_tests` preflight separately stops at lines 21 and 147 because it derives a nonexistent canonical path from fixed `__file__.parents[...]`. Duties forbid editing that frozen fixture. Maintainer migration should use `reviewer_support.load_selected_generator`, `find_root`, `canonical_path`, and `canonical_pairs`.
2. **Authority exact-text drift.** Canonical execution parity passes, but two shared selected `target_code` fields are not exact-text synchronized. The non-applying sync proposal has patch hash `495f708845e90ed55c0838fc1f94eecd99c6052bc5135de4900e85199c048214`; applying it would edit shared files outside the selected-task lane.

## Curriculum annotations

- `multi_rule_interaction`: not applicable — one invariant L-ray rule is applied independently to each emitter.
- `sequential_state`: not applicable — output is computed directly from the input, not through stateful steps.
- `contextual_gating`: not applicable to the task rule; generation schedules examples, but the transformation has no context-selected subrule.
- `task_defined_symbols`: not applicable — nonzero colors are interchangeable payload colors, not a learned symbol vocabulary.
