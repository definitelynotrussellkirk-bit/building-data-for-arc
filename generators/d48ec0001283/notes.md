# Working notes: d48ec0001283

## Current rule and authority

For each row independently, fill the inclusive horizontal interval only when the row contains exactly two equal nonzero cells with at least one zero between them. Every other row is unchanged. The selected Racket authority was not changed; `RULE_HASH = ff9a3ff6c04a`. Final generator SHA-256: `955ee9a2026b451a9b2d64952175ad0d46587021104b6b39bddf2f23f0ee7145`.

## Review review-437a5710898452e9

Prior return `review-ce35ccec4404bbb0:v0001` was used only as a lead. Its audit identified a canonical-fitting shortcut against the pinned baseline SHA `a1a8be7aa23fb14ce0b82e9a7acfbada1e90809cbf498a7cb35713f1d42720be`: fill between the outermost markers of any row whose nonzero markers all share one color. Independent baseline replay confirmed that the rival fit all three canonical pairs and 900/900 ordinary generated inputs; the decisive three-same-color-marker input was outside the old validator domain.

Version 3.1.0 now:

- adds `same_color_triplet` and `all_controls` negative-control modes;
- declares `fill_same_color_extrema` as a canonical shortcut / lesson competitor / semantic rival;
- retains an authority-labelled minimal counterexample at `counterexamples/same_color_triplet_shortcut.json`;
- uses a declared four-slot schedule: exact public anchor, all-controls, all-controls, exact public anchor;
- keeps control scenes at two active spans plus three negative rows to avoid object-count drift;
- guarantees every all-controls scene has at least one active span outside public rows 1 and 3, refuting `canonical_rows_only` without depending on random placement;
- strictly rejects non-integer, boolean, string, floating, or negative `sample_index` values;
- constructs compatible unspecified override axes and declares the impossible exact triple `{grid_h: 5, span_count: 3, distractor_mode: all_controls}`.

## Evidence

- Final strict after battery: 12/12 green at `checks/after-pass/`.
- Portable selected-task tests: 11/11 passed at `checks/task-tests-final/`.
- Final production census: 300 lessons (100 per band), 0/300 production ambiguities and 0/1,200 required query-rotation ambiguities; 802 unique inputs (`checks/lesson-census-final.json`).
- Declared-period census: 12/12 band/start lessons and 48/48 required rotations identifiable at seed 0 (`checks/schedule-census-required.json`).
- Final direct probe: seed 480031, indices 0–299 per band; 900/900 lawful, 450/900 triplet witnesses, 0/891 failing sliding three-demo windows (`checks/after-shortcut/reproduction.json`).
- Semantic gate: 315/600 strict canonical-like draws (52.5%, floor 45%), every declared witness fired in every band, and all tested rival claims held.
- Profile floor exact hits: easy 12/20, medium 10/20, hard 8/20.
- Override gate: 45,720/45,720 accepted draws, zero findings.

## Reversed decisions and intermediate failures

The first triplet repair used three active spans in control scenes; defect lint found object-count drift, so the final design uses two. The first repaired source also allowed all active control spans to land on rows 1 and 3. A 100-per-band census then found 7/300 production ambiguities and 23/1,200 rotation ambiguities for `canonical_rows_only`; the final row-swap constraint removed them. Both failed/interrupted iterations are retained under `checks/` rather than overwritten.

## Known limits

The documented generator domain is 5–12 rows by 6–14 columns, two or three active spans, and zero to three recognized negative-control rows. The four-slot schedule is intentionally visible and declared. Finite declared-rival checks, one fixed-seed cyclic enumeration, and sampled production censuses do not prove unique induction against every imaginable rule or every seed. Canonical and selected authority text are synchronized; a retained archival raw implementation is textually different but passed execution parity.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-ce35ccec4404bbb0:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `a1a8be7aa23fb14ce0b82e9a7acfbada1e90809cbf498a7cb35713f1d42720be`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Repair admits/schedules same-color triplet negative control and declares/tests exact all-same-row rival; reported11tests,900draw probe and300lesson/1200rotation census address previous restricted teaching support. Explicit reviewer-reported disposition only after next-snapshot exact-source acceptance; old witness was outside old validator domain. Exact repair accepted with reviewer-reported evidence; no maintainer rerun or closure of other findings.

### Assessment or prior finding

## d48ec0001283

**Reproduced coverage gap: an all-same-row shortcut is never challenged.** At
generator SHA-256
`a1a8be7aa23fb14ce0b82e9a7acfbada1e90809cbf498a7cb35713f1d42720be`, the
candidate “if a row has at least two nonzero markers and all share one color,
fill between the leftmost and rightmost” matches all **3/3 labeled canonical
pairs** and **900/900 ordinary draws** (300 each for easy, medium, hard; seed
`480031`, sample indices 0..299). Every sampled ordinary input passed the target
validator. Evidence and executable probe:
`checks/audit/d48ec0001283/probe_same_color_extra_marker.py` and `probe.json`.

A 5x8 row containing three separated color-2 markers distinguishes the rules.
The executed Racket authority (rule hash `ff9a3ff6c04a`) leaves that row unchanged
because it has three nonzero cells; the shortcut fills two intervening zeros.
The source-bound result is `checks/audit/d48ec0001283/racket.json`, compared in
`authority_comparison.json`; the rival output is `rival_output.json`.

