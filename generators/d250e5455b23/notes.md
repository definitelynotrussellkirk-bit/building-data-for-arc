# Working notes: d250e5455b23

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `a1b1042d1f730835dfc4525483512dc95ff526059eee05b60070294e178f6233`.

# Decisions for `d250e5455b23`

## Context and prior rationale

The selected baseline was generator `1.3.0`, SHA-256 `4c8df77c906ccb3975f91fbc7403bcae1999367c3c99d1656f739533b62c0c73`. Its imported notes were an empty working-notes template and its associated-notes ledger was empty, so the original rationale for its broad axes, difficulty ranges, rejection loop, and degenerate textures is **unknown**. I used no prior return as a lead. The canonical examples, the current source, and the before battery were the evidence for the repair.

## D1 — Preserve the selected Racket authority

**Choice.** Leave the canonical Racket program unchanged and pin `RULE_HASH = "9af05fcaf1f5"` in the generator.

**Reason.** The before run already showed selected-authority execution parity, and all four canonical input/output pairs express a coherent rule: each horizontal domino grows downward and each vertical domino grows rightward into a 2×2 square. The defects were in input generation and lesson construction, not in the selected rule.

**Alternatives considered.** Rewriting the rule to “complete a 2×2 on either available side” would broaden semantics beyond the examples. Editing the archival divergent copy would not change selected authority and was outside the needed repair.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green in `checks/after/`; canonical inputs also pass `strict_canonical_like` and the independent Python mirror in the task tests.

**Failure mode / limit.** Authority parity establishes agreement with the selected source, not that every imaginable domino arrangement has a uniquely intended completion convention.

## D2 — Replace rejection placement with constructive layout enumeration

**Choice.** Enumerate all legal 2×2 growth-square anchors for `(height, width, count)` and choose only anchor combinations separated by at least one blank row or column.

**Reason.** The baseline attempted up to 300 random placements per color, then silently continued if none fit. Dense hard requests could therefore return fewer components than requested. The final supported envelope is tiny enough that exact layout enumeration is simple, deterministic, cached, and guarantees completion.

**Alternatives considered.** Increasing the retry count would only lower, not remove, the underfill probability. Recursive backtracking would work but adds unnecessary control flow for boards of size 7–9 and counts 2–3. Allowing growth squares to touch would broaden the task and create component/interaction ambiguities absent from the canonical data.

**Probe.** The 48 Cartesian boundary combinations in `test_boundary_overrides_are_constructive_and_observable` are exercised across four difficulty settings (plus the rest of the 62-test suite); the override battery reports no mismatch or generation error.

**Failure mode / limit.** The one-cell moat intentionally excludes interaction cases. The generator is not a test of overlapping growth squares.

## D3 — Expose only truthful axes

**Choice.** Keep exactly four public axes: `grid_h`, `grid_w`, `domino_count`, and `orientation_mode`. Reject unknown keys and invalid types/ranges.

**Reason.** The baseline advertised palette, density, position, and texture controls that were fixed, aliases, dead, overlapping, or not observable. A smaller exact contract is more valuable than a nominally broad one that downstream schedulers cannot trust.

**Alternatives considered.** Implementing every old axis would add variation with little semantic value and would retain degenerate no-rule cases in the normal training surface. Keeping ignored axes for compatibility would perpetuate false metadata.

**Probe.** `lint`, `defect_lint`, and `override` all pass. The task tests observe every requested boundary value and confirm that unknown and malformed overrides fail closed.

**Failure mode / limit.** This is intentionally not backward-compatible with callers that relied on ignored keys. Such callers now receive an actionable error instead of silently getting a different distribution.

## D4 — Use the canonical structural envelope

**Choice.** Generate 7–9 row/column grids with two or three distinct-color dominoes.

**Reason.** The four canonical joint profiles are `(7,7,3 colors including background)`, `(8,8,4)`, `(8,9,4)`, and `(9,9,4)`, corresponding to two or three distinct domino colors. Constraining the public envelope to observed support eliminates the baseline’s unsupported 6×6 through 14×16 and one through six object claims while retaining meaningful spatial variation.

**Alternatives considered.** A broader 5–16 envelope could be constructively supported, but no canonical evidence requires it and larger/count-heavy boards make rule recognition easier through repetition rather than better through composition. Repeated colors were also considered; they can create disconnected same-color components that some component helpers merge semantically and are not needed to teach color preservation.

**Probe.** `strict_canonical_like` accepts all four canonical inputs, all 600 semantic-gate draws were strict hits, and every band’s 20-draw profile-floor check hit canonical support.

**Failure mode / limit.** The trained domain does not certify repeated colors, one or four-plus dominoes, larger grids, or touching zones. These are explicit exclusions, not hidden gaps.

## D5 — Schedule canonical joint profiles, not just independent marginals

**Choice.** For default generation, sample indices `0..3 mod 5` use the four canonical `(height, width, count)` profiles; slot `4 mod 5` uses difficulty-weighted choices within the same supported envelope.

**Reason.** The baseline’s independent difficulty ranges produced zero canonical-profile hits in medium and hard during the before profile-floor check. Joint scheduling guarantees source support without copying canonical grids: anchor positions, colors, and orientations remain fresh.

**Alternatives considered.** Independent weighted draws could achieve a nonzero expected profile rate but still miss a band in small checks. Always using canonical profiles would reduce size/count diversity. A random “occasionally canonical” coin flip would make exact curriculum guarantees seed-dependent.

**Probe.** Final `profile_floor` passes in easy, medium, and hard. The semantic census reports 1,499 unique inputs across 1,500 pair positions, showing that profile reuse did not collapse examples to copied grids.

