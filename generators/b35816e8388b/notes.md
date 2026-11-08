# Working notes: b35816e8388b

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-03 review — assignment review-705b00dde5af0be2

### Baseline defects

The original sampler passed basic generation and Racket execution, but its full before battery failed lint, strict defect lint, and the override contract. The decisive evidence is under `checks/before/`:

- no pinned `RULE_HASH`;
- an unprobeable `orientation` declaration and singleton/diagnostic-only pseudo-axes;
- helpful textures that were byte-identical to the untextured draw;
- ordinary texture values that included malformed negative fixtures;
- unknown override keys accepted silently;
- no executable semantic contract for the canonical ambiguity.

All three canonical input/output pairs place the midpoint at the canvas center. Therefore the wrong rule “ignore the endpoints and always paint the grid center” fits 3/3 canonical pairs. This was treated as a curriculum defect, not a Racket-rule defect.

### Selected repair

- Pinned `RULE_HASH = "259314225434"`; the selected Racket authority was not edited.
- Replaced fictitious palette/texture/density controls with four observable geometry axes: exact height, width, orientation, and even span.
- Broadened lawful spans to `2|4|6|8|10|12`, covering the canonical span 6 as well as shorter and longer cases.
- Added strict difficulty and override validation, exact post-generation observability, and structured `IncompatibleGeometry` failures for impossible joint requests.
- Added fail-closed structural analysis, `self_check`, `strict_canonical_like`, and an independent Python `rule_mirror`.
- Added a deterministic three-profile schedule (`canonical_anchor`, `off_center`, `broad`). Any three consecutive examples contain all profiles. Explicit overrides remain stronger than profile preferences.
- Declared executable rivals (`fixed_grid_center`, `keep_endpoints`, `paint_whole_segment`) and an off-center witness linked to the canonical-fitting fixed-center rival.
- Added `lesson_identifiable` so a lesson is rejected when its demonstrations leave a declared rival alive while the query distinguishes that rival.
- Cached complete placement sets without LRU eviction. A 360-draw focused test dropped from 32.5 seconds during the first green attempt to under one second after eliminating cache thrashing across 2,256 legal geometries.

### Tests and probes

Task-local tests are under `tests/`; the reusable source-bound census is `workspace/lesson_probe.py`.

Final focused command:

```sh
cd repo
PYTHONPATH=shared/runtime python3 -m pytest -q generators/b35816e8388b/tests
```

Result: 21 passed in 2.39 seconds (`checks/focused-tests-final.log`). A retained red-first probe test is in `checks/tdd-red-lesson-probe.log`; intermediate green attempts are retained under `checks/tdd-green-*`.

The final lesson census used 120 lessons per difficulty band, with three demonstrations and one query per lesson, one shared deterministic seed per lesson, and sample indices `lesson_index * 4 + offset`. It imports the live rival declarations rather than copying names. Results in `checks/lesson-probe-final.json`:

- easy: 120/120 identifiable, 352/480 unique inputs, 120/120 unique lesson tuples, fixed-center rival disagreed on 434/480 examples;
- medium: 120/120 identifiable, 374/480 unique inputs, 120/120 unique lesson tuples, fixed-center rival disagreed on 436/480 examples;
- hard: 120/120 identifiable, 388/480 unique inputs, 120/120 unique lesson tuples, fixed-center rival disagreed on 454/480 examples;
- every cyclic schedule start occurred 40 times per band; each profile occurred 160 times per band;
- every declared competitor survived zero complete demonstration sets.

### Final verification

The final generator SHA-256 is `b81daf3ec87cf80d6748ed2220885a57fc0baef944eafb5fab0247994b096a2a`.

The complete after battery is green in all 12 stages (`checks/after/checks/b35816e8388b_after_battery_summary.json`). Notable measured results:

- rule smoke: 120/120 applications fired, 91 distinct outputs, Python mirror 120/120;
- strict profile: 24/60 exact/envelope hits and support in every difficulty band;
- semantic gate: strict 219/600 (36.5%), canonical 3/3 accepted, off-center witness 557/600, fixed-center claim checked 60/60, 12/12 sampled lessons identifiable;
- diversity: 300 pairs, 77% unique inputs and 68% unique outputs;
- override contract: 40,050/40,050 accepted draws over 445 cases and three bands, zero findings, unknown keys rejected;
- authority sync: selected authority synchronized and execution parity passed. A pre-existing archival `raw_code` text remains divergent and was not selected or edited.

