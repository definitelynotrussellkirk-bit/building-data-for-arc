# Working notes: 99e7ba062bec

## Review diagnosis

The baseline Racket authority was healthy; generation was not. The before battery failed lint, strict defect lint, canonical distribution support, and override contract. The principal data defect was role collapse: A, B, and C all used one foreground color, while canonical inputs use A/B same and C distinct. The checker also accepted severe structural impostors, and generic metadata exposed inert/fake axes.

## Repair record

- Kept the Racket authority unchanged and pinned rule hash `e3f7daceeedf`.
- Rebuilt generation around the canonical 5×17, three-panel profile.
- Added A/B shared color and distinct C color.
- Included all seven authoritative transforms with first-match code order.
- Replaced retry/fallback shape construction with bounded exhaustive mask candidates having seven distinct transform images.
- Scheduled branch coverage over seven samples; set serialized lesson length to five after retaining the initial seven-example semantic warning.
- Replaced generic axes with exact `command`, `a_active_count`, and `c_active_count` controls.
- Added strict/canonical validation, Python mirror, witnesses, rivals, lesson identifiability, mutation fixtures, and focused tests.

## Evidence landmarks

- Baseline battery: `checks/before/checks/99e7ba062bec_before_battery_summary.json`
- First semantic warning retained: `checks/iterations/semantic-examples-needed-warning.log`
- Passing semantic rerun: `checks/final-verification/`
- Passing override stress test: `checks/final-verification/`
- Complete after battery: `checks/final-verification/`
- Reusable commands and interpretations: `workspace/REVIEW_PROBES.md`

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `f6228ce86c6cd75049ee0ada2dddc3e9a0223d974a3d4a3e59bc40b3d477bab7`.

# Distribution and implementation decisions

## 1. Preserve the Racket authority

**Original rationale:** The packet's before battery already showed rule smoke, grammar, Racket lint, and authority synchronization as green. The defect was in data generation, not the rule.

**Decision:** Keep the authoritative first-match transform program unchanged and pin `RULE_HASH = "e3f7daceeedf"` in the generator.

**Alternatives considered:** Rewrite the rule to demand a unique transform; add anti-transpose as an eighth transform. Both were rejected because they would change task semantics rather than repair the generator.

**Probe:** Canonical Python-mirror parity in `tests/test_generator_99e7ba062bec.py`; Racket parity in `checks/final-verification/`.

**Failure mode / limitation:** First-match behavior matters when A is symmetric. Ordinary generated samples are stronger and unique, so canonical examples remain the direct regression for tie ordering.

## 2. Exact 5×17 canvas instead of variable dimensions

**Original rationale:** Unknown. The baseline varied dimensions even though the canonical profile was fixed and its dimension overrides were observably false.

**Decision:** Generate exactly 5×17. Keep panel positions variable through row offsets and separator/margin allocation rather than changing the outer canvas.

**Alternatives considered:** Continue 5–10 by 9–20 variable grids; infer a broad envelope from the abstract rule. Rejected because both create unsupported morphology and weaken canonical-profile density.

**Probe:** `test_generated_distribution_reaches_the_canonical_profile_and_role_palette`; profile-floor evidence in `checks/final-verification/`.

**Failure mode / limitation:** This is conservative and may omit valid unseen larger layouts. It is a deliberate data-quality tradeoff, not a claim that the rule only works at 5×17.

## 3. Role-linked three-color palette

**Original rationale:** The baseline used a single foreground color, likely for simplicity, but that made color transfer unlearnable and contradicted every canonical input.

**Decision:** A and B share one color; C uses a different color; the transformed output keeps C's color. Sample from all nonzero ARC colors without assigning semantics to color identity.

**Alternatives considered:** One shared color for all panels; three unrelated colors; fixed colors. Rejected because the first makes “preserve C color” observationally indistinguishable from recoloring, the second breaks the A/B analogy cue, and the third creates color shortcuts.

**Probe:** The role assertions in the focused test, the `recolor_output_to_ab` semantic rival, and palette/profile evidence in `checks/final-verification/` and `checks/final-verification/`.

**Failure mode / limitation:** Global swapping of the two role colors remains lawful, so a color-swap mutation is intentionally accepted.

## 4. Seven transforms in authoritative order

**Original rationale:** The baseline omitted identity from ordinary transform selection, despite identity being part of the rule.

**Decision:** Include all seven authoritative transforms and use exact code order for first-match inference.

**Alternatives considered:** Sample only the six visibly changing transforms; add anti-transpose. Rejected because the former omits a valid branch and the latter is not in the authority.

**Probe:** `schedule_profile`, seven semantic witnesses, the seven-window branch test, and semantic-gate witness counts.

**Failure mode / limitation:** An identity example can be easy in isolation; it is retained because omitting it creates a “must always change” shortcut.

## 5. Deterministic branch schedule, five serialized demos

**Original rationale:** Unknown. The baseline random branch draw did not guarantee local coverage.

**Decision:** Use `(sample_index + seed) mod 7` to cover every branch in a seven-sample window. Set `EXAMPLES_NEEDED=5` because the review contract serializes only 2–5 demos.

**Alternatives considered:** Seven demos per lesson; pure random branch selection; force all seven branches into five examples. Seven demos failed the serialization-range check, random sampling permits branch droughts, and seven branches cannot fit into five single-command examples.

