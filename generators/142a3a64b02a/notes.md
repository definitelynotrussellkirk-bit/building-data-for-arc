# Working notes: 142a3a64b02a

## Current native decision — caps followed by residual-component selection

The separate `workspace/parametric/` family preserves exact canonical caps and
adds `residual_largest`. A caps whole straight red components; its remaining red
components and their sizes feed B's largest-component selection (row-major ties)
and cyan-8 recoloring. A wrong-intermediate program selects from original red
objects while keeping correct yellow caps. Production generator and authority
are unchanged. Its open horizontal-only orientation finding remains open;
both native demos explicitly contain both orientations and whole-component
negative examples, avoiding that defect in the native grammar only.

Self-review found that a dominant non-red distractor in every demo concealed an
all-color selection shortcut under the canonical setting. Alternating distractor
dominance repairs this at the same two-demo cost. The retained before/after
Racket regression is in `WORK/checks/142a3a64b02a/audit.json`. Dimension, L-shape,
length and palette variation raises the observed first-demo diversity from
23/32 to 32/32. Source tests and the original failing receipts are retained.

Current verification: 46 scoped tests; 32 seeds × 2 modes × 5 demo counts = 320
episodes; 2,560 pair checks, 319 unique inputs; 26 policies; 66 protected-Racket
evaluations. The broader native grammar includes cycles and degenerate red line
lengths that the production sampler excludes. Owner acceptance remains pending;
finite coverage, no universal uniqueness or training admission. Author self-review.

## Review scope and prior evidence

Assignment `review-b07d394780faf4f1` reviewed the pinned selected baseline whose generator SHA-256 was `d5648ea39714281fb965e808f3a861d6d9e96a02adc778ea91315f6898b39034`. No prior return was used as an implementation lead; `evidence/associated_notes.jsonl` was empty, so all claims below come from the current packet, canonical task row, and retained checks.

## Root cause

The selected Racket program iterates whole 4-connected non-background objects. A red component is transformed only when the component's complete row extent or complete column extent is one-dimensional. The four canonical training pairs contain only straight red components, but the canonical held-out input contains a connected T-shaped red component and leaves it unchanged.

Baseline generator `2.2.0` rejected every non-straight red component. Consequently it could never distinguish the intended whole-component rule from the strongest train-only shortcut, `recolor_each_maximal_run`, which independently caps every horizontal and vertical run inside a branching component. The baseline also exposed axes that were not exact controls, accepted unknown overrides, omitted the canonical `RULE_HASH`, and had comment-only divergence between selected and archival authority text.

## Repair in version 3.0.0

- Pin `RULE_HASH = "ffb5719ce1e2"` and keep the selected Racket semantics unchanged.
- Generate one isolated straight red component and one isolated non-straight red component on every ordinary draw. The negative component cycles through T, L, and stair trees; placement applies rotations/reflections.
- Keep a one- or two-cell connected non-red decoy so color selectivity remains explicit.
- Replace misleading `n_segments`/`texture` controls with exact observable axes: `grid_h`, `grid_w`, and `scene_profile`.
- Add an independent Python rule mirror, named rivals, semantic witnesses, `lesson_identifiable`, mutation fixtures, deterministic replay checks, and strict unknown-override rejection.
- Broaden `self_check` enough to accept all five canonical inputs, including the held-out T, while retaining a deliberately sparse acyclic generated manifold.
- Synchronize the selected archival Racket text exactly with the canonical program by removing only a comment; executable behavior did not change.

## Verification evidence

