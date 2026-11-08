# Working notes: af6e765bcc41

## Current separate parametric family

`workspace/parametric/` supplies the native adapter, promotion contract, executable
rules and current evidence inventory. `completion=none` preserves the exact
canonical program; `single_gap` simultaneously closes every zero single missing
perimeter cell of each original orange four-connected component, then recomputes
components and fills zero interiors of exact orange frames. Other colors,
including existing cyan, are preserved. A repair can merge a frame with a
satellite and make it ineligible, so recognition must consume the repaired grid.
The separate family accepts exact integer ARC grids with both axes 3..30; the
production sampler and its narrower domain remain unchanged.

Three demonstrations teach the rule: one isolated exact3x5 frame in a5x7canvas,
one isolated corner-gap3x3 frame in a5x5canvas, and a27x27scene with sixteen
contrasting motifs. The large demonstration contains all four side-gap directions
under one spatial transform, exact3x3and larger frames, colored interiors,
non-orange frames, two-gap shapes, a tail, diagonal contact, an occupied gap and
a repair merge. A3x6side-gap motif gives a minimum-thickness, beyond-five witness.
Extra demonstrations and the four-query bank remain independent of requested
counts. Seeds0..2**63-1, demos3..6 and queries1..4 are strictly typed; settings
share input draws, query banks are shuffled before prefixes, and arrays are fresh.

The earlier three crowded, independently oriented demonstrations were rejected:
14/64reviewed episodes admitted shape or omitted-direction shortcuts; a separate
review found context gates requiring multiple components. The new teaching
anchors repair these holes without increasing the demo count or changing any of
256reviewed query pairs or192optional demonstration pairs. Before cases, executable
rivals and regression failures are retained under `checks/af6e765bcc41/`.

Current checks:94portable task tests pass; a frozen39-hypothesis bank plus the
separate component-count gate has no query-changing demo-fit survivor across
64episodes. A separate19-hypothesis review has no remaining finding across
16episodes, with194fresh protected labels. Independent final checks add52fresh
protected executions and explicitly reuse274unchanged-reference checks. Native
qualification passes both settings on seeds0/17at3demos/4queries with40protected
executions. Two wrong-intermediate counterfactuals replay through protected
Racket. All16single-query public views and privacy/order/tamper checks pass.

Evidence: `checks/af6e765bcc41/{independent-final.json,final-review/report.json,
qualification/qualification.json,causal/witness.json,projection-edges.json}` and
`workspace/parametric/evidence/manifest.json`. Finite checks are not universal
uniqueness. Sampling uses separated motif slots and does not cover every lawful
arrangement. Repeated repair to stability is equivalent to one pass for this rule,
not a distinguishable variant. The next owner action is exact-source native
acceptance; this ready proposal grants no production or training admission.

## Current rule and design

Fill the zero interior of every **exact one-cell-thick orange (7) rectangular frame** with cyan (8). Preserve the orange border, broken/incomplete orange shapes, complete frames of other colors, and unrelated cells. Canonical authority hash is pinned as `c8f338ea5e1e`; the task-local Python mirror is for contracts/tests only.

Generator version `3.0.0` defaults to canonical height/width profiles and places four separated motifs: 1–2 valid orange frames, one one-gap orange near-frame, and one exact frame in color 1–6 or 9. The two declared canonical-fitting rivals are:

- `orange_bboxes`: fills every orange component bounding box, ignoring outline completeness;
- `all_color_frames`: fills every exact frame, ignoring color.

Every default sample contains `broken_orange` and `nonorange_frame` witnesses, so each pair refutes both rivals independently. A Racket-checked exact replay is retained at `counterexamples/shortcut_witness.json` and covered by focused tests.

## Public controls

Only exact observable controls remain:

- `grid_h`: integer 8..16
- `grid_w`: integer 10..16
- `n_frames`: integer 1..2

`observe_overrides` recovers all three from pixels. Unknown controls, booleans, floats, strings, out-of-range values, non-integer seeds, and negative/non-integer sample indices fail loudly. The former palette/texture aliases, constant axes, and degenerates were removed because they were inert or did not match the authority domain.

## Domain checks

`self_check` accepts every canonical input, including unrelated colors and 3×3 frames. It requires at least one exact hollow orange frame, rejects pre-existing cyan and malformed orange components, and permits at most the one declared one-gap near-frame. Difficulty changes default sampling, not domain validity.

## Evidence

- Baseline battery: 7 failed stages (`checks/before/`).
- Final battery: 12/12 green (`checks/after-final/`), bound to generator SHA-256 `3f4f976c5c4f688325d81022ce8b6a556404336a09e10b0a7517ed73ef04c60f`.
- Portable task tests: 32 passed (`checks/task-tests-final-v2/`).
- Census: 300/300 lessons, 900 unique inputs, 0 production ambiguities, 0/900 ambiguous rotations (`checks/lesson-census-final.summary.json`; full report compressed per `checks/COMPRESSED-EVIDENCE.json`).
- Selected authority sync changed only `racket_target.target_code` to canonical text; archival `raw_code` remained unchanged (`checks/authority-sync-proposal.json`).

## Reversed decisions and limits

The prior design intentionally generated only complete orange frames and exposed broad texture/palette controls. That was reversed because it taught shortcuts and several controls were inert or unhonored. The current distribution deliberately favors teachability over full lawful-domain coverage: every default grid contains both decoy types and uses separated four-region layouts. Finite rival tests and a 300-lesson census do not prove universal identifiability; new plausible rivals should be added as executable contracts and counterexamples. No cyclic schedule period is declared.
## Current reviewer considerations

