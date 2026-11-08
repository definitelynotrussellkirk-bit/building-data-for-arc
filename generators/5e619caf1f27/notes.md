# Working notes: 5e619caf1f27

## 2026-10-03 review repair

The version-2.0.0 generator guaranteed inner-width-, inner-height-, and edge-limited profiles, but randomized the limiting edge independently. A canonical-consistent rival using

`min(inner_h, inner_w, top_margin, left_margin)`

therefore survived 24/100 easy, 26/100 medium, and 18/100 hard four-demo lessons in the pinned 100-lesson census. The canonical six pairs all place the decisive cap on an inner dimension or a near edge, so the rival fit all six.

Version 2.1.0 keeps the rule and public axes unchanged. `edge_limited_one` now selects top/left, while `edge_limited_two` selects bottom/right. The rival is declared in the semantic contract, with a bottom/right witness and focused regression tests. The after census refuted every canonical-fitting declared shortcut in 100/100 lessons per band across 1,499 unique inputs. See `workspace/lesson_rival_probe.py` and the returned check evidence.
## Current reviewer considerations

Source SHA-256: `88e87cce86c9643944e6b644a7b342e6a5219d5adfda9be74abffa42e24ad999`.

# Decisions for `5e619caf1f27`

## D1: Treat the top/left-only minimum as the primary defect

**Original rationale.** The 2.0.0 source said the alternating four-profile curriculum exposed the inner-dimension minimum and the margin cap. That rationale was partly correct, but the limiting edge was selected randomly, so a lesson could expose only top and left margins.

**Alternatives considered.** I considered accepting the all-green baseline battery; checking only hand-picked seeds; and testing only the already declared rivals. All three would preserve the blind spot. The selected alternative was to construct the strongest simple rival that fits every canonical pair and measure it over the pinned lesson sampler.

**Probe and result.** `checks/before_top_left_margin_probe.json` verifies that `min(inner_h, inner_w, top, left)` plus clipping fits 6/6 canonical pairs and survives all demonstrations in 24/100 easy, 26/100 medium, and 18/100 hard lessons.

**Failure modes and limits.** This rival is not asserted to be the only plausible shortcut. The probe is restricted to lawful generated inputs and one explicit rival in the before phase.

## D2: Keep the canonical Racket rule unchanged

**Original rationale.** The canonical rule, Python mirror, and six canonical outputs agree; the defect was instructional coverage, not transformation semantics.

**Alternatives considered.** Changing the rule or canonical examples could make the historical pairs distinguish the rival, but would alter authority without evidence that the task semantics were wrong. I rejected that option.

**Probe and result.** Both batteries retained `RULE_HASH=ca7c525a09b4`; authority synchronization and execution parity passed. The exact counterexample in `checks/question_5e619caf1f27_shortcut_racket_comparison.json` confirms the canonical Racket output matches the intended mirror and differs from the rival.

**Failure modes and limits.** The canonical examples still do not refute the rival by themselves. The generated curriculum must carry that teaching burden.

## D3: Split edge-limited slots into near-edge and far-edge witnesses

**Original rationale.** The existing schedule already had two edge-limited slots: a one-cell cap and a two-cell cap. Preserving that structure minimized disruption.

**Selected design.** `edge_limited_one` chooses only `top` or `left`; `edge_limited_two` chooses only `bottom` or `right`. Every four consecutive schedule positions contain both slots, so every four-demo lesson has an executable far-edge refuter while retaining near-edge, inner-width, and inner-height cases.

**Alternatives considered.**

- Continue random side selection and hope a far edge appears: rejected because lesson identifiability remains probabilistic.
- Add a fifth or sixth demonstration: rejected because four slots are already sufficient and changing `EXAMPLES_NEEDED` would enlarge lesson cost and interfaces.
- Add a public `limiting_side` override: rejected because side is an internal curriculum choice, not a needed user control.
- Force all edge-limited samples to far edges: rejected because near-edge support is still useful and the two existing slots naturally cover both classes.

**Probe and result.** Focused tests enumerate starts 0–7 for seeds 7, 97, and 997 in each band and assert that every four-demo window refutes the rival. The final 100-lesson census reports zero survivals.

**Failure modes and limits.** Bumping `VERSION` changes the generation stream. The side split guarantees only the intended profile schedule, not uniqueness against arbitrary programs.

