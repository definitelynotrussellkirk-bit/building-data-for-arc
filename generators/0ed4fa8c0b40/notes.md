# Working notes: 0ed4fa8c0b40

## Review `review-28a539988b46d04c` — 2026-09-28

The version-2 generator implemented the broad idea but had zero canonical-profile support, a presence-only self-check, stale/aliased axes, no semantic contract, an unpinned rule, and no generated case separating relative arrow direction from absolute grid position.

Version 3.0.0 preserves the canonical Racket behavior and replaces the distribution with a four-slot linked curriculum:

1. canonical right;
2. canonical left;
3. right arrow whose apex is left of grid center;
4. left arrow whose apex is right of grid center.

The strongest canonical shortcut is `direction_from_absolute_apex_column`. Exact witness: seed `314159`, sample index `2`, medium. Its Python intended output equals canonical Racket execution, while the shortcut differs. See root `QUESTION_ANSWER.md` and `checks/exact-shortcut-counterexample.json` in the review return.

Design notes:

- Cyan connectivity is intentionally 8-neighbor because canonical supports contain diagonal joins.
- Negative textures are explicit malformed fixtures, not ordinary axis values.
- Every axis is recovered by `observe_overrides`; all declared combinations are constructible.
- `lesson_identifiable` checks six concrete rivals, and every sliding four-demo window must eliminate them.
- The selected active target text is canonical-exact; archival `raw_code` is retained unchanged.

Verification in the review packet: focused tests `13/13`; full after battery `12/12` green; override sweep `39,780/39,780`; semantic lessons `12/12` identifiable; Racket mirror `120/120`.
## Current reviewer considerations

Source SHA-256: `af8752f33ee03ccd3859cdf5ac10ef015eabc9be4f5d6fcb2b4f078b50de33ba`.

# Design Decisions: `0ed4fa8c0b40`

## D1. Preserve the canonical transformation and pin its identity

**Decision.** Keep the canonical Racket rule unchanged, add `RULE_HASH = "d42dbc127318"`, provide a Python diagnostic mirror, and make the selected active target text exactly equal to the canonical program.

**Original rationale.** The prior generator described the correct reflection behavior, and both canonical-pair checks and Racket smoke showed the underlying rule behavior was sound. The problem was curriculum/contract quality, not the intended transformation.

**Alternatives considered.** Rewriting or “simplifying” the Racket program; adopting the archival `raw_code`; leaving active texts behaviorally equivalent but textually divergent.

**Probe.** Canonical pairs, 120 generated inputs, Racket execution parity, and authority synchronization.

**Failure modes avoided.** Silent rule drift, stale review hashes, and uncertainty over which active program is selected.

**Limitation.** Archival `raw_code` remains textually divergent by design; it is provenance rather than the selected authority.

## D2. Replace nominal axes with observable semantic axes

**Decision.** Remove `direction="rng"`, `cyan_density`, `anchor_corner`, and the old position aliases. Use exact `direction`, `fill_level`, `arrow_vertical`, and `arrow_horizontal` axes, plus exact grid/cyan dimensions.

**Original rationale.** The old axis list appears to have been written as a generative wish list. Several axes were stale, clamped, aliased, silently ignored, or incompatible with difficulty-specific draw ranges.

**Alternatives considered.** Retaining compatibility aliases; marking stale axes diagnostic; expanding all old valid ranges and adding many incompatibility declarations.

**Probe.** The exhaustive override-contract checker plus `observe_overrides()` and focused boundary tests.

**Failure modes avoided.** A caller believing an override was applied when it was not, a typo being silently accepted, and declared values failing only in some difficulty bands.

**Limitation.** This is an intentional API break for invalid or misleading old overrides. Valid task semantics remain available through clearer names.

## D3. Use a linked four-profile curriculum rather than independent random draws

**Decision.** Cycle through canonical-right, canonical-left, absolute-column-trap-right, and absolute-column-trap-left profiles by `sample_index mod 4`.

**Original rationale.** Independent randomness can produce a locally diverse corpus while still yielding an uninformative lesson. The review question requires the demonstrations as a group to rule out shortcuts.

**Alternatives considered.** Pure random sampling with rejection until coverage; seed-dependent random profile ordering; only canonical-shape generation.

**Probe.** Every sliding four-demonstration window across all three difficulty bands is passed through `lesson_identifiable()`.

**Failure modes avoided.** All-right lessons, all-dense lessons, no canonical anchor, and no example that separates relative arrow geometry from absolute grid position.

