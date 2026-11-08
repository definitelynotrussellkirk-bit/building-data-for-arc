# Current notes: `f60cfd11346a`

Selected generator version: `3.1.0`; rule hash: `23823efe5a14`.

## Intended rule

Find the single red `2`, traverse cardinally through cells whose value is `0` or `2`, and recolor each reached `0` to `8`. Every other color is impassable and remains unchanged.

## Current generator contract

- exact axes: `grid_h=7..15`, `grid_w=8..22`, `layout_style=vertical|horizontal|cross`, `accent_color=1|3|4|6|7|9`;
- unknown, mistyped, and out-of-domain overrides raise rather than silently falling through;
- `observe_overrides()` recovers every exact axis from pixels;
- default size sampling covers the full legal domains while weighting canonical-scale profiles;
- every ordinary draw has one critical accent wall colored 1 or 9 and one internal branch-separated pocket;
- `self_check` accepts the broader canonical grammar and does not require every valid input to contain a disconnected zero.

## Reversed decisions

1. **Version 2.1.0:** broad random wall-segment distribution with seven advertised controls. **Replaced** because most controls were inert, negative textures polluted the ordinary domain, and the validator rejected a canonical pair.
2. **Version 3.0.0:** exact full-divider layouts. **Adjusted** because independently sampled cross gate/side could create a one-cell seeded chamber. Exact witness: `counterexamples/cross-one-cell-chamber-v300.json`.
3. **Version 3.0.1:** all official gates green, but a generated half/quadrant-fill shortcut remained. **Hardened in 3.1.0** with a partial internal branch on every layout. Witness: `counterexamples/coarse-partition-only.json`.

## Shortcut evidence

The strongest canonical-fitting rival treats only colors `{3,4,5,6,7}` as blockers. It fits all 5 canonical pairs but fails on the retained accent-1 witness (`counterexamples/canonical-blocker-palette-only.json`). The ordinary sampler refuted it and the coarse-partition competitor on 64/64 direct draws; the final 300-lesson / 1,200-rotation census found zero declared-rival ambiguity.

## Verification

- official battery: 12/12 green (`checks/after-v310/`);
- protected task tests: 172/172 (`checks/task-tests-v310/`);
- override draws: 36,450, zero findings/warnings;
- lesson census: 300 lessons, 1,200 rotations, 1,190 unique inputs, zero materialization/scoring/ambiguity errors;
- final post-repair solve: one revision, 3/3 visible demonstrations, bound to generator SHA `c8b8f277bb56e95db13d75c843bb89e210be443b95cab51bae299a576bcc14eb`.

## Authority

No semantic Racket change. The base record's comment-only `target_code` divergence was normalized to the selected `raw_code`; authority sync and execution parity pass.

## Known limits

The sampler uses a finite border/divider/branch grammar rather than arbitrary mazes. Declared-rival tests and finite census results do not prove uniqueness against every possible heuristic. Add new plausible rivals to the declarations, task tests, `workspace/reference_probe.py`, and census before broadening claims.
## Current reviewer considerations

Source SHA-256: `c8b8f277bb56e95db13d75c843bb89e210be443b95cab51bae299a576bcc14eb`.

# Decisions for `f60cfd11346a`

Final generator: `3.1.0`, SHA-256 `c8b8f277bb56e95db13d75c843bb89e210be443b95cab51bae299a576bcc14eb`.

## D1 — Replace the baseline sampler instead of repairing its dead declarations

**Prior choice.** Version 2.1.0 advertised seven axes, but generation read only `texture` for three negative fixtures and otherwise drew all structure from a private RNG stream. Helpful textures, dimensions, wall count, wall colors, distinct-color count, and density were not exact observable controls. Random short segments also needed rejection sampling and could not reliably expose the canonical palette gap.

**New choice.** Use four exact, independently observable controls: `grid_h`, `grid_w`, `layout_style`, and `accent_color`. Reject unknown keys and invalid types/ranges. Recover every control from output pixels with `observe_overrides()`.

**Reason.** A smaller truthful contract is more useful than broad inert metadata. It makes failures reproducible and lets the override checker prove the declared behavior.

**Evidence.** `checks/after-v310/checks/f60cfd11346a_after_override_results.json`: 36,450 draws, 0 findings/warnings, unknown key rejected.

## D2 — Preserve full size support but weight canonical profiles

**Choice.** Legal height is 7–15 and legal width is 8–22. Defaults include every integer in those domains, with repeated weights around canonical-scale dimensions. Exact overrides remain unweighted and literal.

**Alternatives rejected.** Canonical shapes only would overfit; uniform 7–15 × 8–22 under-hit the known 8×10, 9×10, 10×12, and 9×11 profiles in the small profile-floor gate.

**Failure mode.** Weighting can create repeated size pairs, but layout, branch, seed, and accent variation still produce 1,190 unique inputs in the 1,200-pair final census.

## D3 — Make an unseen accent cell a required critical wall

**Canonical shortcut.** All five canonical pairs can be solved by treating only `{3,4,5,6,7}` as blockers and every other color as passable. That rival has no evidence about colors 1 or 9.

**Choice.** Ordinary draws use accent 1 or 9 and place it as the only gate cell between the seed and another chamber. Exact overrides also allow canonical accent colors 3/4/6/7 for domain coverage.

**Reason.** The input itself must establish that wall behavior is structural, not a memorized list of canonical colors.

