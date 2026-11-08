# Current account: d93294819fca

## Intended rule and authority

Find the 4-connected components of green(3). Exactly one is smallest. Recolor every cell of that component yellow(4), preserving all other cells. The generator is pinned to canonical `RULE_HASH = c778849809a2`; the selected Racket target and archival executable source are now exact-text synchronized, with no behavior change.

## Opt-in native parametric family: gray bridges

`workspace/parametric/adapter.py` now exposes episode-fixed `gray_role=inert|bridge`.
The inert default is byte-for-byte canonical. Bridge mode converts gray to green,
recomputes component membership/area, then paints the new unique minimum yellow.
This separate grammar permits true gray bridges and irregular objects across
8–30-side canvases; production's isolated-gray grammar and controls are unchanged.

The three constructive demos teach a changed winner, a merged winner, and an
untouched winner. Supported counts are 3–6 demos and 1–4 queries; ordinary lessons
have three demos and four novel queries. Two demos are deliberately unsupported
so all three branches can be taught without restricting queries. Demonstration
selection is independent of settings, query count and future inputs; matching
seeds share input streams, and `visible_turn` uses the strict public serializer.

Self-review found a minimum-perimeter shortcut at seed 17: it fit all three
bridge demos but changed queries 0, 1 and 3. The second demo now contrasts a thin
six-cell merged shape (perimeter 14) with a compact seven-cell shape (perimeter
12). The finite rival set includes this shortcut; no extra demo was needed.
The minimal protected-Racket reproducer is `counterexamples/gray-bridge-perimeter.json`.

Checks: 34 focused tests; 251 protected-Racket audit evaluations; native
qualification passed both settings at seeds 0 and 17 (40 further evaluations).
The causal wrong-order witness adds three executions and binds exact qualified
source. Four public episodes pass exact-byte/ID/masking checks. The 12 size probes
include 8×8 and 30×30; the latter have 16 original components and 323–537 occupied
cells. A bounded 32-seed Python sampler check completed 32/32, using at most six
teaching attempts. These counts have different scopes and are not one exhaustive
correctness or training-benefit claim. Current compact receipts and the source
inventory are in `workspace/parametric/evidence/`; full private cases and native
qualification travel in this return's `checks/d93294819fca/`.

Status: native-ready reviewer return; owner exact-source acceptance remains the
next action after integration. Production source SHA remains
`f80fb929d42edcd26e1739fdebadad2d96f4a5801b045036b8b23489a4828f38`.
The sampler separates nonjoining objects diagonally; it does not teach 4 versus 8
connectivity. No production size override or training activation was added.

## Reversed baseline decisions

Version 1.2.0 advertised palette, blob-count, palette-size, position, color-count, density, and texture axes that ordinary generation mostly ignored. It also included unlawful negative fixtures in the ordinary texture domain and required exactly one gray marker, rejecting a lawful canonical input containing two. Version 2.0.0 retires those false controls and exposes only four observable axes: `grid_h`, `grid_w`, `component_profile`, and `marker_count`.

The baseline's independent examples also left a canonical shortcut: all five canonical outputs recolor a size-two component. The new four-phase lesson schedule deliberately includes winner sizes one and three and rotates the winner through first, middle, and last discovery ranks.

## Current grammar

- canvas: height 8–12, width 10–14;
- two to four separated green components, each connected and confined to a sampled 3×3 corner zone;
- profiles: `(2,3,4)`, `(2,3,5)`, `(1,3,4)`, `(3,4,5)`, `(2,4)`, `(1,2,3,5)`;
- exactly one minimum component;
- zero to two isolated gray(5) markers;
- unknown/retired controls and invalid scalar requests are rejected;
- generation is deterministic and does not touch global RNG state.

Strict canonical-like inputs use one of the five canonical canvas shapes, profile `(2,3,4)` or `(2,3,5)`, and one or two markers. The declared strict floor is 0.40; measured after repair is 287/600 (47.8%).

## Lesson contract

A production lesson has three ordered demonstrations and one query. The four schedule phases use winner sizes `2,1,2,3` and row-major winner ranks first, middle, last, middle. Declared competitors are first component, last component, largest component, and fixed size two. The last competitor is retained as `CANONICAL_SHORTCUTS.fixed_size_two` because it fits all five canonical pairs.

Evidence on final generator SHA `f80fb929d42edcd26e1739fdebadad2d96f4a5801b045036b8b23489a4828f38`:

- 109 task regressions pass;
- aggregate battery 12/12 green;
- canonical support 5/5 and exact profile floor 60/60;
- override matrix 13,950/13,950 accepted with zero findings;
- fixed-seed schedule census 12 lessons / 48 rotations, zero ambiguity;
- wider census 300 lessons / 1,200 rotations, zero ambiguity among declared and searched rivals.

