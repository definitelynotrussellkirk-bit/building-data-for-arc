# Review notes

Version 3.1.0 keeps the canonical Racket authority and public exact-axis API unchanged. It broadens the ordinary four-slot curriculum from elbow-only blocker placement to leg, mixed, elbow, mixed placement. Two mixed slots per cycle make the newly declared `elbow_only_clearance` rival answer-changing in every three-demo subset of a four-sample lesson.

The source-bound diagnostics are `workspace/probe_blocker_clearance.py` and `workspace/probe_lesson_windows.py`. Baseline evidence is retained at `checks/before/blocker-clearance-probe.json`; final distribution evidence is at `checks/probes/blocker-clearance-after-final.json`; the all-start/all-query-rotation lesson probe is at `checks/probes/lesson-windows-final.json`.
## Current reviewer considerations

Source SHA-256: `70a373dd8e3e3ca917e96fd1724981a794a2dc124d5c28701b3d1727a7a97ddd`.

# Decisions for c7c9b61d5a51

## D1 — Preserve blind-solve isolation

**Choice.** Complete and freeze the unrelated `f44596002946` solve before reading the selected generator, canonical rule, or audit targets.

**Rationale.** This keeps the blind record interpretable as an actual visible-example inference attempt rather than a reconstruction after source exposure.

**Alternatives rejected.** Skipping or postponing the episode would invalidate the assignment's intended ordering. No blind artifacts were reused in the repair.

**Evidence / limits.** `solve-blind/summary.json`; one revision, 4/4 visible examples. This says nothing about its masked query.

## D2 — Treat elbow-only support as a teaching defect, not a label defect

**Choice.** Repair the input distribution and semantic contract while leaving the Racket transformation unchanged.

**Original rationale.** The historical reason for elbow-only placement is not recorded. From the implementation, it appears to have been a simple way to guarantee one blocked candidate route while matching all five canonical examples.

**Probe.** `workspace/probe_blocker_clearance.py` classified every generated pair blocker and evaluated the explicit elbow-only rival. On baseline hash `ee84b45...`, all 480 sampled pair blockers were elbows and the rival matched 192/192 scenes. The probe also retained a lawful off-elbow counterexample.

**Alternatives rejected.** Changing the Racket rule would alter correct canonical semantics. Merely documenting the shortcut would leave low-value training data unchanged. Adding only a rival declaration without changing generation would cause the semantic contract to expose, not resolve, the defect.

**Failure modes / limits.** The counterexample establishes that full-route and elbow-only rules differ within the executable grammar. It does not by itself determine the best curriculum frequency.

## D3 — Keep the public exact-axis surface unchanged

**Choice.** Make blocker position an internal scheduled curriculum concept (`BLOCKER_PATTERNS`) rather than a new public `AXES` key.

**Rationale.** The user-facing controls already cover grid size, pair count, and route pattern. Blocker position is needed to teach the invariant, not necessarily as another combinatorial contract that every downstream caller must support. Preserving the API also keeps frozen fixtures and the 6,120-draw override matrix meaningful.

**Alternative rejected.** A public `blocker_pattern` axis would be useful for targeted generation but would enlarge the exact override product and require compatibility policy for combinations that are not needed by ordinary lessons. The reusable probes already provide targeted diagnostics.

**Failure modes / limits.** Future dataset builders that need direct blocker-position control must either promote this internal concept deliberately or use the schedule residues; that is documented rather than silently promised.

## D4 — Use a four-slot `leg, mixed, elbow, mixed` schedule

**Choice.** Pair the existing four-slot route/pair-count schedule with blocker patterns `leg`, `mixed`, `elbow`, `mixed`.

**Rationale.** With three demonstrations and one query, every holdout rotation leaves at least one mixed scene in the demos. Mixed scenes combine elbow and leg blockers in one input, and the generator requires them to be answer-changing for the elbow-only rival whenever the chosen route pattern permits disagreement. The pure-leg and pure-elbow slots also prevent blocker position from becoming a stable label for route choice.

**Alternatives rejected.** Fully random blocker positions could produce unlucky all-elbow lesson windows. Making every scene mixed would remove simple support profiles and move farther from canonical anchors. Alternating only elbow/leg without lesson-window reasoning would not guarantee every three-demo subset contains the needed witness.

**Probe.** `workspace/probe_lesson_windows.py` enumerates 64 cyclic starts per band, rotates all four query positions, and dynamically uses the generator's actual `LESSON_COMPETITORS` mapping.

**Failure modes / limits.** The schedule is periodic and therefore correlated with other scheduled profile fields. Models do not receive sample indices, but further undeclared shortcut probes remain worthwhile.

## D5 — Declare the exact shortcut and its witness

**Choice.** Add `elbow_only_clearance` to both `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`, add `off_elbow_blocker_requires_full_path_scan` to `SEMANTIC_WITNESSES`, and bind them in `WITNESS_RIVALS`.

**Rationale.** A prose statement would not make the failure regression-testable. The executable rival says exactly what the bad learner does, while the witness requires a lawful scene where that rule changes the answer.

**Alternative rejected.** A broad generic “local cue shortcut” label would be harder to replay and could conceal implementation drift.

**Failure modes / limits.** Rival coverage is finite. Other undeclared hypotheses may exist; the question response proposes a generic counterfactual gate to discover this class earlier.

## D6 — Preserve explicit `route_pattern="first"` overrides

**Choice.** Enforce answer-changing mixed witnesses only when the selected route pattern allows the elbow-only rival to disagree.

**Rationale.** The first implementation rejected all mixed scenes with rival agreement. Under `route_pattern="first"`, the rival inspects route 0 first and is necessarily correct even when route 1 has a leg blocker. Requiring disagreement was impossible and caused placement exhaustion.

**Rejected alternative.** Declaring those public combinations incompatible would hide a repair-induced regression and unnecessarily shrink the advertised domain.

**Probe / failure retained.** `checks/after-attempt1/` records the 11/12 battery with 450 override findings. `checks/task-tests-override-red/` records the new regression test failing 2/17 cases before the conditional fix. Final evidence is 6,120/6,120 accepted.

## D7 — Add two source-bound reusable probes

**Choice.** Keep `workspace/probe_blocker_clearance.py` for distribution/counterexample analysis and add `workspace/probe_lesson_windows.py` for exhaustive cyclic lesson rotations.

**Rationale.** The shared battery's small lesson smoke check passed both before and after the repair, so future reviewers need diagnostics that inspect blocker position and full schedule windows directly. The lesson probe reads the current competitor declarations rather than maintaining a stale copied list.

**Alternatives rejected.** One-off shell snippets would be difficult to rerun and easy to detach from source hashes.

**Failure modes / limits.** These probes cover current bounded schedules and declared rivals; they are not formal uniqueness proofs.

## D8 — Keep authority and canonical data unchanged

**Choice.** Do not edit the canonical JSONL or selected Racket rule.

**Rationale.** Canonical outputs already implement full-route clearance correctly, and final rule smoke/authority parity pass. The defect was which lawful inputs ordinary generation supplied.

**Alternative rejected.** Rewriting canonicals to include leg blockers would exceed selected-task scope and alter immutable reference data.

**Evidence / limits.** Rule hash remains `82200d439ef3`; authority set hash remains `228c3b8f22a91c070021d1a459ae3cb3950724d77e56133045d2382fd191a34b`.
