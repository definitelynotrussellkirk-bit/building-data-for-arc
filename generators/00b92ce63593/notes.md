# Working notes: 00b92ce63593

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `e278f779baeae1c16a96aadd180accd452f9fdc088531f8f691958183cc85691`.

# Decisions

## D1 — Measure the pinned baseline rather than trusting prior prose

The baseline comments already claimed varied colors and off-legend examples, but the assigned bytes had not been validated. I treated those comments as a lead only. The before battery established the actual state: missing rule pin, dead texture controls, thousands of override failures, no semantic contract, and weak canonical support. Evidence: `checks/before/checks/00b92ce63593_before_battery_summary.json`.

## D2 — Keep the canonical Racket authority unchanged

The before rule smoke, grammar, Racket lint, and authority sync were green, and the canonical rule output matched an independent Python mirror. The defect was the input/lesson distribution and public control contract, not the transformation. I therefore kept the canonical row unchanged and pinned `RULE_HASH = "6f9bcb74d69f"`.

Alternative rejected: editing the Racket program to accommodate generator behavior. That would have changed a correct task to fit a defective generator.

## D3 — Replace the texture surface instead of patching aliases

The baseline exposed `plain`, three body-color textures, and three degenerate textures. Helpful texture overrides were dead because the generator read `body_colors` separately, while degenerate textures overlapped the ordinary advertised domain and generated invalid or rule-hiding scenes.

Final choice: `HELPFUL_TEXTURES = ()`, `DEGENERATE_TEXTURES = ()`; body color is one explicit exact axis. Negative malformed cases live in tests, not the production generator.

Alternative rejected: preserve texture aliases with compatibility rules. It adds two names for the same semantic control, enlarges the override matrix, and makes exact observability ambiguous.

## D4 — Advertise only a fully constructive Cartesian domain

The final controls are:

| Axis | Baseline advertised choice | Final choice | Reason / failure avoided |
|---|---|---|---|
| `grid_h` | 4..10, band-clamped | 5..10 in every band | Height 4 cannot support exact `body_cells=4`; full range is now constructive. |
| `grid_w` | 4..10, band-clamped | 5..10 in every band | Width 4 plus four legends leaves no off-legend column; width 5 supports the full product. |
| `n_legend` | 1..5, silently capped | 2..4 exact | At least two headers improve relational evidence; four leaves a free column at minimum width. No silent cap. |
| `body_cells` | implicit density | 1..4 exact per legend column | Exact counts are observable and avoid probabilistic underfill. |
| `body_colors` | enum plus texture alias | `uniform7`, `uniform_other`, `mixed` | Directly tests whether the rule depends on orange 7. |
| `off_legend` | 0..4 but sometimes underfilled | 0..4 exact | Directly teaches erasure and is recovered by `observe_overrides`. |
| `density` | 0.2..0.9 | removed | Density was not an exact semantic quantity and conflicted with minimum witness guarantees. |

Every combination of boundary values is generated and observed in every band by the task-local suite. `INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty because no advertised combination needs rejection.

## D5 — Fail closed on the public API

`_validate_request` rejects unknown difficulty labels, unknown override names, booleans masquerading as integers, wrong types, invalid enum values, and out-of-range values. This repairs the baseline behavior where misspelled axes were silently accepted and valid-looking requests could be clamped, ignored, or rejected according to the difficulty branch.

Alternative rejected: retain permissive `**overrides` behavior for backward compatibility. The review contract requires exact, falsifiable controls; silent fallback turns typos into false passes.

## D6 — Preserve canonical-looking anchors while adding orthogonal counterexamples

A pure counterexample-only distribution could teach the law but drift away from canonical appearance. The final schedule keeps one canonical anchor every four examples and supplies exact 5x5, 6x6, and 7x7 canonical-size/palette profiles in each band's first 20 draws.

The remaining profiles isolate the two missing factors:

- color variation without erasure;
- erasure with both orange and non-orange body values.

This supports transfer from canonical scenes while making each shortcut falsifiable.

## D7 — Reject the first two-profile repair after interaction self-review

The first repair alternated a canonical profile with a combined mixed-color/off-legend profile. It passed the declared `only_color7` and `keep_off_legend` checks, but the factors were perfectly coupled. The rival “recolor under headers and erase off-legend non-7 cells, but preserve orange off-legend cells” fit every default lesson.

I added a failing regression before changing production code (`checks/tdd-red-factorial-schedule-v2.log`) and replaced the design with four profiles. This is the key reason for the factorial schedule rather than a simpler alternating schedule.

## D8 — Duplicate the comprehensive erasure profile

A five-pair lesson has four demonstrations and one query. If there were only one comprehensive erasure board, holding it out would let color-conditioned erasure rivals survive. Two independent erasure profiles guarantee that every one-pair holdout leaves at least one board with both orange and non-orange off-legend cells.

Alternative rejected: increase `EXAMPLES_NEEDED`. Four demonstrations were sufficient once the schedule was designed correctly, so a larger lesson would add token/data cost without necessity.

## D9 — Make color roles observable

Header colors are sampled from nonzero colors excluding 7. Generated non-7 body colors are also chosen outside the current header palette. This keeps `uniform7`, `uniform_other`, and `mixed` recoverable from the grid and prevents a body policy from collapsing into “already equals the header.” Canonical inputs remain accepted by `self_check`; this restriction applies to generated examples, not the abstract rule.

Alternative rejected: allow arbitrary header/body overlap and infer the requested body policy from hidden metadata. Exact controls must be observable from the returned grid.

## D10 — Declare rivals that fit the canonical data

The canonical demonstrations admit all four declared rivals:

- apply the header only to color 7;
- keep off-legend body content;
- erase only non-7 off-legend content;
- erase only 7 off-legend content.

`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and `WITNESS_RIVALS` are executable. The task-local independent probe verifies each rival fits all three canonical pairs before using it as lesson evidence.

Alternative rejected: rely on prose claims or generic simple transforms. The repair's important competitors are task-specific conditional programs.

## D11 — Test ordered production and arbitrary query rotation separately

Production uses the linked four-profile sequence. The shared semantic smoke checks 12 lessons, while the larger census materializes 100 lessons per band and holds out every labeled pair once. Final results are reported separately: 0/300 production ambiguities and 0/1,500 rotation ambiguities. Task tests additionally enumerate cyclic starts for the small deterministic schedule.

This remains finite evidence against declared deterministic rivals; it is not a uniqueness proof over all programs.

## D12 — Build portable, independent tooling

The new tests use `reviewer_support.find_root`/`canonical_pairs` through `workspace/reference_probe.py`, so they work in the packet runtime and fresh patch replay. The independent oracle reimplements the rule and rivals instead of importing generator-private helpers, reducing correlated-test risk.

## D13 — Preserve genuine solve records and source binding

The blind solve was completed before any generator inspection. The post-repair solve was prepared again after the final factorial edit, so `solve/summary.json` names the actual final generator hash. Earlier rule exposure is recorded as `yes`; no masked-answer or reference consultation is claimed.

## D14 — Keep audit targets findings-only

`cf5ccd73cfe5` and `258e1a721c75` were reproduced but not edited. Their exact assigned hashes remain unchanged. The return contains small reproducer scripts, inputs, selected Racket outputs, and full/summary check evidence under `checks/audit/` and `checks/audits/`.

## D15 — Final acceptance boundary

No shared tool, canonical authority, base solution, or unrelated generator was changed. Catalog approval/training admission remains a maintainer decision. The repair is accepted here only as a source-bound reviewer result with documented finite limits.