**Failure mode / limit.** The modulo-5 profile schedule is deterministic. Models do not receive sample indices, but a downstream assembler that selects pathological nonconsecutive slots could skew profile frequencies; the actual production sampler and 100-lessons-per-band census were tested.

## D6 — Four-example orientation teaching cycle

**Choice.** Retain `EXAMPLES_NEEDED = 4` and schedule orientations as `horizontal, vertical, mixed, mixed` by sample index modulo four.

**Reason.** The canonical transformation has two conditional branches. A four-example lesson should not accidentally contain only one orientation and leave the other branch inferentially unconstrained. Any four consecutive positions in this cycle contain both branches, while mixed examples also demonstrate independent multi-object processing.

**Alternatives considered.** Pure random orientation can create all-horizontal or all-vertical lessons. Alternating only horizontal/vertical would teach branches but omit within-grid composition. Requiring mixed in every example would reduce simple branch-isolation examples.

**Probe.** The semantic gate observed all three schedule profiles in every band. In the required-rotation smoke, all 12 lessons (four per band) and all 60 possible held-out positions were identifiable against declared rivals. The larger census materialized 300 lessons and checked all 1,500 rotations with zero ambiguity.

**Failure mode / limit.** The guarantee assumes the production assembly uses the declared four demonstrations from the sampler. The census holds out each materialized pair, but it does not enumerate every possible nonconsecutive custom assembly.

## D7 — Declare executable rivals and witnesses

**Choice.** Add five rivals: identity, horizontal-only, vertical-only, fixed-color-8, and first-domino-only. Add witnesses for horizontal objects, vertical objects, multiple objects, and preservation of a non-8 source color. `lesson_identifiable` fails closed when a rival fits all demonstrations but changes the query.

**Reason.** Comments naming intuitive alternatives do not let a gate verify whether a lesson actually refutes them. Executable functions make the semantics source-bound and replayable.

**Alternatives considered.** A large generic transform library (flips, rotations, recolors) is already partly covered by shared canonical-shortcut checks, but task-domain rivals are more diagnostic. Adding speculative rivals for 3×3 growth or “fill both sides” was possible; the selected five directly target the branches and object/color independence most likely to be missed by the old sampler.

**Probe.** Each declared witness was tested against its named rivals; the semantic report records 60/60 claim holds for each witness/rival group. No declared competitor survived an identifiable lesson in the 300-lesson census.

**Failure mode / limit.** This is a finite hypothesis family. An undeclared rule may still coincide on all sampled data, so the report says `no_ambiguity_found`, not “uniquely proven.”

## D8 — Keep a Python mirror, but not as label authority

**Choice.** Implement `rule_mirror` and rival transforms for testing/semantic diagnostics only; production labels remain Racket-generated.

**Reason.** A small independent mirror makes tests and rivals understandable and fast, while the source-bound battery compares generated inputs to the selected Racket authority.

**Alternatives considered.** Using the mirror to emit labels would create a second authority and could hide a shared misunderstanding. Omitting it would force every task-local regression through Racket and make rival definitions cumbersome.

**Probe.** The mirror matches all canonical labeled pairs. `rule_smoke` and authority synchronization independently validate the selected Racket execution.

**Failure mode / limit.** Mirror/canonical agreement covers the four canonical pairs; the Racket battery remains the authority for generated labels.

## D9 — Strict self-check and observable metadata

**Choice.** `self_check` validates rectangular 0–9 grids, the declared size/count envelope, distinct colors, axis-aligned two-cell components, in-bounds growth squares, and the moat. `observe_overrides` reconstructs all four public controls from a valid grid.

**Reason.** The baseline self-check did not verify in-bounds completion direction and could not support exact override observation. A source-bound validator must reject near-miss inputs rather than merely count components.

**Alternatives considered.** Recording requested values in side metadata would make override tests trust provenance instead of observable grids. Inferring orientation from generation state rather than the output grid would miss corruption.

**Probe.** The override gate reports `PASS`, rejects unknown keys, and has no findings/warnings. A task test deletes one domino cell and confirms the nearest singleton impostor is rejected.

**Failure mode / limit.** Same-color disconnected objects are excluded via distinct colors rather than supported by a more elaborate component identity scheme.

## D10 — Verification and replay policy

**Choice.** Treat the completed resumed battery, explicit task-test stage, required-rotation semantic stage, large census, and fresh-packet patch replay as acceptance evidence. Preserve the interrupted first after attempt and optional repository-wide timeout separately.

**Reason.** The first full after command was stopped by the execution wrapper after three green stages. The battery’s hash-bound checkpoint/resume mechanism verified unchanged source/settings and completed the remaining stages. The fresh extraction replay proves that acceptance does not depend on untracked local state.

**Probe.** Final source hash is identical in the working packet, runtime manifest, solve summary, and fresh replay. The fresh copy passes 62/62 focused tests after `git apply --check` and application of the exact delta.

**Failure mode / limit.** The optional whole-repository suite did not finish inside the available per-command window; it reached 26 passes before a slow archival self-check. No claim in this return depends on that incomplete run.

## D11 — Audit targets remain unchanged

**Choice.** Record, but do not patch, the two randomly assigned audits.

**Reason.** The assignment explicitly separates audit findings from the selected repair. Editing either target would violate scope.

**Probe.** `A1` and `A2` have canonical Racket outputs, executable rival outputs, exact generator/rule hashes, generated-batch fits, and domain/validator notes under `checks/audit/`.

**Failure mode / limit.** These are adversarial findings, not complete reviews of either target. The reports establish the reproduced shortcuts described, not the absence of other defects.
