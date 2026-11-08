# Working notes: 72a6d8b343e4

Version 3.0.0 replaces the aligned-pairs-only baseline with alternating
`canonical_core` and `dual_witness` profiles.  The decisive negative cases are:

- an exactly-two misaligned colour, which must remain unchanged;
- a three-occurrence colour with one aligned subset, which must also remain unchanged.

The selected Racket authority was not changed; `RULE_HASH` is pinned to
`3650a4704dc3`.  Exact design rationale and limitations are in packet-root
`DECISIONS.md`.  Reusable independent probes live in
`workspace/reference_probe.py`; they expose canonical answers and therefore must
not be used during visible-only solve episodes.

Final task-local regression status at generator SHA-256
`a4e9484773602a3e6e2f8302ad2d999a6ed94d55d6bbae46e938d2bb1e8b2192`:
40 tests passed, including real Racket parity and cyclic lesson rotations.
## Current reviewer considerations

Source SHA-256: `a4e9484773602a3e6e2f8302ad2d999a6ed94d55d6bbae46e938d2bb1e8b2192`.

# Decisions for 72a6d8b343e4

## D1 — Preserve the canonical authority; pin it

**Choice.** Leave the canonical Racket program unchanged and add `RULE_HASH = "3650a4704dc3"` to the generator.

**Original rationale.** Unknown beyond the baseline comments; the baseline omitted a pin even though its prose described the correct rule.

**Alternatives considered.** Rewriting the Racket implementation, or treating the Python mirror as authority. Both were rejected because all canonical pairs and direct Racket probes already agreed with the intended rule; the defect was the sampled input distribution and contract, not answer execution.

**Probe/evidence.** Final rule smoke and authority sync are green in `checks/after/`; real Racket parity is exercised by `test_real_racket_authority_matches_oracle_on_canonical_witness_and_generated_inputs`.

**Failure mode/limit.** The Python mirror is review scaffolding only. `workspace/reference_probe.py` fails loudly when Racket is unavailable and never silently substitutes its oracle.

## D2 — Replace the old axis surface rather than patch its aliases

**Choice.** Advertise only six exact pixel-recoverable axes: `grid_h`, `grid_w`, `n_lines`, `n_adjacent`, `n_misaligned`, and `n_triplets`.

**Original rationale.** The baseline claimed palette kind/size, position bias, density, distinct-colour count, pair count, and texture. Some appeared intended to expose combinatorial variety, but palette textures were never applied, several fields were aliases, and negative textures overlapped the ordinary domain.

**Alternatives considered.** Keep compatibility aliases; declare all invalid combinations; or mark fake controls diagnostic. Keeping them would preserve a misleading API and a large incompatibility surface. Structured incompatibility declarations were unnecessary because a smaller truthful contract can construct every joint combination.

**Probe/evidence.** The final override matrix accepts 17,730/17,730 draws over 197 cases (`checks/after/checks/72a6d8b343e4_after_override.log`). Task tests independently recover every requested count from pixels on the minimum 8×9 grid and reject unknown/out-of-range/wrong-type values.

**Failure mode/limit.** Palette choice remains randomized but is not promised as an exact control. There are only nine nonzero ARC colours, so the declared maxima deliberately cap total roles at seven.

## D3 — Match the canonical profile explicitly

**Choice.** Add a `canonical_core` profile with 8 rows, width cycling through 9/10/11, exactly two nonzero colours, and no semantic witness groups.

**Original rationale.** The baseline sampled roughly 5–9 rows by 7–12 columns and therefore hit none of the three canonical `(height,width,palette-size)` profiles in 60 draws.

**Alternatives considered.** Expand all random ranges and hope for incidental hits, or opt out of the profile floor. Incidental support is fragile and an opt-out was unjustified because exact support is easy and semantically useful.

**Probe/evidence.** `checks/after/checks/72a6d8b343e4_after_profile_floor.json` reports 31/60 exact hits and nonzero support in every band. All three canonical inputs pass `self_check` and `strict_canonical_like` tests.

**Failure mode/limit.** Canonical-profile examples alone are semantically ambiguous; they are never the whole curriculum.

## D4 — Teach both decisive guards in the same example

**Choice.** Add a `dual_witness` profile containing (a) an exactly-two misaligned pair and (b) a three-occurrence colour with one tempting aligned subset, alongside at least one true bridgeable line.

