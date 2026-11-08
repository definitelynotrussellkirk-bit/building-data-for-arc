# Working notes: d3633a9fb1cd

## Review repair 2026-10-03

Baseline v1.2.1 used one large outer frame, advertised several inert palette/texture axes, accepted unknown overrides, omitted the canonical rule pin, and did not guarantee examples that distinguish geodesic distance from component-restricted Manhattan distance. The canonical task instead uses two separated framed rooms and includes one- and two-seed rooms.

v2.1.0 replaces the sampler with a pixel-observable two-room grammar. Exact controls are `room_depth`, `room_span_a`, `room_span_b`, `gap`, `orientation`, `seed_mode`, and `barrier`; all are constructive in every difficulty band and recoverable with `observe_overrides`. The canonical Racket authority was not changed.

The default three-slot schedule is `detour`, `canonical_single`, `broad`. Every consecutive three-example window therefore contains a true wall-detour counterexample, while the detour and broad branches also provide equal-distance ties. Geometry-keyed seed-pair candidates are cached because exact override auditing revisits the same few dozen room geometries many thousands of times.

Independent probes and the 29 task-local regressions live in `workspace/` and `tests/`. Final-source evidence is under `checks/final-*` and `checks/lesson-probe-100-per-band-final.json` in the review packet.
## Current reviewer considerations

Source SHA-256: `9f4712ba17e90e8418b30ad432ae12825229bc0d23dc52f639a90e12b1355b5f`.

# Decisions for d3633a9fb1cd

## D1 — Preserve the Racket authority

**Choice.** Keep the canonical Racket program unchanged and pin `RULE_HASH = "2c2e8f36a1dd"`.

**Original rationale.** The baseline did not state one beyond implementing blocked geodesic Voronoi. Direct canonical inspection and rule smoke showed the authority already implements the intended behavior: color 5 is impassable, other non-zero colors are seeds, unique shortest-path winners fill zeros, and ties stay zero.

**Alternatives considered.** Change the rule to Manhattan distance, force tie-breaking, or add special handling for rooms. All would contradict canonical outputs and were rejected.

**Probe.** Canonical examples were independently recomputed with BFS and compared with live Racket; authority sync and rule smoke both pass.

**Failure mode / limitation.** Pinning protects against accidental authority drift but cannot prove the written explanation is complete; semantic probes remain necessary.

## D2 — Use the canonical two-room grammar

**Choice.** Generate exactly two separated rectangular color-5 frame components on zero background.

**Original rationale.** Unknown. The baseline used one large outer frame even though all four canonical inputs use two framed rooms.

**Alternatives considered.** Retain one frame and merely adjust dimensions; mix one- and two-frame scenes; reproduce only the four exact canonical shapes. One frame misses the component boundary central to the task, mixing grammars weakens lesson clarity, and exact copying would have poor diversity.

**Probe.** `self_check` parses wall components and frame boxes; all four canonical inputs pass. Profile-floor exact hits occur in every band.

**Failure mode / limitation.** Exactly two rooms is faithful to observed canonical data, not a proof that unseen task variants could never contain more.

## D3 — Geometry controls

**Choice.** `room_depth=4..6`, each room span `2..5`, gap `1..2`, plus horizontal/vertical orientation.

**Rationale.** Depth 4–6, spans 2–4, and gaps 1–2 cover measured canonical profiles. Span 5 and transpose add bounded extrapolation while preserving the same relational rule. Separate spans prevent accidental symmetry from becoming a shortcut.

**Alternatives considered.** Expose raw grid height/width; use arbitrary free-form frames; restrict to canonical dimensions only. Raw dimensions are indirect and ambiguous, free-form walls complicate exact contracts, and canonical-only shapes are too narrow.

**Probes.** `observe_overrides` reconstructs every value from pixels. The override gate accepts all 17,280 draws with zero findings. Distribution and lesson probes report realized min/max and counts.

**Failure modes.** Span 5 and vertical scenes are broad, not canonical-like; `strict_canonical_like` explicitly labels that distinction.

## D4 — Seed modes

**Choice.** Expose `single`, `mixed`, and `double`, with globally distinct seed colors excluding 0 and 5.

**Rationale.** Canonical data includes one- and two-seed rooms. A mixed mode varies the number of local competitors without changing the global rule. Global color uniqueness prevents same-color sources from hiding ownership and tie behavior.

**Alternatives considered.** Keep a raw `n_seeds` axis across the whole grid or allow duplicate colors. A global count does not specify which room contains competition; duplicate colors make equal-distance ownership unobservable.

**Probes.** Tests recover each mode from pixels in all bands and require two-seed rooms to contain a genuine equal-distance cell.

**Failure modes.** The sampler does not explore more than two seeds per room because no canonical example supports that extra complexity.

## D5 — Constructive barriers and seed placement

**Choice.** An optional wall finger remains connected to a frame. If that room has two seeds, seed pairs are selected only when they create both a geodesic tie and a geodesic-vs-Manhattan disagreement.

**Rationale.** A random interior wall often changes appearance without changing ownership. Constructive selection makes the advertised semantic branch observable. For span 2, the finger rotates horizontally because a vertical finger cannot create the intended detour.

**Alternatives considered.** Pure rejection sampling; detached obstacles; complete room splits. Rejection sampling was slow and could fail unpredictably, detached obstacles violate the two-wall-component grammar, and full splits risk seedless chambers.