## D4: Declare the rival and bind it to a semantic witness

**Original rationale.** The semantic gate can only test rivals present in `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`. The baseline battery was green because the strongest newly identified rival was absent.

**Selected design.** Add `top_left_margin_only_clipped` as executable code and add `bottom_or_right_margin_caps_frame` to `SEMANTIC_WITNESSES`, with `WITNESS_RIVALS` linking the two.

**Alternatives considered.** Documenting the shortcut only in prose was rejected because it would not protect future changes. Adding an exact grid fixture alone was also rejected because a semantic witness generalizes across generated scenes.

**Probe and result.** The focused test confirms the rival fits all six canonical pairs, every scheduled far-edge sample satisfies the witness, and the rival disagrees with the authority there.

**Failure modes and limits.** Declared-rival systems remain incomplete by construction; a future rival census must continue searching beyond the current declarations.

## D5: Retain four demonstrations and existing public axes

**Original rationale.** The baseline exposed only exact `grid_h` and `grid_w` overrides; shape, palette, placement, and curriculum profile were intentionally internal. Four demonstrations correspond exactly to the four deterministic profile slots.

**Alternatives considered.** Adding a side/profile override would make targeted probing simpler, but would expand the override contract and risk teaching users an implementation detail. Increasing lesson length was unnecessary after the side split.

**Probe and result.** The after battery's override and grammar stages passed, and all sliding four-demo windows in the focused test are identifiable.

**Failure modes and limits.** Internal schedules are less convenient for external callers to target directly; the retained workspace probe compensates by using deterministic seeds and sample indices.

## D6: Build a source-bound rival census instead of relying on the smoke sample

**Original rationale.** `DUTIES.md` explicitly warns that the small battery lesson sample is a smoke check and requests at least 100 lessons per band when canonical-fitting rivals exist.

**Selected design.** `workspace/lesson_rival_probe.py` imports the final generator by path, records generator and probe hashes, reads the actual `CANONICAL_SHORTCUTS`, verifies which rivals fit all canonical pairs, and applies the pinned lesson sampler to only those rivals.

**Alternatives considered.** A copied rival-name list was rejected because it drifts from the semantic contract. Random unrecorded sampling was rejected because it is not reproducible.

**Probe and result.** Four canonical-fitting rivals were discovered automatically. Each was refuted in 100/100 lessons per band; zero `lesson_identifiable` failures occurred across 300 lessons and 1,499 unique inputs.

**Failure modes and limits.** The tool uses `rule_mirror` for throughput; Racket/mirror parity is checked separately by the battery. It is a bounded census, not a universal theorem.

## D7: Version the distribution repair as 2.1.0

**Original rationale.** Version is part of deterministic generator context, so a distribution-affecting change should not masquerade as identical generator bytes or stream semantics.

**Alternatives considered.** Leaving version 2.0.0 would minimize sample churn but obscure a real curriculum change. A major version bump was unnecessary because the task rule and public axes are unchanged.

**Probe and result.** The final generator hash and version are recorded in the solve summary, rival probe, and battery evidence.

**Failure modes and limits.** Exact historical seeds no longer reproduce the same 2.0.0 grids under 2.1.0; baseline evidence remains retained for comparison.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/5e619caf1f27/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-24 parametric handoff `review-2f669e754965367d`

Built `workspace/parametric/edge_cap_episodes.py` with one episode-fixed
parameter, `edge_cap`:

- `capped` is the exact canonical Racket program and remains the default.
- `uncapped_inner` uses the smaller inner dimension without the four edge
  margins, with the finite canvas clipping the expanded frame.

Both settings consume identical source-shaped nested rectangles.  The adapter
supports 2–6 demonstrations and exactly four private queries, including a
source-valid 30x30 edge-limited case.  Racket replay, demo-only distinction,
sequential reveal, public/private projection, batch binding, and corruption
rejection are covered by focused tests and retained two-seed examples.

The review also found that `CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)` falsely
claimed all nine rivals fit the six canonical pairs.  The registry now contains
exactly the four programs actually derived to fit every canonical pair.  The
retained tests were made source-bound and portable instead of importing a
legacy staged namespace or assuming a fixed parent depth.

Native promotion qualification correctly stops at the current-source approval
gate because the production generator hash changed in this repair.  The owner
must review/re-approve that source before rerunning qualification; no gate was
bypassed and no variant acceptance was attempted.
