# Current notes: b6ba2d176fe8

## Intended rule

The input contains 2–6 distinct-color solid rectangular components separated left-to-right by at least one blank column. Sort components by source left bbox column. On a fresh same-size zero canvas, paint each rectangle’s bbox dimensions starting at `(0,0)`; after a rectangle of height `h` and width `w`, advance by `(h-1,w-1)`. Consecutive rectangles share one corner and the later rectangle owns it.

## Current distribution and assumptions

- Unoverridden draws use a 30% official-profile prior and 70% broader lawful geometry.
- Official profiles are 10×10, bottom-aligned, compact, and contain 3 or 4 objects.
- Generalized draws retain difficulty-dependent object counts/canvas ranges, row layouts `bottom|mixed|scattered`, and column layouts `compact|irregular|spread`.
- Components are solid, have distinct nonzero colors, area at least 2, dimension diversity, at least one non-square rectangle, and enough unchanged-canvas room for the staircase.
- Explicit general-axis overrides bypass the random canonical prior unless `canonical_prior=True` is itself explicit.

## Review-7af9419bc1a75fd5 decisions and evidence

- **Strict API boundary:** literal integer seed; nonnegative literal integer sample index; exact difficulty string/None; exact bool/int/enum overrides. Malformed values now raise `ValueError` before `gen_ctx`. Reproducer: `counterexamples/review-7af9419bc1a75fd5/strict_scalar_boundary.json`.
- **Canonical compatibility:** `canonical_prior=True` accepts exact `n_objects` 3 or 4 by filtering official profiles. Counts 2/5/6, non-bottom rows, and non-compact columns are declared value-specific incompatibilities.
- **Teaching contract:** `strict_canonical_like = self_check`; witness `shared_corner_ownership`; rival/lesson competitor `earlier_corner_owner`. Final semantic evidence: 600/600 strict and witness hits, 60/60 rival disagreements, 12/12 3-demo lessons identifiable, 0/48 ambiguous query rotations.
- **Authority:** selected `racket_target.target_code` was formatting-synchronized exactly to canonical program SHA `7c21d73859afbccc68dd227a0093cce43d0a7921ad044563e12ffe27fdba1a03`; canonical source and archival `raw_code` were not changed semantically.
- **Version:** retained `3.0.0` because the inherited frozen fixture asserts it. Final generator SHA is `53981d265a66ee0cf0c971254564f6c66f361064671a7e1da3a56e7f8448c3cd`.
- **Proposed variant:** `workspace/parametric/` contains an unapproved episode-level `sort_order` prototype (`left_to_right|right_to_left`). It is separate from production and labels every pair with protected Racket.

## Known limits and open findings

- Semantic evidence is finite and covers declared rivals/settings, not all possible ARC hypotheses.
- Query rotations were diagnostic, not required production ordering, though all 48 checked rotations were non-ambiguous.
- The proposed parameter has evidence for two settings and two retained episodes only; it is not approved training data.
- No selected-task blocker remains: final battery 12/12 green and portable selected-task tests 37/37. Masked solve correctness remains independently scored.

Imported historical notes remain in `evidence/associated_notes.jsonl`.


## Current external prototype follow-up

Review `review-7ab6474ceb76fd4f` resolved the task-local export/count defects without changing production generation or canonical authority. Public filenames now equal the SHA-256 of exact canonical visible challenge bytes and therefore exclude seed, hidden setting, program, query answers, and private metadata. Demonstration and query counts are independent (`3..8` and `1..8`); the default episode is 3 demonstrations plus 4 simultaneous distinct queries, all executed through protected Racket. `workspace/parametric/adapter.py` and `promotion.json` provide the bounded future-worker interface. The variant remains proposed and unapproved; retained evidence is finite and source-bound.
Owner follow-up: all17focused prototype tests passed on the selected correction, including real Racket replay and public-ID/count/privacy regressions. The original external finding and exact old prototype are preserved under `evidence/parametric-external-followup-7af9419bc1a75fd5/historical/`; its current inventory now points to those prior bytes and records the scoped resolution. Current proof: `evidence/owner-public-identifier-correction/manifest.json`. This resolves only the identifier/count follow-up; parameter qualification, acceptance and training admission remain separate.