**Probes.** Independent BFS tests compare ownership; a pinned wall-detour counterexample fails the Manhattan rival. `self_check` rejects seedless open components.

**Failure modes.** The barrier family is intentionally simple. It teaches shortest-path detours but not every possible maze topology.

## D6 — Three-slot curriculum schedule

**Choice.** Cycle `detour`, `canonical_single`, `broad` by `sample_index % 3`; set `EXAMPLES_NEEDED=3`.

**Rationale.** Aggregate witness frequency did not ensure a complete lesson contained a counterexample. An intermediate 100-lesson audit found only 13/100 easy and 36/100 medium lessons refuted the Manhattan rival. The fixed cycle guarantees every consecutive three-demo window includes a detour example while retaining canonical and broad cases.

**Alternatives considered.** Increase random barrier probability; make every example hard; post-hoc reject ambiguous lessons. Probability cannot guarantee lesson identifiability, all-hard lessons lose curriculum breadth, and episode-level rejection belongs in shared assembly rather than hidden inside one draw.

**Probes.** All cyclic starts are tested. The final 100-lesson-per-band audit refutes both declared rivals in every lesson.

**Failure modes.** The guarantee is for the default three-consecutive-example policy. A caller that skips indices or reorders arbitrary samples must perform its own lesson-level check.

## D7 — Exact override contract

**Choice.** Reject unknown keys and invalid types/ranges before creating the generation context; make every declared value constructive in every band.

**Original rationale.** The baseline silently accepted unknown keys and declared domains wider than difficulty-local draw ranges.

**Alternatives considered.** Declare many incompatibility combinations or clamp values. Incompatibilities would make simple geometry controls hard to use; clamping makes accepted overrides dishonest.

**Probes.** Tests cover unknown keys, bool-vs-int distinctions, all single-axis values, and representative cross-axis cases. The exhaustive gate reports zero findings.

**Failure modes.** Future axes must be added to validation, observation, and tests together or the contract will fail loudly.

## D8 — Geometry-keyed candidate cache

**Choice.** Cache lawful two-seed pairs by `(depth, span, blocked, require_detour)`.

**Rationale.** The exact override audit revisits a few dozen geometries across tens of thousands of draws. Recomputing all pairwise BFS maps made 1,000 draws take roughly 11 seconds and caused gate timeouts. The cache reduced the same probe to about 0.74 seconds per 1,000 draws.

**Alternatives considered.** Weaken the override audit, precompute a static table, or choose hand-authored coordinates. Weakening verification hides defects, a static table is brittle, and hand-authored pairs reduce shape coverage.

**Probes.** A regression confirms cache hits; the full 17,280-draw override gate completes and passes.

**Failure modes.** The cache is process-local and bounded to 64 entries. This is sufficient for the current small geometry domain.

## D9 — Independent probes

**Choice.** Add `workspace/reference_probe.py` and `workspace/lesson_probe.py` rather than relying only on generator-internal helpers.

**Rationale.** Tests that call the same oracle as production can reproduce the same bug. The reference probe has a separate BFS implementation and live-Racket parity; the lesson probe uses the generator’s declarations and the actual Racket authority.

**Alternatives considered.** Only unit tests or only battery stages. Neither directly measures complete lesson competitor survival.

**Failure modes.** These probes cover declared rivals and recorded policies, not arbitrary models or all sampling seeds.

## D10 — Verification policy

**Choice.** Treat the unified battery wrapper stall as a tooling failure and rerun every stage independently; do not label the combined command successful.

**Rationale.** A stalled wrapper is not evidence that a stage failed, but it is also not a pass. Individual stage receipts provide complete source-bound evidence.

**Limitation.** Maintainers may still wish to reproduce the wrapper issue. The exact console log is retained.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-66f32fcc6493fdcb:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `9f4712ba17e90e8418b30ad432ae12825229bc0d23dc52f639a90e12b1355b5f`. At disposition, audited bytes match the current source.

### Current decision

Explicit bounded no_issue for earlier clean source9f4712ba report underdocumented deterministic ordered policy. Earlier29tests/60ordered lessons andnew300orderedlessons show no reported production defect. Thisassessment doesnotqualifyarbitraryrotations orerase the separate121/1200rotation finding. No new source approval orowner audit rerun.

### Assessment or prior finding

## d3633a9fb1cd

**No issue found** after checking generator SHA `9f4712ba17e90e8418b30ad432ae12825229bc0d23dc52f639a90e12b1355b5f`.

I reviewed the two-room blocked-geodesic grammar, exact observable controls, independent shortest-path oracle, tie and Manhattan-detour rivals, and the deterministic three-profile teaching schedule. The selected task suite passed 29/29 tests, including canonical parity, exact overrides in every band, hash-seed determinism, real Racket witnesses, and every three-demo window refuting both declared competitors. A separate Racket-backed lesson probe built 20 lessons per band (60 total, 240 unique inputs); all 20/20 lessons in each band refuted every declared competitor and reported zero errors. Evidence: `checks/audit-d363-task-tests/` and `checks/audit-d363-lesson-probe.json`.

The finite audit does not prove there is no undeclared rival, but I did not reproduce a concrete shortcut, invalid override, authority mismatch, or schedule hole. No files for this audit target were modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-66f32fcc6493fdcb-v0001/audit_assets.json), manifest SHA-256 `7b61c875480a43f5d13f538089ff14dd77d46f4c9ff93b4e7bcf8f12d9ccfaf3`.
<!-- arcpuzzles-current-audit-assessment:end -->