The minimal fixed-size-two reproducer is `counterexamples/fixed-size-two.json`.

## Known limits and open findings

The rival set is finite, so these checks do not prove universal identifiability. Corner-zone placement and component sizes at most five are conservative and do not cover arbitrary central placement, close-but-separated layouts, or larger canonical-like objects. Expanding those dimensions should preserve exact observer semantics and rerun schedule-rotation evidence.

The post-repair visible-only solve passed all three visible examples in one revision, but earlier rule exposure was correctly declared. No training approval is implied by this review packet.
## Current reviewer considerations

Source SHA-256: `f80fb929d42edcd26e1739fdebadad2d96f4a5801b045036b8b23489a4828f38`.

# Decisions: d93294819fca

## D1 — Preserve the rule; pin and synchronize its authority

**Prior choice:** the baseline generator had no `RULE_HASH`; the selected Racket `target_code` differed from archival `raw_code` only by a comment. The original reason is unknown.

**Decision:** keep the canonical rule unchanged, set `RULE_HASH = "c778849809a2"`, and use the packet's source-bound authority-sync flow to remove only the comment difference from `target_code`. Preserve `raw_code`, canonical puzzle rows, and expected outputs.

**Alternatives rejected:** changing the Racket rule to match the baseline generator; editing canonical examples; or tolerating multiple active exact source strings. All would weaken provenance or conceal the mismatch.

**Probe/evidence:** `checks/authority-sync-proposal.json`; `checks/after-final/checks/d93294819fca_after_authority_sync.json`; 120/120 Racket rule-smoke applications.

**Failure mode:** any future authority change requires a new rule hash and a full parity/canonical review; this patch must not be treated as permission to alter rule semantics.

## D2 — Replace false breadth with four truthful controls

**Prior choice:** version 1.2.0 advertised canvas, palette, blob count, palette size, position, color count, density, and texture controls. Most were accepted but ignored, and unlawful negative fixtures appeared in the ordinary texture domain. The original rationale is unknown.

**Decision:** expose only `grid_h`, `grid_w`, `component_profile`, and `marker_count`. Each control changes an observable property, is reconstructed by `observe_overrides`, and is covered exhaustively enough for the shared 13,950-draw override matrix. Retired/unknown controls are rejected rather than silently accepted.

**Alternatives rejected:** animating unrelated palette/color axes, because the authority depends specifically on green(3) objects and yellow(4) output; keeping degenerate textures in the production domain, because they violate the unique-minimum rule; retaining `n_blobs` plus free component sizes, because many combinations would be impossible or would hide coupling.

**Probe/evidence:** focused override regressions; `checks/after-final/checks/d93294819fca_after_override.log`; defect-lint zero findings.

**Failure mode:** the finite profile axis is less flexible than independent object-count/size controls. Adding a profile requires updating `PROFILE_SIZES`, observer support, tests, and semantic coverage together.

## D3 — Encode component sizes as named lawful profiles

**Prior choice:** the baseline always emitted three components with hand-coded shapes of nominal sizes 5, 3, and 1-or-2, despite claiming broader blob-count support.

**Decision:** use six named profiles: canonical `(2,3,4)` and `(2,3,5)`; counterfactual `(1,3,4)` and `(3,4,5)`; two-object `(2,4)`; and four-object `(1,2,3,5)`. Every profile has one unique minimum and maps bijectively through the observer.

**Alternatives rejected:** arbitrary size tuples, which would enlarge validation and placement complexity without evidence of training value; requiring all sizes distinct beyond the unique minimum, which is stricter than the authority; allowing tied minima, which makes the rule underspecified.

**Probe/evidence:** all six profiles round-trip in every band; canonical inputs map to the two canonical profiles; `self_check` rejects unsupported/tied profiles.

**Failure mode:** only sizes one through five are represented. Larger-object morphology is a known scope limit rather than a silent claim.

## D4 — Use separated 3×3 corner zones for robust geometry

**Prior choice:** placements were partly fixed and partly sampled in narrow ranges, with no executable separation contract.

**Decision:** place each connected shape inside one of four 3×3 corner zones, sampled without replacement. This guarantees room for all legal shape variants and prevents inter-component diagonal/orthogonal contact. Shape identity still varies under the dihedral group.

**Alternatives rejected:** rejection-sampling arbitrary locations, which complicates exact override behavior and can produce flaky failures on small canvases; fixed single shapes, which would reduce morphology diversity.