**Limitation.** Profile order is predictable. That is acceptable because schedule coverage, not sequence unpredictability, is the objective.

## D4. Retain canonical-profile support explicitly

**Decision.** Emit `6×9` examples with a `3×3` cyan bounding box and central bottom arrow in two of four slots.

**Original rationale.** The baseline emitted zero exact/envelope canonical profiles in 60 draws. A generator can be behaviorally correct yet teach a noticeably different task if it never shows source-like cases.

**Alternatives considered.** Relying only on broader grids; exact replay of canonical examples; increasing `MIN_STRICT_FRAC` above one half.

**Probe.** Canonical profile floor, strict-profile hook, and all-band focused tests.

**Failure modes avoided.** Distribution drift and a learner treating the broadened geometry as the actual task definition.

**Limitation.** The generated cyan masks are not copies of the four canonical inputs; they preserve the linked profile while varying support.

## D5. Interpret the yellow marker as exactly five cells

**Decision.** Decode only a bar of three cells, one stem cell, and one apex displaced one column left/right from the bar center.

**Original rationale.** The old comments called the marker a “plus-arrow,” but the actual canonical marker has five cells. The previous `self_check` accepted any yellow pixels, including an ambiguous two-apex fixture.

**Alternatives considered.** Accepting supersets containing a recognizable arrow; choosing the first match; permitting arbitrary rotations.

**Probe.** Canonical acceptance, malformed-arrow mutation, ambiguous fixture, and exact decoder uniqueness.

**Failure modes avoided.** Multiple direction readings, extra yellow decoys accidentally changing the topmost yellow cell, and validator/rule disagreement.

**Limitation.** The validator does not support rotated vertical arrows because the canonical rule does not define them.

## D6. Use 8-connectivity for the cyan support

**Decision.** Require one 8-connected cyan support whose bounding box is `2..3 × 2..3` and spans every row/column of that box.

**Original rationale.** Some canonical supports are joined diagonally. Four-connectivity would incorrectly reject valid source inputs.

**Alternatives considered.** No connectivity requirement; four-connectivity; arbitrary disconnected cyan cells.

**Probe.** All canonical inputs, explicit disconnected mutations, and reflected-copy fit checks.

**Failure modes avoided.** Accepting unrelated cyan objects whose shared global bounding box makes the rule ambiguous, while still preserving canonical diagonal structures.

**Limitation.** A disconnected scene that the raw Racket code could mechanically process remains outside the teaching grammar.

## D7. Separate lawful lessons from negative fixtures

**Decision.** Keep `no_arrow`, `no_cyan`, and `ambiguous_arrow` callable only as explicit diagnostic textures; exclude them from ordinary axes and require `self_check` to reject them.

**Original rationale.** The defect linter found negative textures inside the valid texture domain, and `ambiguous_arrow` passed validation.

**Alternatives considered.** Delete the fixtures; declare them lawful; let generation return invalid examples as ordinary data.

**Probe.** Parametrized tests over every degenerate texture and defect-lint rerun.

**Failure modes avoided.** Training on examples without a defined answer and allowing linter sampling to confuse negatives with valid support.

**Limitation.** Diagnostic generation intentionally returns a malformed grid rather than raising; callers must run `self_check`, as the test tools do.

## D8. Prefer sparse asymmetric supports plus a dense contrast

**Decision.** Sparse profiles choose an 8-connected mask with holes and horizontal asymmetry when possible; dense profiles fill the bounding box.

**Original rationale.** A solid rectangle cannot distinguish reflection from translation and cannot show whether holes are preserved. Sparse asymmetric masks make both properties observable, while dense examples show the same rule is not conditional on holes.

**Alternatives considered.** Arbitrary Bernoulli density; only sparse masks; only canonical mask templates.

**Probe.** Executable rivals `translate_without_reversing` and `fill_reflected_bbox`, witness firing counts, and diversity checks.

**Failure modes avoided.** A learner filling the reflected bounding box or copying without reversing columns.

**Limitation.** Mask enumeration is tiny but contributes to the cost of exhaustive override testing.

## D9. Make the canonical shortcut explicit and executable

**Decision.** Name `direction_from_absolute_apex_column` as a canonical shortcut and generate arrows at a left/right extreme with the opposite relative direction.

**Original rationale.** In every canonical demonstration the arrow is centered, so absolute apex location and relative apex offset are perfectly correlated.

**Alternatives considered.** Merely moving the arrow while keeping the same absolute-side correlation; describing the shortcut only in prose; using random off-center arrows without coverage guarantees.