The witness does **not** pass the current validator: it reports “unrecognized
negative-control row” and therefore is outside the documented generator domain.
That exclusion is the finding's limitation and part of the coverage problem,
not a claim of a mislabeled accepted example. A repair could add a third
same-color-marker control, broaden the validator to recognize it, and declare
this rival. The audited generator was not edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-ce35ccec4404bbb0-v0001/audit_assets.json), manifest SHA-256 `a2cd69aea00f39664dc8a4f3c67d4e1999d948f2108c93ad5a0914643f3799ed`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `955ee9a2026b451a9b2d64952175ad0d46587021104b6b39bddf2f23f0ee7145`.

# Decisions: d48ec0001283

Final generator SHA-256: `955ee9a2026b451a9b2d64952175ad0d46587021104b6b39bddf2f23f0ee7145`
Final version: `3.1.0`
Selected rule hash: `ff9a3ff6c04a` (unchanged)

## D1 — Treat the prior audit as a lead, not a result

**Prior choice:** version 3.0.0 had mixed-endpoint and different-color-blocker controls but no monochrome extra-marker case. Original rationale for that omission is unknown.

**New choice:** independently replay the pinned source, then retain the earlier audit only as provenance. Baseline measurements showed the proposed rival matched all 3 canonical pairs and 900/900 ordinary draws, while its distinguishing input failed `self_check`.

**Alternative rejected:** accepting the imported audit without replay would conflate a historical report with current-source evidence.

## D2 — Add a lawful monochrome-triplet control

**Choice:** add `same_color_triplet`, with three separated markers of one color, and combine it with the existing two controls in `all_controls` scenes. Declare `fill_same_color_extrema` in all semantic rival surfaces and bind it to a witness.

**Why:** this is the smallest input feature that distinguishes “exactly two markers” from “two or more markers of one color.” The selected Racket authority leaves that row unchanged, while the rival fills two zero cells.

**Alternatives rejected:**

- Merely naming the rival without generating counterexamples would not teach the distinction.
- Reusing the different-color blocker does not refute a rival conditioned on all markers sharing one color.
- Changing the Racket rule would be incorrect; the authority already expresses the intended exact-two predicate.

**Evidence:** `counterexamples/same_color_triplet_shortcut.json`, `checks/same-color-triplet-counterexample/racket-final.json`, and focused tests.

## D3 — Keep the four-slot anchor/control curriculum

**Prior choice:** `[anchor, both_controls, both_controls, anchor]` with three active spans in control scenes.

**New choice:** `[anchor, all_controls, all_controls, anchor]`, declaring `LESSON_SCHEDULE_PERIOD = 4`. Anchors preserve exact public joint profiles; controls use two active spans plus all three negative rows.

**Why:** every consecutive three-demo window contains at least one complete control scene, while 50% of ordinary draws remain canonical-profile anchors. Reducing active spans from three to two kept connected-object counts within canonical scale after defect lint flagged the first repair.

**Alternative rejected:** random independent control frequency could leave complete lessons without the exact-two witness; making every draw a control would abandon canonical support.

## D4 — Make each control scene refute the public-row-only rival

**Intermediate failure:** the first repaired generator passed the fixed-seed schedule enumeration, but the 100-per-band production census found 7/300 lessons (and 23/1,200 rotations) where `canonical_rows_only` survived. In those cases, both active spans in a control scene happened to occupy rows 1 and 3.

**New choice:** if an `all_controls` draw samples all active rows from `{1, 3}`, swap one already-sampled noncanonical control row into the active set.

**Why:** the change addresses the causal feature directly, consumes no additional randomness, adds no objects, and makes every control scene itself a counterexample.

**Alternative rejected:** removing `canonical_rows_only` from the rival set would hide a demonstrated ambiguity rather than fix the lesson.

## D5 — Make dependent overrides constructive

**Intermediate failure:** a partial override such as `grid_h=5` could retain incompatible random defaults, and the early all-controls design silently created impossible combinations.

**New choice:** derive legal `(span_count, distractor_mode)` pairs after height is known, sample only compatible unspecified values, and declare the one impossible exact triple `{grid_h: 5, span_count: 3, distractor_mode: all_controls}`.

**Why:** every advertised exact axis remains observable across bands, and partial controls adapt only unspecified axes.

**Alternative rejected:** broadly rejecting all small heights with controls would unnecessarily shrink valid support.

## D6 — Reject invalid sample indices at the API boundary

**Choice:** require `type(sample_index) is int` and `sample_index >= 0`.

**Why:** booleans, floats, strings, and negative indices previously flowed into schedule arithmetic and violated the strict scalar contract. Five parameterized regressions cover this boundary.

## D7 — Keep the selected Racket authority unchanged

The selected rule already solves all canonical pairs and agrees with the Python mirror on 120/120 final smoke cases. Authority sync reports canonical and selected text exactly synchronized; a pre-existing archival raw implementation is textually different but also solves all canonical pairs. No rule edit was justified.

## D8 — State finite coverage honestly

The final semantic gate checked 600 generated inputs, a 52.5% strict canonical-like rate against a 45% floor, declared witnesses/rivals, 12 smoke lessons, and required rotations. The larger production census checked 300 lessons and 1,200 rotations; the cyclic census exhausted four starts at one fixed seed across three bands. These measurements establish the tested contract, not universal uniqueness against undeclared rules or all seeds.