**Probe:** The retained warning in `checks/iterations/semantic-examples-needed-warning.log`, passing rerun in `checks/final-verification/`, and `test_five_demo_lessons_are_serializable_and_seven_samples_cover_all_branches`.

**Failure mode / limitation:** No individual lesson contains every branch. Lesson-level rival checks ensure the five demos are nevertheless identifying against the declared shortcut set.

## 6. Enumerated transform-discriminative masks

**Original rationale:** The baseline attempted random connected asymmetric shapes, but its fallback did not guarantee the property named by the constructor.

**Decision:** Enumerate bounded 2×3 through 4×3 masks with 4–7 active cells, full row/column support, and seven distinct transform images. Choose C outside A's transform orbit.

**Alternatives considered:** Keep retry-plus-fallback random growth; permit symmetric masks routinely; use only one fixed asymmetric template. Rejected respectively for silent semantic failure, transform ambiguity, and low diversity.

**Probe:** `_shape_candidates`, `_transform_image_count`, focused transform-discrimination assertions, and 600/600 strict semantic acceptance.

**Failure mode / limitation:** Enumeration favors small masks and excludes lawful symmetric ordinary examples. Canonical symmetric/tied examples are still accepted and used for authority parity.

## 7. Vary connectedness while holding canonical marginals

**Original rationale:** The baseline produced exactly three components, below canonical support.

**Decision:** Sample transform-discriminative masks across one to three components and schedule active-cell counts by difficulty, yielding total component counts around canonical support without changing the outer profile.

**Alternatives considered:** Force every panel connected; draw arbitrary sparse pixels. Rejected because the first missed canonical object counts and the second risks accidental panel fragmentation/shortcut artifacts.

**Probe:** Component-count assertions in the focused test; defect lint, distribution gate, and profile-floor results.

**Failure mode / limitation:** The schedule controls cell count, not exact total component count. Component variation is verified statistically rather than exposed as another override axis.

## 8. Three truthful override axes only

**Original rationale:** The baseline inherited generic metadata for dimensions, palette, texture, density, and other singleton/fake axes.

**Decision:** Expose only `command`, `a_active_count`, and `c_active_count`. Make all exact and observable; reject unknown keys and invalid values.

**Alternatives considered:** Keep compatibility aliases for old axes; expose row offsets, colors, component count, and separator widths. Rejected because aliases would preserve false contracts and the additional axes were not needed to test semantic boundaries.

**Probe:** `observe_overrides`, boundary override regression, and the 8,100-draw override gate.

**Failure mode / limitation:** Some useful latent variation is not user-controllable. That is preferable to declaring an axis whose effect cannot be independently observed.

## 9. Strict generated profile plus canonical acceptance

**Original rationale:** The baseline checker looked only for blank separators and accepted severe impostors.

**Decision:** Separate structural parsing from generated-profile strictness. Accept canonical inputs if they obey the task grammar; require ordinary generated inputs to have exact role palette, three panels, supported sizes, discriminative masks, and an observable command.

**Alternatives considered:** Apply generated uniqueness constraints to canonical inputs; accept any grid the rule can execute. The former would reject real examples; the latter would let low-value or malformed training data through.

**Probe:** Canonical acceptance test, `strict_canonical_like`, mutation fixtures, self-check and defect-lint gates.

**Failure mode / limitation:** The checker encodes a conservative curriculum profile, not the complete mathematical language of every valid transform analogy.

## 10. Semantic rivals and lesson-level identifiability

**Original rationale:** The baseline had no executable contract proving that a lesson taught the intended rule rather than a shortcut.

**Decision:** Declare branch witnesses and competitors: fixed transforms, recolor-to-A/B, copy-A, and copy-B. Require every sampled lesson to falsify each relevant rival in at least one demonstration.

**Alternatives considered:** Trust marginal diversity and Racket execution alone; compare only final outputs. Rejected because both can pass shortcut-teaching distributions.

**Probe:** `SEMANTIC_WITNESSES`, `LESSON_COMPETITORS`, `lesson_identifiable`, and the passing semantic gate.

**Failure mode / limitation:** The rival set is finite. It proves resistance to named plausible shortcuts, not all possible learned heuristics.

## 2026-10-25 native parametric admission candidate

Added a source-bound two-setting family without changing the accepted generator
or canonical rule. `forward` returns the exact selected canonical Racket text;
`inverse` infers the same A-to-B transform but applies its inverse to C (quarter
turns 2 and 4 exchange; self-inverse transforms remain unchanged). Inputs are
matched across settings, prefixes are count-stable, the first two demos expose
commands 2 and 4, and the fourth query is a dense 30×30 three-panel scene.

Reviewer qualification replayed 40 labels in protected Racket across two seeds
and both settings. Public projection produced 16 sequential one-query views;
export conformance and 24 private-field invariance checks passed. A protected
counterfactual witness holds the panels fixed and changes only the effective
transform intermediate, changing the final orientation. A broader author
self-review found seed 84 could fall to 87 active cells in the 30×30 scene;
a regression test now covers it and the sampler constructively requires at least
30 active cells in both A and C, guaranteeing at least 90 across A/B/C. The final
512-seed independent-oracle sweep passed. This is ready reviewer evidence, not
owner acceptance or a claim of universal identifiability/training gain.
