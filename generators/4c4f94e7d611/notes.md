# Working notes: `4c4f94e7d611`

## Intended rule

Select the unique largest 4-connected nonzero component as the template. Count
all singleton components regardless of color. Crop the template and emit that
many horizontal copies with one zero-column gap, alternating original and
left-right mirror beginning with the original. Canonical/Racket `RULE_HASH` is
`d1c2577e1828` and was not changed in this review.

## Current teaching schedule

The exact period is four slots:

1. `canonical_anchor`
2. `decoy_high_count`
3. `visible_mirror`
4. `single_marker_boundary`

`LESSON_SCHEDULE_PERIOD = EXAMPLES_NEEDED = 4`. The schedule teaches five
executable rivals: count every non-template object, count color-1 cells, count
only color-1 singleton components, omit gaps, and repeat without mirroring.

## Review decisions

- Added the previously missing `count_color_1_singletons` rival. It fits all
  four canonical pairs.
- Added `non_color1_singleton_marker` as its witness and bound the witness to
  the rival.
- Reversed the prior boundary-color choice: `single_marker_boundary` formerly
  inherited the general palette and could be blue; it now always uses a
  non-blue marker. Reason: the earlier choice left 6/60 query rotations
  ambiguous when the mixed-color high-count profile was held out.
- Replaced the focused test's private `scripts.*` canonical helper with
  portable `reviewer_support.canonical_pairs` + `find_root`.
- Kept the Racket authority, canonical rows, shape/count ranges, decoy policy,
  overrides, and output construction unchanged.

## Evidence

- Exact shortcut counterexample: `counterexamples/color1_singleton_shortcut.json`
  (seed 17, sample 1, medium).
- Authoritative output: `checks/shortcut-color1-singletons/racket-final.json`.
- Initial exhaustive census: `checks/schedule-census.json` — 6/60 ambiguous
  rotations.
- Final exhaustive census: `checks/schedule-census-after.json` — 12 lessons,
  60 rotations, 0 ambiguous, 18 diagnostic hook warnings, 16 unique inputs.
- Final battery: 12/12 green; focused tests: 8/8 green.

## Known limits and open findings

The 18 rotation warnings are retained because some held-out rotations omit the
sole example of a named profile, even though every declared rival is refuted by
the remaining four demonstrations. The rival set is finite; no claim of
universal rule uniqueness is made. The one-marker profile no longer samples
blue markers, but two other slots still do, so both blue and non-blue singleton
markers remain represented in each ordered lesson.
## Current reviewer considerations

Source SHA-256: `96088190dc76a6d94deea6f6fe73ce20061d24809a98974f6bb0bec3251217b1`.

# Decisions for `4c4f94e7d611`

## D1 — Preserve the transformation and Racket authority

**Prior choice and rationale:** The selected generator already implemented the canonical count/crop/alternate-mirror rule, and the before battery was 12/12 green. The original rationale beyond the source comments is unknown.

**Decision:** Do not change the Racket program, canonical examples, `RULE_HASH`, output construction, or lawful input domain.

**Alternatives considered:** Rewrite the rule or generator wholesale; add a second labeling implementation. Both would add authority risk without addressing the observed teaching shortcut.

**Probe:** Before and after authority/rule-smoke stages plus canonical mirror tests.

**Failure mode / limit:** Passing authority checks proves source binding and sampled agreement, not that every lawful input is covered.

## D2 — Add the strongest missing canonical shortcut

**Observed issue:** Every canonical marker is a singleton of color 1. Therefore “count only color-1 singleton components” fits all four canonical labeled pairs, while being strictly stronger than the already declared “count color-1 cells” shortcut.

**Decision:** Add `count_color_1_singletons` to `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; add `non_color1_singleton_marker` as its executable witness.

**Alternative:** Rely on the broader color-1-cell rival. Rejected because a two-cell color-1 decoy refutes cell-counting but does not refute singleton-only counting.

**Probe:** Canonical-fit assertions plus generated seed 17, sample index 1, medium. The authoritative rule emits five copies; the shortcut emits `[[0]]`.

**Evidence:** `repo/generators/4c4f94e7d611/counterexamples/color1_singleton_shortcut.json` and `checks/shortcut-color1-singletons/racket-final.json`.

## D3 — Reverse the boundary marker-color choice

**Prior choice:** `single_marker_boundary` inherited the general marker palette and could choose color 1. The original rationale is not recorded.

**Observed failure:** With the high-count mixed-color profile held out, 6 of 60 query rotations let both color-1 counting shortcuts survive (`checks/schedule-census.json`).

**Decision:** For `single_marker_boundary`, choose marker colors only from 2–9, excluding the template color. The slot still teaches the one-marker count boundary and now independently teaches that marker color is irrelevant.

**Alternatives considered:**

- Force every slot to use mixed colors. Rejected as unnecessary and less canonical-like.
- Add a fifth demonstration. Rejected because the task already declares a four-example minimum and redundancy can be achieved inside that budget.
- Suppress query rotations. Rejected because downstream assembly may rotate queries and the census found a real declared-rival ambiguity.

**Probe:** Every band, every schedule start, every one-of-five holdout. Final result: 0/60 ambiguous rotations (`checks/schedule-census-after.json`).

**Failure mode / limit:** The boundary slot no longer samples blue markers. Other slots retain blue markers, so this is a local profile restriction rather than a global palette restriction.

## D4 — Declare the exact schedule period

**Decision:** Set `LESSON_SCHEDULE_PERIOD = EXAMPLES_NEEDED` and test that it equals the four-profile cycle for two complete periods.

**Rationale:** The schedule is deterministic by `sample_index % 4`; declaring it lets shared census tooling enumerate every cyclic start rather than estimate coverage from random samples.

**Alternative:** Keep the period implicit. Rejected because the initial smoke gate did not expose the 6/60 rotation ambiguity.

## D5 — Make focused tests portable

**Prior choice:** The task test imported `scripts.canonical_profile_gate`, a private layout-dependent helper. The original rationale is unknown.

**Decision:** Use `reviewer_support.canonical_pairs` with `find_root(__file__)`.

**Alternative:** Hard-code parent depths or canonical paths. Rejected because the final handoff runs tests in a portable reconstructed runtime.

**Probe:** Selected task-test stage in the working packet and a fresh extraction after patch replay; both passed 8/8.

## D6 — Retain diagnostic warnings rather than weaken the lesson hook

**Decision:** Keep the 18/60 rotation hook warnings that report a held-out unique profile, while separately reporting 0/60 declared-rival ambiguities.

**Rationale:** The warnings accurately describe pedagogical coverage. Removing the corresponding checks would make the report look cleaner while conveying less information.

**Limit:** Ordered production lessons have all four profiles and no warnings. Arbitrary query rotations remain supported against the declared rivals, but some rotations no longer exhibit every named witness type.

## D7 — Keep audit work separate

The two random audit targets were inspected and reproduced, but no files under those generators were changed. Their findings are documented in `AUDIT.md` and `checks/audit/` only.