- Before battery: 5 green, 1 advisory, 6 failed of 12; generator hash `d5648ea39714281fb965e808f3a861d6d9e96a02adc778ea91315f6898b39034` (`checks/before/checks/142a3a64b02a_before_battery_summary.json`).
- Final battery: 12 green of 12; generator hash `9a70d3d7b963e449a97efc672a7af6e906615a2739d66151e27576cf9138c9e2` (`checks/after/checks/142a3a64b02a_after_battery_summary.json`).
- Task-local regression suite: 13 tests, including canonical parity, exact overrides, targeted impostors, shortcut counterexample, generated semantic witnesses, replay neutrality, and the workspace rotation probe.
- Shared lesson census: 300 lessons, 1,200 materialized pairs, 1,200 query rotations, 1,200 unique inputs, zero ambiguous lessons/rotations and zero materialization/scoring errors (`checks/lesson-census-final.json`).
- Task-local schedule audit: 576 consecutive windows over all three bands, seeds `0..31`, starts `0..5`; 2,304 query rotations, 864 unique inputs, zero declared-rival failures (`checks/semantic-audit-final.json`).
- Canonical shortcut evidence: `checks/shortcut/142a3a64b02a/` records that the maximal-run rival fits all four canonical demonstrations and disagrees on the canonical T input; Racket, canonical output, and the independent Python mirror agree.

## Reusable probe

`workspace/semantic_audit.py` reads `LESSON_COMPETITORS` directly from the generator, materializes consecutive windows, holds out every pair once, and reports rival survival, hook mismatches, generation errors, source hashes, and unique-input counts. It is intentionally compact and task-local; it supplements rather than replaces Racket authority checks and the shared source-bound census.

## Deliberate limits

The production sampler is narrower than the full legal rule domain: it emits one straight component, one acyclic non-straight tree from three topology classes, and one small decoy. It does not sample arbitrary cyclic red components, multiple branching components, or every possible non-red object. `self_check` likewise rejects cyclic non-straight red components even though the Racket rule would lawfully leave them unchanged. These restrictions keep lessons sparse and observable, but finite rival passes do not prove unique induction against undeclared rules.
## Current reviewer considerations

Source SHA-256: `9a70d3d7b963e449a97efc672a7af6e906615a2739d66151e27576cf9138c9e2`.

# Decisions for 142a3a64b02a

## D1 — Preserve the canonical Racket semantics

**Original rationale:** the baseline summary described endpoint recoloring but did not capture the held-out whole-component boundary. The selected Racket implementation itself was internally consistent and matched all five canonical pairs.

**Choice:** do not alter executable Racket behavior. Pin rule hash `ffb5719ce1e2` and synchronize the archival selected text exactly by removing a comment-only divergence.

**Alternatives considered:** (a) change the rule to process every maximal run, which would fit the four demonstrations but contradict the canonical held-out output; (b) rewrite the Racket for readability, which would add unnecessary authority risk.

**Probe/failure mode:** canonical parity tests and the supported `apply` receipt show that whole-component behavior leaves the T unchanged. Any semantic Racket rewrite would require revalidating authority and could accidentally convert the task into the shortcut.

## D2 — Put the decisive negative inside every ordinary sample

**Original rationale:** baseline generation intentionally sampled only straight red segments. That made labels correct but made the object-level boundary unteachable.

**Choice:** every draw contains both one straight red component and one non-straight red component. Thus even a one-example demonstration set distinguishes identity and maximal-run shortcuts; any three-example lesson remains identifiable under every query rotation.

**Alternatives considered:** emit a non-straight witness only once per three-step schedule, or rely on random texture probability. Both allow a query holdout to remove the only decisive example—the same class of defect reproduced in audit target `641108b687a1`.

**Probe/failure mode:** `workspace/semantic_audit.py` rotates every pair in 576 production windows. A future edit that makes the negative witness intermittent will produce exact failed seed/start/query records.

## D3 — Use T, L, and stair trees as the negative profile catalog

**Original rationale:** the canonical held-out object is T-shaped; no rationale for a broader baseline negative catalog existed because non-straight objects were rejected.

**Choice:** cycle `tee`, `ell`, and `stair`, with rotations/reflections at placement. These profiles cover branching, a bend, and a multi-bend path while staying sparse and visually legible.

**Alternatives considered:** only T shapes (closest to canonical but easy to overfit), arbitrary random walks (more diversity but harder to observe/control and more likely to self-touch), and solid/cyclic blobs (lawful for the Racket rule but outside the chosen sparse tree grammar).