### Remaining limitations

This establishes behavior for the declared finite domain and tested rival set, not universal human/model induction. Individual examples repeat in the deterministic census, although all 120 lesson tuples per band were unique. The Racket linter still reports non-blocking style findings in the unchanged canonical source. Training admission remains `unverified`; passing local review checks does not approve the task.
## Current reviewer considerations

Source SHA-256: `b81daf3ec87cf80d6748ed2220885a57fc0baef944eafb5fab0247994b096a2a`.

# Distribution and implementation decisions — b35816e8388b

The selected design keeps the canonical transformation fixed and changes only the sampler, validation contract, task-local tests, and reusable probe. Evidence IDs match `REVIEW.md`.

## D1 — Keep colors and the transformation fixed

**Choice.** Inputs use only background 0 and two color-4 endpoints; outputs use only background 0 and one color-8 midpoint.

**Rationale.** These colors are semantic constants in the selected authority, not curriculum variables. Advertising palette controls would imply rule-preserving color substitution that the Racket rule does not perform.

**Rejected alternative.** Retain `palette_kind`, `palette_size`, `n_distinct_colors`, or helpful texture names. Baseline defect lint showed the textures were byte-identical and the palette-like axes were singleton or inert (B358-F2). This would manufacture combinatorial reach without observable behavior.

**Limitation.** The repaired distribution does not train color abstraction; it trains this exact color-bound rule.

## D2 — Use exact dimensions 5 through 16

**Choice.** `grid_h` and `grid_w` are exact integer controls in `5..16` for every difficulty.

**Rationale.** Five cells are enough for nontrivial span-2 placements with off-center alternatives. Sixteen supports the largest declared span 12 with placement freedom while staying comfortably inside ARC size limits. Difficulty changes preferences, not legality.

**Rejected alternatives.** Lock canonical shapes only (too narrow and preserves center bias); advertise larger hard dimensions than the declared valid range (contract violation); silently clamp overrides (destroys exact-control semantics).

**Probe.** `observe_overrides` recovers dimensions from every output, and the override checker accepted all 40,050 draws.

## D3 — Split direction into four observable orientations

**Choice.** `horizontal`, `vertical`, `diag_down`, and `diag_up`.

**Rationale.** The two diagonal slopes produce visibly distinct endpoint relations and should be independently scheduled. The labels are directly recoverable from the returned pixels.

**Rejected alternative.** Baseline `h|v|d` under a non-probeable `choice` declaration. It collapsed both diagonals and prevented the override matrix from running (B358-F2).

## D4 — Declare even coordinate spans 2, 4, 6, 8, 10, 12

**Choice.** `span_steps` is Chebyshev endpoint distance, not number of interior cells.

**Rationale.** Every value has a unique lattice midpoint. Span 6 anchors the canonical examples; shorter and longer values prevent a fixed-length shortcut. The maximum fits at least one legal 13×13-or-larger geometry.

**Rejected alternatives.** Only spans 2 and 4 (misses canonical 6); odd spans (no single integer midpoint); “segment length” terminology (ambiguous about endpoints).

**Probe.** Final tests cover all six values and all four orientations; the deeper probe reports exact per-band support.

## D5 — Three-profile deterministic lesson schedule

**Choice.** Cycle `canonical_anchor`, `off_center`, `broad` by `sample_index % 3`; `EXAMPLES_NEEDED = 3`.

**Rationale.** Any three consecutive demonstrations contain canonical support, a direct fixed-center counterexample, and wider geometry. This makes the curriculum property structural rather than probabilistic (B358-F1).

**Rejected alternatives.** Pure random sampling can produce an all-centered lesson; always off-center weakens canonical-profile support; always canonical preserves the shortcut; post-hoc rejection sampling obscures reproducibility.

**Probe.** The 120-lessons-per-band census covers each cyclic start 40 times and each profile 160 times per band. Every complete lesson is identifiable against the declared rivals.

## D6 — Canonical anchor is narrow but not exclusive