## Current reviewer considerations

Source SHA-256: `53981d265a66ee0cf0c971254564f6c66f361064671a7e1da3a56e7f8448c3cd`.

# Decisions for `b6ba2d176fe8`

All selected-generator decisions below bind to final generator SHA-256 `53981d265a66ee0cf0c971254564f6c66f361064671a7e1da3a56e7f8448c3cd`. Finding IDs match `REVIEW.md`.

## D1 — Preserve the intended transformation

**Choice.** Keep the original task rule: recover solid monochrome rectangles, order them by left bbox column, redraw them on a same-size zero canvas as a corner-overlapping staircase, advance by `(h-1,w-1)`, and let the later rectangle overwrite the shared corner.

**Original rationale.** This behavior is documented by the generator summary and solves all four canonical pairs. The exact source history before this packet is unknown.

**Alternatives rejected.** Reordering by color, size, or source row; preserving source gaps/rows; allowing the earlier rectangle to own a shared corner. The retained `earlier_corner_owner` rival is lawful but disagrees on every generated witness checked.

**Probe/evidence.** `B6-SEMANTIC-CONTRACT`, final semantic gate, 120-rule smoke applications, and first-revision visible solve.

**Failure modes/limits.** The declared rival covers corner ownership, not every conceivable alternative ordering or object interpretation.

## D2 — Keep the mixed canonical/generalized distribution

**Choice.** Preserve the preexisting 30% canonical prior and 70% generalized prior for unoverridden draws. Preserve the four 10×10 canonical geometry profiles and broader dimension-profile tables.

**Original rationale.** Source comments state that canonical geometry should remain positive-measure while broader legal layouts provide coverage. The exact historical reason for 30% is not recorded.

**Alternatives rejected.** Removing the canonical prior would risk drifting away from demonstrated geometry; forcing only canonical profiles would collapse diversity; retuning the 30/70 ratio was unnecessary because profile-floor and diversity checks were already healthy.

**Probe/evidence.** 4/4 canonical inputs accepted, 15/60 exact-profile hits across all bands, 300 pairs with 100% unique inputs and outputs.

**Failure modes/limits.** Sixty profile-floor draws estimate support but do not prove long-run proportions exactly. The canonical profiles cover only object counts 3 and 4.

## D3 — Make exact general-axis overrides bypass the random canonical prior

**Choice.** When `n_objects`, `row_layout`, or `column_layout` is explicitly supplied and `canonical_prior` is not, force the generalized branch. When `canonical_prior=True` is explicit, honor it or reject an incompatible exact combination before generation.

**Original rationale.** The existing implementation already aimed for exact-or-loud overrides. A valid exact override must not fail stochastically because a 30% canonical draw cannot realize it.

**Alternatives rejected.** Randomly retrying until compatible hides the contract and consumes variable work; silently coercing to a canonical-compatible value violates exactness; rejecting every multi-axis combination discards valid requests.

**Probe/evidence.** `B6-OVERRIDE-CONTRACT`: 6,750 matrix draws, 6,120 accepted, 630 declared refusals, 0 findings.

**Failure modes/limits.** The declaration must be updated if canonical profiles or axes change.

## D4 — Filter canonical profiles for compatible `n_objects`

**Choice.** For `canonical_prior=True`, filter official profiles to the requested object count. Counts 3 and 4 are accepted; 2, 5, and 6 reject explicitly.

**Original rationale.** The prior code recorded an exact object count after choosing a random profile, which made compatible requests fail depending on profile selection. Filtering is the smallest deterministic repair.

**Alternatives rejected.** Adding invented 2/5/6-object “canonical” profiles would no longer be canonical; ignoring `n_objects` would violate the override; random retries would be opaque.

