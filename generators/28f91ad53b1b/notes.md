# Working notes: 28f91ad53b1b

## Final selected design

Version `3.1.0`, generator SHA-256 `74d9067b1305a5990585f0ddd5739405b51d92c2d46f8eeb4379a6632d2e2dd3`.

The repair replaced an unpinned, weakly recoverable distribution with a five-profile semantic curriculum. The executable law was not changed. `RULE_HASH` is pinned to `443a7da44ab8`; the selected Racket `target_code` was normalized to the existing `raw_code` after confirming that the only prior difference was two comments.

Every five-example window contains all profiles. The initial version still failed when the sole tie or wall-detour witness was held out as query. Final profiles deliberately provide redundant evidence: `open_voronoi` backs up `tie_order`, and `seedless_rooms` backs up `wall_detour`. The final production census found 0 ambiguities in 300 ordinary lessons and 1,800 query rotations against all declared competitors.

## Retained evidence

- Before battery: `checks/before/` — 5 green, 2 advisory, 5 failed.
- Final battery: `checks/final-battery/` — 12/12 green.
- Final task tests: `checks/task-tests/` — 49/49 pass.
- Final census: `checks/lesson-census-final2.json.gz` plus compression manifest.
- Independent source-bound probe: `checks/reference-probe-final.json`.
- TDD failures: `checks/task-tests-red-console.log`, `checks/rotation-test-red-stage-console.log`, and `checks/seedless-backup-red-console.log`.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `74d9067b1305a5990585f0ddd5739405b51d92c2d46f8eeb4379a6632d2e2dd3`.

# Decisions for `28f91ad53b1b`

These decisions describe the final generator at SHA-256 `74d9067b1305a5990585f0ddd5739405b51d92c2d46f8eeb4379a6632d2e2dd3`. Baseline rationale is marked unknown when it was not recoverable from retained notes.

## D1 — Pin the authority instead of rewriting the rule

**Choice.** Declare `RULE_HASH = "443a7da44ab8"`, retain the existing wall-aware Voronoi law, and make selected `target_code` byte-for-byte equal to retained executable `raw_code`.

**Original rationale.** The baseline omitted the rule pin; why is unknown. The two Racket texts differed only by comments.

**Alternatives considered.** Rewrite the Racket for speed; leave the comment-only mismatch; change canonical data. Rewriting risked a semantic regression, leaving the mismatch failed authority sync, and canonical changes were unnecessary.

**Probe.** Canonical independent BFS, `rule_mirror`, rule smoke, authority sync, and public `Catalog.apply` on three canonical grids plus the exact tie witness.

**Failure modes / limits.** Byte identity prevents this specific drift but does not prove future semantic equivalence after edits. The Racket remains intentionally unchanged.

## D2 — Keep a canonical-style input envelope

**Choice.** Generate 8–10 rows by 10–12 columns, with an all-zero outer border and an inset color-5 chamber frame.

**Original rationale.** Baseline claimed canonical-like support but drifted from the observed canonical dimensions/morphology; exact original reasoning is unknown.

**Alternatives considered.** Arbitrary open mazes; larger grids; fixed canonical dimensions only. Arbitrary mazes broaden coverage but make exact semantic witnesses and control recovery harder; larger grids add no needed concept; fixed dimensions reduce useful variation.

**Probe.** Profile-floor battery, all boundary overrides, `self_check` mutation tests, and 300-lesson census.

**Failure modes / limits.** The generator does not cover every mathematically valid wall arrangement. It deliberately covers a compact teachable subdomain.

## D3 — Use four exact recoverable axes

**Choice.** Public controls are exactly `grid_h`, `grid_w`, `n_seeds`, and `texture`. Integer ranges are `8..10`, `10..12`, and `2..5`; texture has five named values. Every Cartesian product is constructive in every band.

**Original rationale.** Baseline exposed `position_bias` and texture declarations that were singleton, overlapping, or not reliably observable. Their original rationale is unknown.

**Alternatives considered.** Keep advisory/fuzzy controls; declare incompatibility tables; expose internal wall coordinates. Fuzzy controls violate exact override semantics; incompatibilities were avoidable; wall coordinates overfit implementation details.

**Probe.** Battery override stage, 120 independent boundary cases, task-test cross-products, and `observe_overrides` round trips.

**Failure modes / limits.** Texture recovery relies on the declared topology signatures; adding a new topology requires updating the observer and tests together.

## D4 — Five semantic profiles, not cosmetic textures

**Choice.** `open_voronoi`, `wall_detour`, `tie_order`, `seedless_rooms`, and `mixed_rooms` each carry a distinct rule-discriminating obligation.

**Original rationale.** Baseline texture names overlapped and did not form a semantic curriculum; exact original intent is unknown.

**Alternatives considered.** Random walls with post-hoc filtering; one universal template; many cosmetic texture labels. Random filtering made guarantees and reproducibility weaker; one template encouraged shortcuts; cosmetic labels repeated the baseline problem.

**Probe.** Named profile reproducers, semantic witnesses, declared-rival outputs, all cyclic starts, final battery semantic gate, and reference probe.

**Failure modes / limits.** Profile names are task-local contracts, not claims that these five topologies exhaust all useful examples.

## D5 — Five demonstrations plus one query with redundant witnesses

**Choice.** Keep `EXAMPLES_NEEDED = 5`; use a five-cycle schedule; make `open_voronoi` back up `tie_order` and `seedless_rooms` back up `wall_detour` so every six-pair query rotation retains a counterexample.

**Original rationale.** The packet required generated lessons to teach the law and recommended rotation checks when permitted. The first repair assumed one witness per profile was enough; the census disproved that assumption.