**Choice.** Prefer canonical shapes `(7,9)` and `(9,9)` with span 6 for one profile.

**Rationale.** It guarantees exact linked support for the observed source profiles and passes the profile-floor gate without letting those shapes dominate the full distribution.

**Rejected alternative.** Copy only the exact canonical endpoint coordinates. That would add no new teaching information and reinforce the center shortcut.

## D7 — Off-center witness is explicit

**Choice.** The `off_center` profile filters placements so the true midpoint differs from the deterministic grid-center rival.

**Rationale.** All canonical outputs happen to be centered. A linked witness is therefore necessary to teach endpoint dependence rather than canvas-center dependence.

**Rejected alternative.** Merely increase random placement entropy. High witness frequency does not guarantee that every complete lesson contains a witness.

**Probe.** Witness frequency was 557/600 in the semantic gate and 434/480, 436/480, and 454/480 examples in the deeper easy/medium/hard census.

## D8 — Explicit overrides outrank curriculum preferences

**Choice.** First filter the complete lawful geometry space by exact overrides; profiles and difficulty only prefer among remaining candidates.

**Rationale.** An override is a contract, while a profile is a default curriculum preference. Impossible joint requests raise `IncompatibleGeometry` with named axes rather than being clamped or ignored.

**Rejected alternative.** Draw independent axes and retry until they fit. That can bias values, hide impossible requests, and make exact controls flaky.

## D9 — Fail-closed validation and independent mirror

**Choice.** `_analyze` checks rectangularity, dimensions, values, endpoint count, legal alignment, and span. `self_check`, `observe_overrides`, `strict_canonical_like`, and `rule_mirror` all consume this analysis.

**Rationale.** One structural definition avoids drift among validators while still keeping the Python output construction independent of the Racket implementation text.

**Rejected alternative.** Permissive validation that accepts malformed negative fixtures. Baseline defect lint showed malformed cases inside the ordinary texture domain.

## D10 — Executable rivals, not prose-only warnings

**Choice.** Declare `fixed_grid_center`, `keep_endpoints`, and `paint_whole_segment`; link `off_grid_center` to the canonical-fitting rival; verify lesson identifiability.

**Rationale.** These are plausible local rules that differ in causal use of endpoints, output sparsity, or segment extent. Executable declarations let the gate and source-bound probe test them directly.

**Rejected alternative.** A generic statement such as “avoid shortcuts.” It is not reproducible and cannot fail a build.

**Limitation.** The rival set is intentionally small and task-specific. Other unknown shortcuts can still exist.

## D11 — Cache complete placement sets

**Choice.** Cache placements by exact geometry without eviction; there are only 2,256 legal geometry keys and each value is immutable.

**Rationale.** The initial bounded LRU repeatedly evicted keys during full-domain tests, causing 32.5-second thrashing. Complete caching made the same behavioral coverage inexpensive (B358-F4).

**Rejected alternative.** Reduce test coverage to mask the slowdown. That would weaken evidence rather than fix the root cause.

## D12 — Do not edit the Racket authority

**Choice.** Pin and verify rule hash `259314225434`; leave canonical and archival sources untouched.

**Rationale.** Rule smoke, canonical parity, and authority sync showed the transformation was correct. The defect was in training distribution and contracts.

**Known authority condition.** One archival raw-code text is divergent, but the selected active authorities are synchronized and execution parity passes. This pre-existing condition remains documented rather than silently rewritten.

## Baseline rationale uncertainty

No original design note explained the old pseudo-axes or texture names. My hypothesis is that they came from a generic generator scaffold, but that is not established evidence. The repair therefore relied on observable rule semantics and battery failures rather than attributing intent.

## D13 — Native midpoint-key relay (review-aba1370dbba2cbfe)

The exact canonical midpoint program remains the default. The alternate setting derives the midpoint of the first two row-major color-4 endpoints, reads the aligned key color, and uses that value to select a remote payload. The grid-center-key counterfactual changes the retained 30x30 output, so the second action genuinely consumes the first action's intermediate. The family supports 2–6 demonstrations and four prefix-stable queries; source-bound qualification and public-projection evidence live under `checks/b35816e8388b/`. Owner acceptance remains pending.