Source SHA-256: `3f4f976c5c4f688325d81022ce8b6a556404336a09e10b0a7517ed73ef04c60f`.

# Decisions: af6e765bcc41

## D1 — Treat exact frame shape and orange color as essential

**Original choice:** emit only complete orange frames on a zero background. Original rationale is not recorded beyond the imported summary.

**Failure mode:** both `orange_bboxes` (fill any orange component's bounding box) and `all_color_frames` (fill complete frames of any color) fit every canonical demonstration and every baseline-generated example.

**Alternatives considered:** add only malformed orange objects; add only non-orange frames; depend on multi-example schedules to separate rivals; include both witnesses per grid.

**Decision:** every default grid includes one one-gap orange near-frame and one exact non-orange frame in addition to 1–2 valid orange frames. This makes each labeled pair independently refute both rivals, so query rotation cannot remove the only witness.

**Evidence:** focused rival tests, retained counterexample, semantic battery gate, and the 300-lesson/900-rotation census.

**Limit:** the witness set is finite. Other plausible hypotheses may remain unenumerated.

## D2 — Use four separated motif regions

**Original choice:** random rejection placement of 1–3 large orange frames with a deterministic corner fallback.

**Failure mode:** the baseline could not guarantee room for two contrastive decoys, and its ranges missed several canonical profiles.

**Alternatives considered:** global rejection sampling with more attempts; grow boards; fixed templates; four independently sized corner/quadrant regions.

**Decision:** split each board around a blank central row/column into four disjoint regions, draw 3–5-cell motifs inside them, and shuffle role assignment. This guarantees separation without a brittle fallback while supporting canonical dimensions as small as 8×10.

**Evidence:** deterministic-generation tests, override tests, profile floor, grammar, diversity, and census materialization with no errors.

**Limit:** motif placement has a recognizable four-region structure and does not span all lawful spatial arrangements.

## D3 — Replace inert axis breadth with exact observable controls

**Original choice:** advertise nine keys including palette aliases, constant axes, texture aliases, and degenerates, with ranges much wider than local generation actually honored.

**Failure mode:** controls were inert or incompatible with local difficulty ranges; unknown controls could be ignored; values were not recoverable from output pixels.

**Alternatives considered:** repair every historical axis; retain aliases for compatibility; declare incompatibility matrices; reduce the surface.

**Decision:** expose only `grid_h` (8–16), `grid_w` (10–16), and `n_frames` (1–2). All are exactly recoverable through `observe_overrides`; there are no incompatible combinations. Unknown keys and non-exact/out-of-range values fail loudly.

**Evidence:** override battery stage and parameterized focused tests across all difficulty bands.

**Limit:** callers using removed legacy axes must migrate rather than receiving silent compatibility behavior.

## D4 — Sample canonical profiles by difficulty

**Original choice:** easy 10–11, medium 10–14, hard 13–14, with only colors 0 and 7.

**Failure mode:** exact canonical height/width/color-count profiles were underrepresented or absent, causing profile-floor and distribution failures.

**Alternatives considered:** independent broad dimension draws; exact canonical-profile table; weighted mixture of canonical and extrapolated profiles.

**Decision:** default dimensions come from observed canonical `(height,width)` profiles, with overlapping subsets by band; unrelated frame colors provide canonical-like distinct-color counts. Exact user overrides still cover a broader 8–16 by 10–16 envelope.

**Evidence:** final profile-floor and distribution gates are green; the census produced 900 unique inputs.

**Limit:** the finite profile table may need extension if canonical data changes.

## D5 — Make `self_check` describe the actual lawful domain

**Original choice:** accept only colors 0/7, require frames at least 4×4, and require two frames on hard boards.

**Failure mode:** all canonical examples with unrelated colors or 3×3 frames were rejected. Difficulty-specific frame counts conflated default sampling with domain validity.

**Decision:** validate rectangular ARC grids, reject pre-existing cyan, accept unrelated colors, require at least one exact hollow orange frame of size ≥3×3, allow at most one declared one-gap orange near-frame, and reject every other malformed orange component.

**Evidence:** every canonical input and every generated sample passes focused tests and the final self-check stage.

**Limit:** `self_check` intentionally recognizes the generator's near-frame grammar, not every conceivable irrelevant orange arrangement that the Racket rule would preserve.

## D6 — Declare executable rivals and witnesses

**Original choice:** no `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, witnesses, or lesson-identifiability hook.

**Decision:** register `orange_bboxes` and `all_color_frames` in all rival surfaces; bind them to `broken_orange` and `nonorange_frame` witnesses; set `EXAMPLES_NEEDED=2`; and implement `lesson_identifiable` against labeled demonstrations.

**Evidence:** semantic gate is green and the full rotation census has zero survivors.

**Limit:** declared-rival success is not universal identifiability.

## D7 — Synchronize selected Racket text without changing semantics

**Original choice:** selected `target_code` included comments absent from canonical `program_solution`; executable tokens were otherwise equivalent.

**Alternatives considered:** waive the drift; change canonical text; edit archival `raw_code`; synchronize only selected target text.

**Decision:** use the authority-sync proposal workflow to replace only `/racket_target/target_code` with canonical source. Preserve archival `raw_code` byte-for-byte.

**Evidence:** `checks/authority-sync-proposal.json` records old/new hashes and the sole JSON pointer; final rule smoke, Racket lint, and authority sync pass.

**Limit:** the proposal's static proof is restricted token identity, not a general semantic-equivalence theorem.