**Evidence.** `checks/shortcut-witness-v310/probe.json`: the rival fits 5/5 canonical pairs, disagrees with selected Racket on the exact seed-43 witness, and is refuted on 64/64 ordinary draws. `checks/lesson-census-v310-final.json`: refuted on 100/100 lessons in every difficulty band.

## D4 — Add an internal branch pocket to every layout

**Prior choice (3.0.1).** Full vertical/horizontal/cross dividers plus a colored gate were enough to refute the palette shortcut and pass the official battery.

**New choice (3.1.0).** Add one partial branch inside the seed's coarse half or quadrant, with a same-side zero pocket separated from the seed.

**Reason.** Without the branch, a solver could ignore actual four-neighbor connectivity and fill the entire seed-side half/quadrant. That was a new grammar-specific shortcut introduced by the repair.

**Evidence.** `counterexamples/coarse-partition-only.json`; 64/64 direct draws and 300/300 census lessons refute the declared competitor.

## D5 — Select cross geometry jointly

**Failed intermediate choice.** Version 3.0.0 sampled cross gate row and seed side independently. On minimum shapes it could put the seed into a one-cell quadrant, leaving no zero to recolor.

**New choice.** Enumerate legal `(gate, side, branch orientation, branch coordinate, quadrant)` combinations and sample only candidates with at least two passable cells in the seeded component and at least one cell in the pocket.

**Evidence.** `counterexamples/cross-one-cell-chamber-v300.json` records the exact old witness. The regression spans every small shape band, accent, and 30 seeds; the final override stage has zero self-check/provenance findings.

## D6 — Let `self_check` own the canonical domain, not a generator-specific teaching preference

**Prior choice.** `self_check` required at least one disconnected zero. Canonical train pair 2 is all reachable, so the validator rejected lawful source data.

**New choice.** Validate the actual canonical grammar: shape, ARC colors, solid border, one seed, one accent, no pre-existing 8, and at least one reachable zero. Selectivity and shortcut witnesses are ordinary sampler/semantic-contract guarantees, not universal validity requirements.

**Reason.** A validator must accept every canonical input even when generated lessons intentionally use a stricter teaching subset.

## D7 — Keep the selected Racket semantics unchanged

The authoritative rule already implements the intended cardinal flood through `{0,2}` and matched all canonical outputs. Changing it would expand scope without fixing the generator. I only removed comment-only divergence in the base solution record by setting `target_code` to the selected `raw_code` verbatim. Rule hash remains `23823efe5a14`.

## D8 — Make the rival analysis reusable

Added `workspace/reference_probe.py`. It imports the generator's declared `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, checks every usable canonical pair, creates the exact witness, samples 64 ordinary draws, and optionally verifies the selected Racket output. It writes one source-bound JSON receipt rather than relying on prose.

Usage from `WORK/`:

```bash
python3 run_with_racket.py python3 repo/generators/f60cfd11346a/workspace/reference_probe.py \
  --out checks/shortcut-witness-v310/probe.json --with-racket
```

## D9 — Lesson policy

Production lessons contain 3 demonstrations and one query. The final census used the production sampler and required every labelled pair to serve as the query once (`--rotate-query`). This is stronger than relying on one fixed order, but it still tests only declared rivals and the sampled schedules.

## Known limits

- Topology is a deliberately bounded family, not arbitrary maze generation.
- Ordinary accents are only 1/9; the exact override domain covers 3/4/6/7 as contract cases rather than default lessons.
- The declared-rival set is finite. A future plausible rival should be added to the generator declaration, focused tests, probe, and census.

## 2026-10-24 native parametric admission candidate

Built a source-bound two-setting family under `workspace/parametric/` without changing the approved production generator or canonical rule.

- `mode=canonical` preserves the selected Racket source byte-for-byte.
- `mode=reachable_port_relay` first floods from the unique red seed through `{0,2}`. The input-dependent intermediate is the number `k in {1,2,3}` of color-1 ports cardinally adjacent to that reached component. The rule then selects the `k`-th color-3 anchor in row-major order and floods its separate zero chamber to color 8.
- Exactly three ports are present, but inactive ports border a disconnected pocket. Thus a global-port-count shortcut chooses the wrong chamber. The generated source area is also tuned so an area-modulo shortcut points at a different chamber.
- Inputs are matched across settings, demonstration count is independently 2–6, query count is independently 1–4, query streams are prefix-stable, and the fourth stored query is 30x30.

Evidence and verification:

- `workspace/parametric/evidence/current/audit.json`: 320 finite episodes over seeds 0–31 and all demonstration counts 2–6, zero surviving named query-changing rivals, 74 protected-Racket evaluations, and two checked public exports.
- `checks/f60cfd11346a/qualification/qualification.json`: native status `qualified`, two settings, seeds 0 and 17, 3 demonstrations, 4 queries, 4 jobs, 40 protected-Racket evaluations.
- `checks/f60cfd11346a/causal/witness.json`: source-bound wrong-intermediate witness; active count 2 versus global count 3. `replay.json` status is `reviewer_replayed`.
- Focused plus existing task tests: 184 passed after the addition. Production generator SHA-256 remains `c8b8f277bb56e95db13d75c843bb89e210be443b95cab51bae299a576bcc14eb`.
- Native source inventory: `workspace/parametric/evidence/manifest.json`; adapter and promotion contract: `workspace/parametric/adapter.py`, `workspace/parametric/promotion.json`.

This is reviewer-ready, not owner-accepted. Owner integration, canonical approval, fresh exact-live-source qualification/acceptance replay, and any training admission remain pending.