**Probe.** Exact seed `314159`, index `2`, medium; canonical Racket execution; semantic gate witness counts; every sliding lesson.

**Failure modes avoided.** A generator that looks spatially diverse but never breaks the confound.

**Limitation.** This is the strongest identified shortcut, not a proof that no imaginable program fits finite examples. The declared competitor set is intentionally concrete and testable.

## D10. Add executable future-agent tools at the task boundary

**Decision.** Put the Python mirror, rival functions, witnesses, override observer, profile hook, and focused tests next to the generator.

**Original rationale.** Prior notes contained no executable reasoning trail. Future reviewers otherwise have to rediscover the rule, manually inspect grids, and trust prose claims.

**Alternatives considered.** A standalone notebook; only root-level review prose; relying entirely on corpus-wide tools.

**Probe.** Focused 13-test suite plus the full shared battery.

**Failure modes avoided.** Regression to nominal axes, reintroduction of the canonical shortcut, mismatch between validator and rule, and unverifiable audit claims.

**Limitation.** These hooks cover this task's known rivals; future findings should extend the maps and tests rather than weakening the current contract.

## Review `review-6cec8c042909a5d9` — 2026-10-23

Pinned baseline source `af8752f33ee03ccd3859cdf5ac10ef015eabc9be4f5d6fcb2b4f078b50de33ba` retained the prior v3 semantic repair but failed the strict defect linter with 24 warnings: coercible `seed`/`sample_index` values and negative indices were accepted across bands. The current source adds one request-boundary validator used by both `generate()` and `schedule_profile()`. It requires literal Python `int`, keeps all integer seeds (including negative/large), and requires nonnegative indices. Valid generation behavior is unchanged, so `VERSION=3.0.0`, `RULE_HASH=d42dbc127318`, and canonical Racket authority remain unchanged.

Final source SHA-256: `5ff1e2d5705bf658b3ce6c0247c5fee012ae53b8952e21670137c15a90a4974f`.

Verification:

- strict after battery: 12/12 green;
- portable selected task tests: 71/71;
- override sweep: 39,780 accepted cases, no findings/warnings;
- profile exact/envelope hits: easy 7/20, medium 9/20, hard 12/20, pooled 28/60;
- source-bound lesson census: 300/300 materialized, 1,500 production pair checks and 1,500 rotations, 0 ambiguous, 1,029 unique exact inputs;
- strongest shortcut witness regenerated from final source at seed 314159/index 2 and matched canonical Racket execution.

The original-family parameter assessment is retained separately in `workspace/parametric/`: `copy_style={mirror,translate}` × `gap={0,1}`. All four exact Racket settings match an independent Python assertion, and each three-demo episode refutes the other three settings. `mirror-gap0` is the canonical/default behavior on prototype-lawful inputs. These are bounded prototypes only; they do not alter production sampling or approval.

Current limitations remain those of the prior v3 design: the declared rival set and finite census are not universal uniqueness proofs; the production curriculum is deliberately ordered; archival `raw_code` remains provenance-only. The parametric prototype is restricted to asymmetric 3×3 cyan supports with sufficient margin and requires separate review before any production use.


## Review `review-b6a239ca4469c5fe` — public export correction

The retained external finding reproduced exactly: the prior writer emitted four filenames containing `mirror|translate` and `gap0|gap1`, while `build_episode()` rejected separate demonstration/query counts. Prototype v1.1.0 now delegates the public projection and identity to `reviewer_support.public_challenge_bytes` / `public_challenge_id`, names files with the full visible-byte SHA-256, sorts batches by that ID, and rejects duplicate visible payloads before creating output. Private settings, seeds, enumeration order, Racket text and query answers do not affect public paths.

The return format forbids deleting baseline source files, so the four prior setting-named samples remain byte-for-byte as historical fixtures only. Prototype v1.1.0 neither emits nor references them; its current examples under `examples/current/` and manifest use the four content-hash filenames.

Episode inputs now come from separate deterministic demonstration/query streams with independently validated counts (`1..8` each). The retained command uses three demonstrations and four distinct queries for each of the four fixed settings. Every output is executed through its exact Racket rule; demonstrations alone leave only the selected setting, and all four queries are checked against those demo-consistent survivors without borrowing query answers. The canonical generator, production sampling, `RULE_HASH=d42dbc127318`, and approval state are unchanged. The extension remains a bounded unapproved prototype; its finite four-setting rival family is not a universal identifiability proof.
