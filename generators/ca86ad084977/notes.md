# Working notes: ca86ad084977

## Current selected design

Version `3.0.0`, rule pin `1c1d9560813f`. Inputs use canonical roles: zero background, sparse gray(5) wall objects, and exactly one checkpoint each of colors 2, 3, 4, and 7. The selected authority performs independent 4-neighbor BFS legs `2→3`, `3→4`, and `4→7`, with neighbor priority up/down/left/right, and paints every interior path cell cyan(8), including a checkpoint crossed by another leg.

The prior `2.0.1` choice—wall-5 background with one horizontal zero corridor—was reversed because it had the opposite foreground/background geometry, no canonical sparse-maze support, no tie cases, and no checkpoint-overwrite examples. The selected sampler now alternates canonical-like sparse mazes with compact semantic witnesses. A four-step schedule alternates overwrite-of-2 and overwrite-of-4 witnesses; every four-pair lesson (three demonstrations plus one query) leaves at least one witness in the demonstrations under every query rotation.

Exact axes are limited to `grid_h` (12–13), `grid_w` (12–14), and `scene_pattern` (`canonical_maze|semantic_witness`). Inputs and overrides are strictly validated. `strict_canonical_like`, executable witnesses/rivals, `lesson_identifiable`, and `workspace/reference_probe.py` bind morphology and teaching claims to source hashes.

The Racket behavior was not changed. The selected solution target differed from canonical authority only by four stale comments; it was exact-token synchronized while preserving executable behavior and raw source.

## Known limits

Finite checks cover the two declared plausible rivals: right-before-left BFS priority and preserving crossed checkpoints. They do not prove universal rule identifiability. Fixed-seed schedule enumeration does not exhaust all seeds, and literal color-transition coverage can overconstrain tasks whose colors are semantically interchangeable. Python oracle checks are supplemental; Racket remains the label authority.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ecb9eab7828409d2:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `be9798d95558acdd2418ef3415f7305e9790f494366deeec6c22c00728545a76`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Single-row corridor/0of5canonical validator support on baselinebe9798d95558 addressed by acceptedb4f223 return: restores multi-row routing canonical topology, public tests/canonical support and transition probes including0to8/2to8/4to8. Final reported12/12 battery and300lesson census bound to accepted source, no independent rerun.

### Assessment or prior finding

## ca86ad084977

**Classification: reproduced distribution/domain defect.**

I checked the assigned generator at SHA-256 `be9798d95558acdd2418ef3415f7305e9790f494366deeec6c22c00728545a76`, its validator, all five canonical inputs, and 200 generated draws in each of easy/medium/hard. The selected rule hash is `1c1d9560813f`.

The generator produces a one-row horizontal corridor with all checkpoints on that row. Across **600/600** sampled draws, every checkpoint layout was single-row and every input passed its validator. In contrast, **0/5** canonical inputs have a single-row checkpoint layout; each spans exactly three checkpoint rows, and **0/5** canonical inputs pass the generator validator. The canonical-profile stage likewise found no support.

This is not merely low visual variety: the generated domain omits the topology present in every source example. A model trained only on this generator can learn one-dimensional ordering/path behavior without learning the multi-row routing rule required by the canonical task.

Evidence: `checks/audit/ca86ad084977/distribution_probe.json`, `checks/audit/ca86ad084977/selfcheck/`, and `checks/audit/ca86ad084977/profile/`. The audit target was not modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ecb9eab7828409d2-v0001/audit_assets.json), manifest SHA-256 `260d366d3cc9be0cce16579538d3914b8bb1c3419f22e15d383296157b15177c`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `54f8993e6eb120488c5ef8aa151e685cef37e08a7455d48015948281cf7f7d16`.

# Decisions for ca86ad084977

## D1 — replace the one-row wall-background domain

**Prior choice.** Version 2.0.1 generated a wall-5 background with one horizontal zero corridor and checkpoints in fixed left-to-right order. In the retained baseline battery it failed lint, self-check, defect lint, distribution, profile floor, override, and authority-sync stages. A prior-review lead and a direct 600-draw census found 600/600 generated inputs in that one-row family, while all five canonical inputs use a zero background, sparse wall-5 obstacles, multiple rows, and irregular shortest paths.

