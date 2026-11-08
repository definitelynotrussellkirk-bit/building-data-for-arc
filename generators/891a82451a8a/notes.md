# Working notes: 891a82451a8a

## Review repair

The imported `2.0.2` sampler rejected the canonical background color `7`, exposed stale or inert controls, lacked `RULE_HASH`, admitted degenerate texture aliases, and provided no executable lesson rivals or task-local tests. Its fixed-index seed family also collapsed to four outputs.

The repaired `3.0.0` sampler exposes only pixel-observable controls:

- `grid_h`, `grid_w`: exact `5..18` controls, with full default support and an explicit canonical-size branch.
- `bg_color`: exact nonzero ARC color `1..9`.
- `seed_color`: exact member of `(0, 5, 2, 8, 9, 6, 1, 3, 4)`, distinct from the background.
- `seed_region`: one of four disjoint recovered regions: corner, edge, center, interior.

Unknown, mistyped, out-of-range, and jointly impossible overrides fail loudly. `observe_overrides` recovers every advertised exact axis from pixels.

## Rule-domain boundary

A retained counterexample showed why background `0` is not lawful for the selected Racket authority. For an `8 × 6` grid of zeros with a single `5` at `(4, 2)`, the selected Racket `mode` primitive ignores zeros, treats `5` as the background, and anchors on the first zero cell. The independent Python mirror originally treated zero as the modal background, so the outputs disagreed. The repair excludes background `0` in generation, overrides, validation, and the helper mirror. Seed color `0` remains lawful.

## Teaching contract

`EXAMPLES_NEEDED = 2`. Declared executable competitors are:

- Chebyshev distance instead of Manhattan distance.
- Fixed cycle phase `0` instead of phase from seed color.
- Fixed grid-center anchor instead of the actual seed.
- Canonical-profile memorization: behave correctly only on `8 × 8`, background-`7` inputs.

The sampler schedules phase, anchor region, palette, and off-canonical profiles so ordinary two-demo lessons refute those declared competitors. Task-local tests exhaust 36 tested cyclic starts across every difficulty setting and every query rotation. This is finite evidence against declared rivals, not a proof of unique induction against all possible programs.

## Authority synchronization