**Probe/failure mode:** exact `scene_profile` overrides are recovered from the returned grid modulo D4. The limitation is explicit: cycles, degree-4 branches, and arbitrary non-straight components are not sampled.

## D4 — Keep one isolated straight positive component

**Original rationale:** endpoint recoloring needs a visible change; identity-only scenes are unhelpful. Baseline used multiple straight segments but mixed their count with misleading axes.

**Choice:** one length-3..6 horizontal or vertical red component, Chebyshev-separated from the negative object and decoy. This is enough to refute identity without adding counting or grouping distractions.

**Alternatives considered:** multiple positives, length-2 segments, and singletons. Multiple positives add no semantic information here; length 2 makes both cells endpoints and weakens the interior concept; singletons make “two extrema” degenerate.

**Probe/failure mode:** `self_check`, mutation fixtures, and tests reject no-positive, singleton, and length-2 impostors. The generated distribution does not teach interactions among several straight components, although the canonical and rule mirror support them.

## D5 — Replace nominal axes with exact observable controls

**Original rationale:** baseline advertised `n_segments` and texture choices that were not jointly honored, accepted unknown keys, and produced many self-check failures under the override battery.

**Choice:** expose only `grid_h`, `grid_w`, and `scene_profile`. Each can be forced exactly and recovered by `observe_overrides`; unknown or out-of-range values fail loudly.

**Alternatives considered:** keep approximate count/texture axes, or declare many incompatibilities. Both preserve a misleading API. Removing unsupported controls is smaller and more honest.

**Probe/failure mode:** boundary-value override tests cover all four dimension corners and all three profiles; the final override gate has zero findings and rejects unknown keys.

## D6 — Separate production manifold from rule-domain acceptance

**Original rationale:** baseline `self_check` rejected the canonical held-out T because it treated all non-straight red components as defects.

**Choice:** accept sparse canonical-like inputs containing straight and acyclic non-straight red components, while production generation remains the stricter one-positive/one-negative/one-decoy manifold. All five canonical inputs pass.

**Alternatives considered:** make `self_check` exactly mirror the production distribution (would again reject canonical inputs), or accept every rectangular ARC grid (would provide no mutation sensitivity).

**Probe/failure mode:** targeted impostors test ragged/boolean grids, blank scenes, short red lines, and a cyclic 2x2 block. A known limitation is that lawful cyclic red components are rejected despite being identity under the Racket rule.

## D7 — Declare executable rivals and witnesses

**Original rationale:** the baseline semantic gate was advisory because the generator exposed no complete task-domain contract.

**Choice:** declare `identity` and `recolor_each_maximal_run`, with witnesses for a changing straight component and the whole non-straight boundary. `lesson_identifiable` validates labels and detects any declared rival that survives demonstrations but differs on the query.

**Alternatives considered:** prose-only invariants or tests hard-coding rival names. Executable declarations let the shared census and task-local probe consume the same source of truth.

**Probe/failure mode:** finite declared-rival checks do not rule out undeclared hypotheses. Reports explicitly avoid claiming universal identifiability.

## D8 — Add a reusable rotation audit instead of only a one-off script

**Original rationale:** the shared census samples many lessons but does not enumerate every possible schedule start; assignment guidance explicitly asks for task-local probes when the schedule is small.

**Choice:** retain `workspace/semantic_audit.py`, with a test of its public `audit_generator` function. It reads competitors from the generator, rotates every query, counts all failures, retains compact exemplars, and records source hash/domain limits.

**Alternatives considered:** leave only a terminal transcript, or copy a rival list into a notebook. Those would drift and be harder for future agents to replay.

**Probe/failure mode:** 32 seeds × 6 starts × 3 bands produced 576 lessons / 2,304 rotations with zero failures. The probe uses the Python mirror and therefore supplements, rather than replaces, source-bound Racket execution.