**Original rationale.** The baseline source named `no_shared_axis` as a degenerate texture but ordinary samples never included it, and it had no case where a third occurrence suppresses an otherwise tempting line.

**Alternatives considered.** Separate one-guard profiles, random optional guards, or a single hand-written fixture. Separate/random profiles can leave a three-demo lesson without one of the guards; a fixed fixture provides poor geometric and palette diversity. A dual witness guarantees both semantic contrasts whenever that profile appears.

**Probe/evidence.** Each witness fires 309/600 draws in the semantic gate. Both declared rivals are refuted in 300/300 production lessons and in every cyclic rotation tested locally.

**Failure mode/limit.** The two selected rivals are the strongest simple canonical-fitting alternatives found, not an exhaustive hypothesis class.

## D5 — Alternate profiles deterministically

**Choice.** Use a period-two schedule: `canonical_core`, `dual_witness`, repeating; keep `EXAMPLES_NEEDED = 3`.

**Original rationale.** The baseline had no explicit lesson assembly policy.

**Alternatives considered.** Pure IID profile draws, a longer six-step hand schedule, or all-witness examples. IID draws can create all-canonical ambiguous windows. A longer schedule adds proof burden without benefit. All-witness examples lose direct canonical-shape support and may make the exception structure look universal.

**Probe/evidence.** Any four consecutive instances contain two examples of each profile. The task-local rotation test makes each of those four instances the query in turn and verifies both competitors are refuted by the other three; the production census covers 100 starts per band and all six sampler residues.

**Failure mode/limit.** Sample-index parity identifies the profile family, though it does not identify the output. This is called out in `REVIEW.md` rather than hidden.

## D6 — Construct layouts by disjoint local blocks

**Choice.** Partition each grid into 1×N, 2×N, or 2×3 blocks and assign one colour-role per block, each at least 3×3.

**Original rationale.** The baseline used rejection sampling and could fail or ignore controls when pair counts and dimensions interacted.

**Alternatives considered.** Continue global rejection sampling, backtracking placement, or use fixed coordinates. Rejection/backtracking is more complex and leaves hard-to-prove override holes; fixed coordinates collapse diversity. Block packing gives a constructive proof for every advertised combination while still randomizing block order, orientation, endpoints, palette, and dimensions.

**Probe/evidence.** Maximum controls (`3+1+1+1 = 6` roles; the implementation also tolerates the aggregate colour bound) are exercised on every band at 8×9. The full override gate reports no generation rejection or mismatch.

**Failure mode/limit.** Roles do not cross or overwrite each other. The generator therefore teaches independent colour transformations, matching the canonical evidence but not hypothetical overwrite precedence.

## D7 — Treat adjacent endpoints as a lawful positive edge case

**Choice.** Model `n_adjacent` separately from separated `n_lines`; adjacent exactly-two endpoints are accepted and remain unchanged because the inclusive segment is already complete.

**Original rationale.** The baseline listed `adjacent_pair` as a degenerate texture, and defect lint showed it actually passed `self_check`, revealing that it was a lawful edge case misclassified as a negative.

**Alternatives considered.** Remove adjacent cases or count them as lines. Removing them weakens the boundary behavior; combining them makes exact observable controls ambiguous.

**Probe/evidence.** `observe_overrides` distinguishes path length two from length three or greater. Canonical-core phases use adjacent examples while maintaining two aligned endpoint colours.

**Failure mode/limit.** `n_lines` always remains at least one, so every generated example has an observable output change.

## D8 — Make the semantic contract executable

**Choice.** Declare `strict_canonical_like`, two witness predicates, two rivals in `CANONICAL_SHORTCUTS`/`LESSON_COMPETITORS`, and `lesson_identifiable`.

**Original rationale.** No contract existed; baseline semantic gate returned `NO_CONTRACT`.

**Alternatives considered.** Prose-only documentation or tests with copied rival names. Prose does not drive the shared gate, and copied lists drift. The reusable probe/test code iterates the generator’s live declarations.

**Probe/evidence.** Shared semantic gate passes 3/3 canonical inputs, 2/2 witness classes, 2/2 rival claims, and 12/12 smoke lessons. The 300-lesson census independently uses production materialization.

**Failure mode/limit.** A declared rival can never prove absence of undeclared shortcuts. `QUESTION_ANSWER.md` names the strongest current rival and retains an exact Racket-checked counterexample.

## D9 — Build a portable independent probe for future reviewers

**Choice.** Add `workspace/reference_probe.py` with a literal oracle, observable-role extractor, canonical data loader, standard witnesses, and a real-Racket batch bridge.

