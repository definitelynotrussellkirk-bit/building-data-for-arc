# Working notes: 395201c95f9d

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `fc4da9dc0021d34cede8847d5c99206574639aa63431d3b03b7a52466197d306`.

# Decisions — 395201c95f9d

Final generator SHA-256: `fc4da9dc0021d34cede8847d5c99206574639aa63431d3b03b7a52466197d306`.

## D1 — Keep the selected Racket authority unchanged

**Decision.** Preserve the canonical program and pin `RULE_HASH = "a99b04260a01"` in the generator.

**Rationale.** The defect was in sampling and validation, not output semantics. The selected program solves all canonical pairs and final rule smoke reports 120/120 mirror parity.

**Alternatives rejected.** Rewriting the Racket rule would expand review scope without evidence of an authority defect. Replacing it with the archival `raw_code` was also rejected: authority sync shows that source is textually divergent even though it is execution-equivalent on canonical pairs.

**Probe / failure mode.** `checks/after-v31-r2/checks/395201c95f9d_after_authority_sync.json` and the 120-apply smoke guard against source drift, mutation, statefulness, and Python-mirror disagreement.

## D2 — Use connected 3×3 shape families with 4–6 cells

**Decision.** Enumerate connected supports in a 3×3 box, quotient them by D4, choose the matched family from classes with all eight distinct images, and choose a D4-distinct distractor with the same cell count.

**Rationale.** Full-orbit shapes make the requested transform uniquely observable, while equal cell counts defeat the trivial “choose by size” shortcut. Connected objects stay visually coherent and fit all supported panel sizes.

**Alternatives rejected.** A small handwritten shape bank risked accidental D4 duplicates and poor coverage. Arbitrary subsets could be disconnected or symmetric, making transform labels ambiguous. Different prototype sizes would teach a count shortcut.

**Probe / failure mode.** Canonical inputs include a symmetric/ambiguous transform case, so the validator accepts lawful canonical data; generated strict instances require unique transform observability. Tests cover canonical acceptance, equal counts, D4 distinction, deterministic replay, and all 144 exact override combinations.

**Limit.** This is a bounded curriculum subset: it does not sample disconnected shapes, supports larger than 3×3, or cell counts outside 4–6.

## D3 — Transform normalized support, then independently place the query

**Decision.** Normalize the selected prototype, apply a D4 transform, independently translate the query, and exclude reuse of the matched prototype's exact raw local coordinates.

**Rationale.** This directly removes the imported exact-coordinate shortcut while preserving the canonical rule: match shape up to D4 and keep the query's displayed pose.

**Alternatives rejected.** Merely translating without rotating/reflection would still teach translation-only matching. Transforming around absolute grid coordinates would entangle pose with panel size and create clipping artifacts. Allowing occasional exact-pose reuse would weaken every small lesson unless scheduled carefully.

**Probe / failure mode.** `workspace/lesson_probe.py` reports zero exact-pose reuse in 384 final-source draws; the semantic witness `old_exact_coordinate_shortcut_refuted` fires in all bands and its rival claim is verified.

## D4 — Cross every transform with both labels in a 16-step schedule

**Decision.** Use a 16-profile deterministic cycle. Each D4 transform occurs once with panel 0 and once with panel 1. The repeating semantic roles are panel-0 reflection, panel-1 rotation, panel-0 rotation, panel-1 reflection.

**Rationale.** The first 8-profile repair paired panel 0 only with reflections and panel 1 only with rotations. That left a wrong canonical-fitting rule: inspect panel 1 under rotations and otherwise choose panel 0. A full 2×8 crossing removes static panel/transform correlation.

**Alternatives rejected.** Independent random draws can omit rare combinations from short lessons. The original 8-step alternation gave excellent marginal coverage but encoded a cross-feature shortcut. An 8-profile permutation cannot pair every transform with both labels.

**Probe / failure mode.** The red regression at `checks/395201c95f9d_schedule_red.log` proves the old schedule covered only 8/16 profiles. The final semantic gate reports all 16 profiles, while `checks/395201c95f9d_lesson_probe_v31.json` exhausts every cyclic start in all bands.