The two selected base records had behaviorally equivalent but text-divergent active `target_code`. Their active fields were synchronized byte-for-byte to the canonical `program_solution` with rule hash `635140e0e1b3`. The older executable `raw_code` fields remain preserved as archival variants.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl` when present; no prior selected-task return was used as repair evidence in this packet.
## Current reviewer considerations

Source SHA-256: `e7ba6890d0edbb7fcf6194dc8e553e6897bbca2773b594e7cd1e1b571afb65a9`.

# Decisions for 891a82451a8a

Final generator SHA-256 is recorded by the final checks and solve episode. The authoritative rule hash remains `635140e0e1b3`.

## D1 — Preserve the authoritative transformation

**Choice.** Keep the rule as Manhattan distance from the unique seed through the fixed cycle `(0,5,2,8,9,6,1,3,4)`.

**Rationale.** All six canonical labelled pairs and selected Racket execution agree. The repair target was distribution/teaching quality, not a new task.

**Alternatives rejected.** Chebyshev distance, fixed phase, fixed center, and profile memorization each fit some superficial cues but disagree on retained generated witnesses.

**Probe.** `checks/question-shortcut/witness.json`, final `rule_smoke`, and task-local canonical tests.

## D2 — Lawful input grammar

**Choice.** Generate rectangular `5..18 × 5..18` grids with one strict modal nonzero background and exactly one seed whose color is in the fixed cycle and differs from the background.

**Rationale.** This keeps the task simple while materially varying scale, palette, phase, and anchor. Every returned grid has a unique, recoverable semantic seed.

**Rejected alternative: background 0.** A concrete `8 × 6` zero-background input with seed 5 showed that the selected Racket `mode` primitive ignores zeros, selects 5 as the mode, and then anchors at the first zero. The independent intended mirror therefore disagreed. Background 0 is rejected by generation, overrides, validation, and the review helper; seed color 0 remains lawful. Evidence: `checks/repro_mirror.py` and `checks/repro_mirror.log`.

**Limit.** This is the selected runtime's lawful domain, not a claim that every abstract Manhattan-ring program must exclude zero backgrounds.

## D3 — Exact public controls

**Choice.** Expose only `grid_h`, `grid_w`, `bg_color`, `seed_color`, and `seed_region` (`corner|edge|center|interior`). Every accepted exact control is visible in pixels and recoverable by `observe_overrides`.

**Rationale.** The imported generator advertised stale/inert axes and an unprobeable color declaration. The replacement fails closed on unknown, mistyped, out-of-range, and jointly impossible requests. Equal explicit background/seed colors raise a structured incompatibility.

**Alternatives rejected.** Texture aliases, edge-avoidance flags, decoy-seed flags, and generic bias names were removed because they were either degenerate, inert, or not exactly observable.

**Probe.** Final override stage and `test_every_exact_axis_is_observable_and_honored`.

## D4 — Default distribution and canonical envelope

**Choice.** Give each difficulty band full legal size support with band-specific weighting, schedule all nonzero backgrounds, all seed phases, and all four seed regions, and reserve a deterministic one-third branch for exact `8 × 8` two-color profiles.

**Rationale.** The first repaired version's one-quarter branch produced only 13/60 pinned exact-profile hits (21.7%), below the checker floor. A test was added first; changing to one third yields at least 5/20 hits in every pinned band while retaining broad scale diversity.

**Alternatives rejected.** Always-canonical sampling invites memorization; a sparse one-per-band branch met the prose minimum but failed the actual envelope-rate gate; a half-canonical branch was unnecessary.

**Evidence.** `checks/after-attempt2-profile-floor/`, `checks/task-tests-red3-profile-floor.log`, `checks/task-tests-green3-profile-floor.log`, and final profile-floor evidence.

## D5 — Lesson contract

**Choice.** Set `EXAMPLES_NEEDED = 2` and declare executable rivals for Chebyshev metric, fixed-zero phase, fixed-grid-center anchoring, and canonical-profile memorization. Schedule consecutive phases/regions/profiles so ordinary two-demo lessons refute these declared competitors.

**Rationale.** Correct individual labels do not guarantee a teachable rule. These rivals capture the strongest observed shortcuts: wrong metric, ignoring seed color, ignoring seed location, and canonical-envelope memorization.

**Ordering/query policy.** Production ordering is deterministic by sample index. Task-local tests cover 36 cyclic starts, four difficulty settings, and every rotation of a three-pair lesson. The public semantic gate and the 100-per-band rotating census are reported separately.

**Limit.** Finite declared-rival checks do not prove unique induction against all programs or every possible schedule start.

## D6 — Authority text synchronization

**Choice.** Synchronize the active `target_code` in both selected base records byte-for-byte to canonical `program_solution`; retain their older executable `raw_code` fields unchanged as archival variants.

**Rationale.** The active programs were behaviorally equivalent but exact-text divergent, causing authority and defect-lint blockers. No transformation semantics changed.

**Evidence.** `checks/targeted-authority-sync/`, `checks/targeted-defect-lint-sync/`, and final authority evidence.

## D7 — Durable tooling and tests

**Choice.** Add `workspace/reference_probe.py` and 49 task-local regression tests.

**Rationale.** Future agents need an independent analyzer/output mirror, canonical loader, override observer, and competitor ambiguity helper rather than re-deriving the contract. Tests retain the three red-to-green discoveries: missing generator contract, zero-background Racket mismatch/fixed-index collapse, and pinned profile-floor rate.

**Limit.** The Python mirror is diagnostic; selected Racket execution remains authoritative.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/891a82451a8a/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Current parametric proposal — direct waves and corner relay

`workspace/parametric/` adds a native adapter with episode-fixed `mode=direct`
or `corner_relay`. Direct returns the selected canonical program byte-for-byte;
the production generator, reference, and approval remain unchanged. Relay derives
the four corner phases of the first wave, selects the lowest phase with a
row-major tie break, and uses that corner and phase for a second wave. The full
first-wave grid can be reduced to four corner values; those input-dependent
values, rather than an indispensable full-grid simulation, are the causal claim.

The parametric grammar extends dimensions to 5..30 while retaining the one-seed,
nonzero-background contract. Independent counts support 2..6 demos and 1..8
queries, with three/four as the ordinary request. Inputs are matched across modes.
The first four query shapes include 5×5 and substantive full-output 30×30 cases.

Self-review reproduced two teaching holes: omitting an unshown corner and using
an alternative corner priority on a previously unobserved tie. The originals
remain in `workspace/parametric/evidence/current/*before.private.json`.
The repair constructs two demos refuting 29 core rivals, adds missing winning
corners in demos three and four, and filters queries against four corner-omission
and 23 alternative priority rules fitted only to demos. Short lessons query only
taught winning corners; four-demo lessons cover all four. This preserves the
complete family while explicitly limiting short-lesson corner extrapolation.
The reusable `audit.py` replays both old failures and repaired lessons through
protected Racket, separately reporting Python-only sampler counts.

Current verification is in `workspace/parametric/evidence/current/` and the
returned `checks/891a82451a8a/`. Native qualification and the causal witness bind
the exact source. Reviewer-ready is not owner acceptance or training admission.
After integration, the next action is fresh owner qualification and acceptance;
future edits must regenerate the inventory and execution evidence.