**Alternatives considered.** Increase to six or more demonstrations; forbid query rotation; rejection-sample ambiguous lessons. More examples increase cost, forbidding rotation weakens downstream flexibility, and rejection sampling hides rather than structurally fixes the curriculum.

**Probe.** Initial census found 334/1,800 ambiguous rotations; first backup repair left 22/1,800; final census and exhaustive task tests report 0/1,800.

**Failure modes / limits.** Redundancy is established against declared rivals. A new rival may require another independent witness or schedule revision.

## D6 — Seed counts by semantic role and difficulty

**Choice.** `open_voronoi`, `wall_detour`, and `tie_order` default to two seeds in all bands. `seedless_rooms` uses 3/4/5 seeds for easy/medium/hard; `mixed_rooms` uses 3/3/4.

**Original rationale.** Baseline seed-count schedule and its relation to difficulty were not documented.

**Alternatives considered.** Random 2–5 everywhere; monotone seed count for every profile; two seeds only. Random counts interfered with exact witnesses; monotone counts add complexity where it does not teach a new concept; two seeds cannot refute “first two seeds only.”

**Probe.** All bands × all cyclic starts, exact override cross-products, named witness tests, and final census.

**Failure modes / limits.** Difficulty here changes compositional load, not grid dimensions or an independently calibrated human difficulty score.

## D7 — Anchor colors 2 and a varying secondary, then add distinct extras

**Choice.** Every grid contains seed color `2`, a secondary from `{3,4,6,7,8,9}`, and distinct extras from legal nonzero/nonwall colors. In tie profiles, smaller color `2` is placed row-major later than the larger seed.

**Original rationale.** Canonical examples use color `2` with `3` or `4`; baseline color rationale was not recorded.

**Alternatives considered.** Fixed canonical colors only; fully random colors; position-ordered colors. Fixed colors invite palette shortcuts, fully random colors can lose canonical support, and position-ordered colors fail to teach numeric tie-breaking.

**Probe.** Canonical-profile checks, exact tie reproducer, distribution diversity, and public-Racket tie witness.

**Failure modes / limits.** Color 5 remains reserved for walls and 0 for background; the generator does not test malformed repeated-color seeds because the selected grammar forbids them.

## D8 — Attach every seed to the connected wall network

**Choice.** Seed locations touch the inset wall/frame network, producing one nonzero component while preserving one-cell colored markers.

**Original rationale.** The baseline advertised an object-count expectation inconsistent with emitted grids. Canonical morphology suggested one connected nonzero object when walls and seeds are counted together.

**Alternatives considered.** Allow detached seeds; remove object-count claims; connect seeds with colored lines. Detached seeds failed the intended strict profile, dropping the claim hides morphology drift, and colored lines would cease to be one-cell seeds.

**Probe.** `_nonzero_component_count`, strict profile, self-check mutation tests, and final distribution gate.

**Failure modes / limits.** This is a morphology constraint, not required by the mathematical rule. It narrows the generated domain intentionally.

## D9 — Structural witnesses instead of probabilistic luck

**Choice.** Builders construct exact wall/tie/seedless situations and then add controlled variation around them.

**Original rationale.** Unknown; baseline relied more heavily on random placements and prose claims.

**Alternatives considered.** Generate randomly until a witness appears; merely tag profiles in metadata. Rejection loops can be slow/nonterminating at override boundaries, and tags do not prove the grid contains the claimed distinction.

**Probe.** Witness functions recompute intended and rival outputs; task tests assert exact differing cells/properties; independent probe replays from source.

**Failure modes / limits.** A bug shared by builder and witness could mask an error, so the retained probe uses a separate BFS implementation and public Racket checks.

## D10 — Declare four plausible rivals

**Choice.** Retain executable competitors: row-major tie-breaking, component-local Manhattan distance, global Manhattan distance, and using only the first two seeds. Declare row-major tie-breaking as the canonical-fitting shortcut.

**Original rationale.** Baseline had no executable semantic contract.

**Alternatives considered.** A much larger enumerated rule library; prose-only rivals; no canonical shortcut declaration. A large library was unnecessary for this repair, prose cannot gate lessons, and omitting the known canonical shortcut would overstate canonical identifiability.

**Probe.** Canonical pair fit, all lesson starts, all query rotations, 300 production lessons, and source-bound reference probe.

**Failure modes / limits.** These are strong plausible rivals, not an exhaustive program synthesis search.

## D11 — Reject invalid controls loudly and avoid global RNG state

**Choice.** Unknown override keys raise `TypeError`; wrong value types/ranges raise; generation uses named context RNG streams and does not mutate Python global random state.

**Original rationale.** Baseline behavior could swallow unknown controls; original intent is unknown.

**Alternatives considered.** Ignore unknown keys for forward compatibility; coerce strings/floats; use module-level random. Silent acceptance makes experiments irreproducible, coercion hides caller bugs, and global RNG introduces order dependence.

**Probe.** Invalid-control tests, deterministic replay, fresh-object checks, global-RNG purity, and input-purity checks.

**Failure modes / limits.** Strict calls may break callers that depended on undocumented permissiveness; that is intentional contract tightening.

## D12 — Add a reusable independent reference probe

**Choice.** Add `workspace/reference_probe.py`, which imports public reviewer support, derives declared rivals from the generator, checks canonical data, all schedule starts/rotations, override boundaries, and optional public Racket execution.

**Original rationale.** No retained task-local independent probe existed.

**Alternatives considered.** Rely only on battery logs; duplicate expected grids in tests; import private runner internals. Battery smoke samples are too small for cyclic guarantees, duplicated labels become stale, and private imports are unsupported.

**Probe.** `checks/reference-probe-final.json` records probe hash, generator hash, counts, exact counterexample, and Racket receipts.

**Failure modes / limits.** It is finite and source-bound; it does not enumerate all random seeds or all possible rival programs.