## D5 — Require four demonstrations per lesson

**Decision.** Set `EXAMPLES_NEEDED = 4` and make every cyclic four-example window contain rotation and reflection evidence for both labels.

**Rationale.** With asymmetric full-orbit shapes, three examples cannot show both transform classes for both labels. Four demonstrations are the minimum direct witness set for refuting all four one-panel/one-transform-class defaults.

**Alternatives rejected.** Retaining three examples would require symmetric shapes whose transform class is ambiguous, conflicting with exact `transform` overrides. Adding more than four increases cost without adding a new semantic branch.

**Probe / failure mode.** Final task tests enumerate all 16 starts × 3 bands, and the lesson probe checks 48 cyclic lessons. The 300-lesson census reports every declared rival refuted 100/100 in each band.

## D6 — Keep canonical profile support while varying bounded scale

**Decision.** Produce the canonical 5×17/seven-color input profile on two thirds of natural draws in every band, with the remaining third using band-specific panel-size variants.

**Rationale.** This keeps a strong anchor to public examples while preventing a single-size template from dominating the corpus.

**Alternatives rejected.** Always canonical size would reduce structural diversity; fully random dimensions could miss the required canonical floor in small fixed samples.

**Probe / failure mode.** Profile floor measured 37/60 exact hits and nonzero support in each band. Task tests require both the canonical profile and at least one alternate profile per band.

## D7 — Use five distinct role colors plus fixed background/separators

**Decision.** Draw distinct colors for two labels, two prototypes, and the query; reserve 0 for background and 9 for separators.

**Rationale.** Distinct role colors prevent identity/copy-color shortcuts and make panel parsing stable. The output color must come from the selected label, not from a prototype or query color.

**Alternatives rejected.** Reusing colors can collapse semantic roles or produce accidental output equality. Random separator colors would depart from the canonical grammar.

**Probe / failure mode.** `copy_query_color` is an executable rival, `query_repaint_required` fires 600/600, and all claims are oracle-checked.

## D8 — Make overrides exact and observable

**Decision.** Advertise only `panel_h`, `panel_w`, `cell_count`, `match_panel`, and `transform`; honor each exactly, expose `observe_overrides`, reject unknown keys, and reject unsupported difficulty values.

**Rationale.** A declared axis is useful only when it changes visible bytes and can be recovered from them. Exact controls also make distribution tests reproducible.

**Alternatives rejected.** Difficulty-local narrowing of advertised domains creates metadata/implementation contradictions. Silent unknown-key acceptance hides misspellings.

**Probe / failure mode.** The final override gate accepted 18,720/18,720 draws over 208 cases and rejected its unknown-key probe with zero findings/warnings.

## D9 — Declare executable rivals and canonical shortcuts

**Decision.** Include constant-panel, count, exact-coordinate, rotations-only, query-color, prototype-pose, and four one-panel/one-transform-class rivals. Mark the two panel-1 restricted-transform rules as canonical shortcuts because each fits all 3 canonical pairs.

**Rationale.** Marginal diversity is insufficient; named executable alternatives make “identifiable” a testable claim. The canonical shortcuts are especially valuable because public examples alone cannot reject them.

**Alternatives rejected.** Descriptive prose without executable rivals cannot be automatically scored. A tiny rival set would miss cross-feature correlations, as the first repair demonstrated.

**Probe / failure mode.** The final semantic report verifies every witness/rival disagreement claim and shows both canonical-fitting shortcuts satisfied by generated counterexamples. The lesson census scores the generator's declarations directly rather than a copied name list.

## D10 — Preserve failures and build a reusable cyclic-window probe

**Decision.** Retain both red test rounds, interrupted aggregate runs, complete final reports, and `workspace/lesson_probe.py`.

**Rationale.** The second red round is important evidence that the self-review found and corrected a new shortcut rather than merely passing inherited gates. The probe gives future editors a cheap schedule regression independent of the large battery.

**Alternatives rejected.** Keeping only final green logs would erase causal evidence. Relying solely on the 12-lesson semantic smoke would not exhaust all cyclic schedule starts.

**Limit.** The rival set is finite and should grow when a model or reviewer finds a new plausible shortcut.