**Selected choice.** Generate 12–13 by 12–14 zero-background scenes with exactly one 2/3/4/7 checkpoint, two or three separated gray wall components, 6–15 wall cells, and 6–48 changed output cells. `canonical_maze` draws favor canonical shape profiles but also cover the full six-cell shape envelope.

**Rejected alternatives.** Merely changing background color would retain the fixed one-dimensional shortcut. Free-form random walls without morphology constraints frequently yielded trivial direct paths or disconnected legs. The selected constructive sampler rejects disconnected, identity, overly dense, and low-complexity candidates.

**Evidence.** `checks/before/checks/ca86ad084977_before_battery_summary.json`, `checks/reference-probe-final-v2.json`, and final battery distribution/profile reports.

## D2 — preserve the authority and mirror its hidden semantics exactly

Canonical replay established three independent BFS legs (`2→3`, `3→4`, `4→7`) through non-5 cells, priority up/down/left/right. Every interior cell is painted 8, even if it was another checkpoint. Three of five canonical examples overwrite a checkpoint: two exhibit `2→8`, one exhibits `4→8`.

The selected Racket target had execution parity but four stale comments caused exact authority-sync failure. I used the public dry-run/apply synchronization flow; only `racket_target.target_code` changed, and executable behavior plus `raw_code` remained unchanged. Evidence: `checks/authority-sync/proposal.json` and `checks/authority-sync/apply.log`.

## D3 — retain and teach two plausible rivals

Four BFS orders, including up/down/right/left, fit all five canonical labels; a prose-based solver can also preserve colored checkpoints. The generator declares `right_before_left` and `preserve_checkpoints` as executable rivals. Ordinary canonical-like scenes intentionally avoid both ambiguity branches, while `semantic_witness` scenes refute both in one compact grid.

I rejected relying on witness frequency alone: a query can remove the only witness from the demonstrations. `lesson_identifiable` therefore evaluates actual demonstration/query splits against the declared rivals.

## D4 — use a four-step production schedule

A two-step alternation was enough to preserve one generic semantic witness under query rotation, but it taught only checkpoint color 2 being overwritten. The final four-step period alternates:

1. canonical maze,
2. tie + overwrite-2 witness,
3. canonical maze,
4. tie + overwrite-4 witness.

Every consecutive four-pair lesson has two witnesses; holding out any one pair leaves one or two witnesses among the three demonstrations. This covers all canonical-observed changed-cell transitions (`0→8`, `2→8`, `4→8`). Evidence: `checks/reference-probe-final-v2.json`, `checks/lesson-census-final-v2.summary.json`, and `checks/lesson-census-schedule-final.summary.json`.

## D5 — advertise only observable exact axes

The old generic axis list contained unrelated palette, corner, texture, and degeneracy controls. The replacement exposes only `grid_h`, `grid_w`, and `scene_pattern`, all recoverable from pixels through `observe_overrides`. Unknown, malformed, out-of-range, boolean-as-integer, negative sample-index, and invalid difficulty inputs are rejected. The complete 4-band × 2-height × 3-width × 2-pattern matrix has 48/48 passing cases in `checks/reference-probe-final-v2.json`.

## D6 — use independent, source-bound verification

Focused tests reimplement BFS rather than calling production rule helpers. They cover all five canonical pairs, exact overrides, invalid calls, deterministic distribution, both semantic rivals, every query rotation, non-mutation, malformed inputs, and live Racket parity. `workspace/reference_probe.py` gives future agents a portable independent oracle and saves source hashes, transition coverage, schedule coverage, and rival parity.

## D7 — limits and failure modes

The sampler is deliberately narrower than every mathematically lawful maze: it targets canonical morphology and a bounded 12–13 by 12–14 training envelope. Declared-rival success is not a proof against all hypotheses. The four-step schedule is tested exhaustively only over declared start residues at fixed seed 0, plus 300 independently seeded lessons; unseen RNG seeds remain finite-sample evidence. Literal transition classes should not be generalized to tasks with permutable color roles without a role-aware exemption.