**Probe/evidence.** Focused regressions for both compatible counts and the final override matrix.

**Failure modes/limits.** “Canonical” remains tied to the four official 10×10 profiles.

## D5 — Retain all declared input axes and difficulty defaults

### `n_objects`

**Choice.** Retain exact domain 2..6; defaults remain easy 2..3, medium 3..4, hard 4..6.

**Original rationale.** Encodes difficulty through object count while keeping ARC canvas constraints tractable; deeper historical rationale is unknown.

**Rejected alternatives.** Expanding beyond six risks width/height overflow and color exhaustion; narrowing would reduce hard examples and coverage.

### `row_layout`

**Choice.** Retain `bottom`, `mixed`, and `scattered`; easy favors bottom, medium is balanced, hard favors scattered/mixed.

**Original rationale.** Decouples the semantic rule from the canonical bottom alignment. Exact weighting history is unknown.

**Rejected alternatives.** Bottom-only creates a shortcut; arbitrary per-cell placement would violate solid rectangles.

### `column_layout`

**Choice.** Retain `compact` (1-column gaps), `irregular` (one 2-column gap), and `spread` (3-column gaps); difficulty weights remain unchanged.

**Original rationale.** Prevents source-gap preservation from being the target rule and expands visual variety. Exact weighting history is unknown.

**Rejected alternatives.** Zero gaps can merge same-color-adjacent structures and violate the separator invariant; larger arbitrary gaps increase overflow pressure without adding a new concept.

### Dimensions, canvas, starts, and colors

**Choice.** Retain the curated dimension profiles, difficulty canvas ranges, random legal left padding/rows, zero background, and distinct nonzero colors.

**Original rationale.** Source comments require area ≥2, dimension diversity, at least one non-square rectangle, and enough space for the output staircase. Distinct colors make object identity unambiguous.

**Rejected alternatives.** Random unconstrained dimensions would cause frequent overflows or degenerate squares; repeated colors would require a different component/color semantics; changing background would alter the canonical rule.

**Probe/evidence.** Self-check, distribution gate, profile floor, diversity, grammar, and rule smoke all pass. These checks validate legality and coverage, not an optimal pedagogical weighting.

## D6 — Reject malformed scalars at the public boundary (`B6-SCALAR-BOUNDARY`)

**Choice.** Require literal `int` for `seed`, nonnegative literal `int` for `sample_index`, exact `str|None` for difficulty, exact `bool` for `canonical_prior`, exact integer 2..6 for `n_objects`, and exact enum strings for layouts. Do not coerce booleans, floats, or numeric strings.

**Original rationale.** Unknown. Baseline behavior inherited Python’s `bool`/`int` relationship and broad `gen_ctx` acceptance, producing silent acceptance or internal `AssertionError`.

**Alternatives rejected.** Coercion makes recipes non-canonical and can collapse distinct calls; letting malformed values reach self-check leaks internal assertions; accepting negative sample indexes contradicts the deterministic recipe domain.

**Probe/evidence.** Counterexample JSON records baseline/final behavior. Tests were observed RED then GREEN. Final strict defect lint reports zero flags.

**Failure modes/limits.** This is task-local validation; other generators need a shared lint/gate rather than copying code blindly.

## D7 — Declare only genuine incompatibilities (`B6-OVERRIDE-CONTRACT`)

**Choice.** Declare value-specific conflicts for `canonical_prior=True` with object counts 2/5/6, non-bottom rows, or non-compact columns.

**Original rationale.** Canonical profiles are 10×10, bottom-aligned, compact, and have 3 or 4 objects.

**Alternatives rejected.** A blanket “canonical prior conflicts with every other axis” would falsely reject compatible count 3/4 controls. Omitting declarations produced 720 unexplained baseline refusals.

**Probe/evidence.** Final matrix explains all 630 refusals as declared; no root causes or warnings remain.

**Failure modes/limits.** Value-specific declarations are coupled to canonical-profile inventory.