**Probe/evidence:** 300-pair diversity is 100% exact-unique input/output; self-check and destructive-mutation probes pass; no generation crashes across the battery or override matrix.

**Failure mode:** the positional support is structured and underrepresents central/nearby objects. This is explicitly documented and should be expanded only with a placement proof and tests.

## D5 — Treat gray markers as inert, optional context

**Prior choice:** `self_check` required exactly one gray marker, but canonical data contains both one and two markers.

**Decision:** production permits zero to two isolated gray(5) cells; strict canonical-like support requires one or two. Markers cannot touch green or one another, and the rule ignores them.

**Alternatives rejected:** exactly one marker (contradicts canonical support); unrestricted gray cells (could merge into distracting structures or invalidate observer semantics); removing gray entirely (loses canonical context).

**Probe/evidence:** 5/5 canonical inputs accepted; marker counts 0/1/2 round-trip in every band; profile floor 60/60 exact.

**Failure mode:** no production lesson explores more than two markers or non-isolated marker arrangements.

## D6 — Build an ordered four-phase anti-shortcut curriculum

**Prior choice:** the baseline produced examples independently and gave no lesson-level teaching guarantee. Because every canonical winner has size two, a fixed-size-two rival fit all canonical pairs.

**Decision:** declare `EXAMPLES_NEEDED = 3` and `LESSON_SCHEDULE_PERIOD = 4`. Consecutive phases use profiles `canonical_234`, `varied_134`, `canonical_235`, `varied_345`; winner sizes are `2,1,2,3`, and winner rank is first, middle, last, middle. A normal lesson has three ordered demonstrations and one query.

**Alternatives rejected:** random independent profile selection, because a small lesson can accidentally omit the size/position witness; only canonical profiles, because that preserves the fixed-size-two shortcut; two demonstrations, because query rotation can leave an unrefuted rank rival.

**Probe/evidence:** 12/12 exhaustive fixed-seed schedule lessons and 48/48 rotations pass; 300/300 wider lessons and 1,200/1,200 rotations pass. Evidence: `checks/schedule-period-s0.summary.json`, `checks/lesson-census-100.summary.json`.

**Failure mode:** the period declaration is trusted as code and the rival set is finite. Fixed-seed residue enumeration does not exhaust all random support or all possible hypotheses.

## D7 — Declare finite semantic witnesses and rivals

**Prior choice:** no semantic contract existed.

**Decision:** declare witnesses for smallest-not-first, smallest-not-last, smallest-not-largest, and winner-not-size-two. Declare corresponding first, last, largest, and fixed-size-two competitors. Preserve `fixed_size_two` under `CANONICAL_SHORTCUTS` because it demonstrably fits all five canonical pairs.

**Alternatives rejected:** declaring only the known size shortcut, which would miss position shortcuts; relying solely on correct labels, which does not show that a lesson distinguishes plausible rules; claiming unique identifiability, which the finite checks cannot prove.

**Probe/evidence:** semantic gate and both lesson censuses; minimal reproducer `counterexamples/fixed-size-two.json`.

**Failure mode:** unlisted rivals may survive. The contract is an executable lower bound on lesson quality, not a theorem about all programs.

## D8 — Set the strict canonical floor to 0.40

**Prior choice:** no strict-support declaration existed.

**Decision:** two of four default phases are intentionally canonical profiles, so the expected strict fraction is about 0.50. Set `MIN_STRICT_FRAC = 0.40` to leave finite-sample margin while still rejecting a curriculum that drifts mostly out of canonical support.

**Alternatives rejected:** 0.50 exactly, which is needlessly brittle under randomized canvas schedules; a lower/no floor, which would permit semantic counterexamples to crowd out canonical-like examples.

**Probe/evidence:** measured 287/600 = 47.8%, with per-band rates 46.5–49.5%; exact canonical profile support 20/20 per band.

**Failure mode:** passing the floor does not establish matching joint canonical morphology; it only enforces the declared strict predicate.

## D9 — Validate requests strictly and preserve deterministic purity

**Prior choice:** booleans, floats, strings, negative sample indices, unknown bands, and ignored controls could pass into generation.

**Decision:** require an exact nonnegative integer `sample_index`, known difficulty, known override names, exact integer scalars (not booleans), and in-range/profile values. Use only context-derived RNG streams; do not mutate Python's global RNG.

**Alternatives rejected:** coercion, because it hides caller bugs and weakens reproducibility; permissive unknown keys, because they produce false experimental claims.

**Probe/evidence:** task-local scalar/unknown-key regressions; shared defect lint; deterministic replay/global-RNG test.

**Failure mode:** callers relying on previous silent coercion or dead controls will now receive explicit exceptions; that is intentional API correction.