**Original rationale.** The task workspace was empty, so future agents would otherwise rederive path handling, occurrence analysis, and authority parity.

**Alternatives considered.** Put helpers inside production code or only inside tests. Production helpers would conflate generator behavior with its oracle; test-only helpers are harder to reuse for audits. The workspace keeps them clearly non-selected and reusable.

**Probe/evidence.** All 40 portable task tests import this module; 35 canonical/witness/generated inputs are compared with the selected Racket authority.

**Failure mode/limit.** The helper exposes canonical answers and therefore must not be used during either visible-only solve. Its module docstring and the packet duties make this boundary explicit.

## D10 — Preserve failures and avoid manufactured solve revisions

**Choice.** Retain the interrupted baseline, completed failing baseline, TDD red run, and first green run. Record one honest revision for each solve rather than inventing a bad attempt.

**Original rationale.** Required by the assignment and useful for diagnosing what changed.

**Alternatives considered.** Delete noisy failures or manufacture a teaching negative. Both would corrupt the evidence trail.

**Probe/evidence.** `checks/before/`, `checks/before-complete/`, `checks/tdd/red.log`, `checks/tdd/green-1.log`, `solve-blind/`, and `solve/` preserve the sequence.

**Failure mode/limit.** The post-repair solve is intentionally marked exposed because generator work had already revealed the rule.

## Prior-return use

No prior return was used as a lead. `repo/generators/72a6d8b343e4/evidence/associated_notes.jsonl` was empty, and the work began from the immutable selected baseline and assignment metadata in this packet.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-0af7efed3338d396:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `a4e9484773602a3e6e2f8302ad2d999a6ed94d55d6bbae46e938d2bb1e8b2192`. At disposition, audited bytes match the current source.

### Current decision

Audited source means repo/generators/72a6d8b343e4/generator.py, unchanged SHA256 a4e9484773602a3e6e2f8302ad2d999a6ed94d55d6bbae46e938d2bb1e8b2192. No issue found in bounded reviewer audit:40 portable tests and semantic gate over600 draws,zero crashes,strict rate291/600 against0.4floor; declared witnesses/rivals/rotations pass. Finite grammar/hook scope, no universal correctness or new approval. No owner audit rerun or new target approval. Exact target-local evidence: `checks/audit/72a6d8b343e4-combined/RUNTIME_MANIFEST.json` `checks/audit/72a6d8b343e4-combined/checks/72a6d8b343e4_audit_battery_summary.json` `checks/audit/72a6d8b343e4-combined/checks/72a6d8b343e4_audit_commands.jsonl` `checks/audit/72a6d8b343e4-combined/checks/72a6d8b343e4_audit_semantic_gate.json` `checks/audit/72a6d8b343e4-combined/checks/72a6d8b343e4_audit_semantic_gate.log` `checks/audit/72a6d8b343e4-combined/checks/72a6d8b343e4_audit_semantic_gate.ok` `checks/audit/72a6d8b343e4-combined/checks/72a6d8b343e4_audit_semantic_gate.receipt` `checks/audit/72a6d8b343e4-combined/checks/72a6d8b343e4_audit_summary.json` `checks/audit/72a6d8b343e4-combined/checks/task_tests.xml` `checks/audit/72a6d8b343e4-combined/progress.log` `checks/audit/72a6d8b343e4-combined/result.json`

### Assessment or prior finding

## 72a6d8b343e4

**No issue found** in the assigned bounded audit.

Audited source SHA-256: `a4e9484773602a3e6e2f8302ad2d999a6ed94d55d6bbae46e938d2bb1e8b2192`. I ran the combined strict audit preset without changing the target. All 40 portable task tests passed. The semantic gate completed green over 600 draws (200 per difficulty band), with 0 crashes, all schedule residues for moduli 2–8 covered, both declared profiles exercised, and strict-canonical rate 291/600 = 0.485 against the declared minimum 0.4. Its witness, rival, and query-rotation checks passed.

Evidence:

- `checks/audit/72a6d8b343e4-combined/checks/72a6d8b343e4_audit_summary.json`;
- `checks/audit/72a6d8b343e4-combined/checks/72a6d8b343e4_audit_semantic_gate.json`;
- `checks/audit/72a6d8b343e4-combined/checks/task_tests.xml`.

This is a finite audit of the declared grammar and hooks, not a universal proof of correctness.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