## D8 — Add an executable teaching contract (`B6-SEMANTIC-CONTRACT`)

**Choice.** Alias `strict_canonical_like` to `self_check`; declare `shared_corner_ownership`; declare the full-grid `earlier_corner_owner` rival; bind it through `WITNESS_RIVALS` and `LESSON_COMPETITORS`.

**Original rationale.** Baseline had no semantic hooks. Later-corner ownership is the most local plausible ambiguity that every lawful generated input exposes.

**Alternatives rejected.** A trivial malformed-output rival would not test the lesson; using a witness without a rival would only measure frequency; changing production generation solely to make a rival fire was unnecessary.

**Probe/evidence.** 600/600 witness hits, 60/60 authority/rival disagreements, 12/12 production lessons identifiable, 0/48 ambiguous rotations.

**Failure modes/limits.** The gate establishes separation from declared rivals and bounded generic mutations, not global rule uniqueness. `lesson_identifiable` remains undeclared because the shared rival machinery suffices.

## D9 — Synchronize selected authority formatting only (`B6-AUTHORITY-SYNC`)

**Choice.** Use the official selected-only authority tool to copy canonical `program_solution` text into `racket_target.target_code`. Preserve canonical ledger and archival `raw_code` bytes.

**Original rationale.** Baseline selected code was whitespace/comment-normalized equivalent and execution-equivalent but exact-text divergent.

**Alternatives rejected.** Editing canonical authority was unnecessary; rewriting archival `raw_code` would destroy provenance; leaving exact divergence kept the authority gate red.

**Probe/evidence.** Official proposal and apply receipts under `checks/authority-sync/`; final authority sync and rule smoke PASS.

**Failure modes/limits.** Archival divergence remains intentionally reported.

## D10 — Keep `VERSION = "3.0.0"`

**Choice.** Do not bump the version in this return.

**Original rationale.** The inherited frozen fixture asserts 3.0.0, and packet rules prohibit modifying it. Source and evidence hashes uniquely identify the repair.

**Alternative considered.** A version bump would normally advertise changed API validation, but would make the immutable fixture fail and block the required portable snapshot.

**Failure mode/limit.** Maintainers may choose to migrate the fixture and version in a later integration change.

## D11 — Prototype `sort_order` separately (`B6-PARAMETRIC-SORT`)

**Choice.** Propose one episode-level parameter with values `left_to_right` (default) and `right_to_left`. Choose it once per episode; keep object extraction, dimensions, staircase geometry, shared-corner ownership, and input grammar unchanged. Do not add it to production `generate()`.

**Original rationale.** The parameter changes one compositional choice while preserving the family’s reasoning structure. It creates a finite alternate that demonstrations can identify.

**Alternatives rejected.** Parameterizing corner ownership was used as a semantic rival instead: it changes a local overwrite convention and is more valuable as a required counterexample. Parameterizing colors, canvas size, or gap layout changes nuisance generation rather than the rule. Arbitrary object-order permutations enlarge the setting space without a clear lesson benefit.

**Probe/evidence.** Default exact Racket SHA `7c21d738...`; alternate SHA `dff686c...`; 2 complete episodes, 8 protected-Racket pairs, 2 rival checks. In both episodes all three demonstrations refute the alternate and the query also differs. Public files expose only train examples and query input.

**Failure modes/limits.** Only two declared settings and one seed’s four inputs are retained. The prototype is unapproved; it does not prove that every future sampled episode is identifiable. Its verifier and nonzero failure exit are intended to make expansion safe.

## D12 — Stop after final green evidence

**Choice.** Do not refactor the working generator or widen its semantic rivals after all specified gates passed.

**Reason.** Additional changes would increase risk without a reproduced defect. The final self-review found and fixed only the prototype CLI exit-status issue using a RED→GREEN regression.

**Limit.** A fresh independent reviewer was unavailable in this harness; the final code review was author self-review, recorded under `checks/final-review/SELF_REVIEW.md`.
