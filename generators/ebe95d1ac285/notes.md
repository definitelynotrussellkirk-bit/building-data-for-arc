# Current account: `ebe95d1ac285`

## Intended rule

Find the unique color-2 anchor object. Classify each 4-connected monochrome object by (a) whether it touches the outer border and (b) whether its normalized shape is symmetric under top/bottom reflection and under left/right reflection. Recolor every non-anchor object with the same complete signature to color 8; preserve everything else.

## Current generator decision

Version 3.0.0 uses a constructive connected-polyomino catalogue and deterministic slot placement. Declared axes are exact and observable: grid height/width, anchor reflection class, anchor border contact, match count, same-touch/different-symmetry distractor count, same-symmetry/opposite-touch distractor count, and neutral distractor count. Invalid or impossible calls fail loudly; there is no degraded fallback.

Every scene includes both conjunction-breaking distractor classes. `touch_only` and `symmetry_only` are declared executable rivals, with witnesses and a lesson hook. A small deterministic schedule supplies both canonical dimension/palette profiles while all eight anchor signatures remain represented. Sparse connected 12-cell shapes preserve canonical object scale without forcing every sample to be large.

## Reversed choices

- Removed inherited dead/ignored texture and dimension controls rather than pretending they were advisory.
- Replaced rejection-heavy random construction and fallback with constructive placement.
- Removed an over-strict blank-moat condition after an official input showed diagonal contact is lawful.
- Expanded the canonical-profile schedule after the first repair reached only 14/60 required profiles.

## Evidence and limits

Final generator SHA-256: `99dd3e5428dca66f4778723a11c98da8686cd0211f59dc469f2aeb0eea57527d`. Portable focused tests pass 78/78. The final semantic gate requires query rotations; a 300-lesson / 1,200-rotation census reports zero ambiguity or hook/scoring errors. The full override matrix covers 48,960 accepted draws across 544 cases and three bands with zero findings.

The Racket authority was not changed. The finite declared-rival pass does not prove that no other hypothesis can fit the sampled lessons. Unique nuisance colors and the fixed color-2 role are intentional grammar restrictions inherited from the task semantics.
## Current reviewer considerations

Source SHA-256: `99dd3e5428dca66f4778723a11c98da8686cd0211f59dc469f2aeb0eea57527d`.

# Decisions for `ebe95d1ac285`

## D1 — Replace the inherited axis surface instead of patching ignored controls

**Prior choice and rationale:** The previous source declared dimensions, counts, and texture-like controls that were partly ignored or could not be recovered from the returned grid. Its original rationale is not documented beyond the inherited code.

**Decision:** Keep only eight exact axes whose values can be observed from the output input grid. Validate unknown keys, booleans-as-integers, nonintegral values, ranges, `difficulty`, and `sample_index` before construction.

**Alternatives rejected:** Keeping dead texture aliases for backward compatibility would preserve silent contract lies; treating them as advisory would still let the override checker report false exactness.

**Probe and failure mode:** The baseline override run produced 53,081 findings. The final full matrix exercises 48,960 accepted draws across 544 cases and three bands with zero findings. A future axis addition must first acquire an observer and boundary tests.

## D2 — Construct scenes from a connected polyomino catalogue

**Prior choice and rationale:** Random shape sampling plus rejection was easy to write but could exhaust attempts and fall through to an invalid fallback.

**Decision:** Use a fixed, hash-seed-stable catalogue spanning all four reflection classes, including sparse connected 12-cell shapes, and place objects in deterministic slots. Fail loudly if a requested contract cannot be built; never return a degraded scene.

**Alternatives rejected:** More retries would only lower the probability of the same defect. A generic backtracker was prototyped but was unnecessarily expensive over hundreds of samples. The final slot constructor is simpler and fully exercised by exact-axis tests.

**Probe and failure mode:** An early large-shape catalogue accidentally contained a disconnected member; the focused suite failed 22 cases and forced correction. Future catalogue entries must pass connectivity and symmetry classification tests before use.

## D3 — Teach the conjunction in every generated example

**Prior choice and rationale:** The previous generator relied on aggregate variety; it did not ensure that a learner had to use both semantic features.

**Decision:** Every scene includes at least one true match, a `same_touch_wrong_sym` distractor, and a `same_sym_wrong_touch` distractor. Optional neutral distractors vary count without carrying the teaching burden.

**Alternatives rejected:** Relying on chance across a lesson can produce individually correct labels that support touch-only or symmetry-only hypotheses. Adding only one near-miss class leaves the other shortcut viable.

**Probe and failure mode:** `touch_only` and `symmetry_only` are executable rivals declared in both shortcut and lesson contracts. The required-rotation semantic gate and 300-lesson census report zero surviving query-changing rivals. Undeclared hypotheses remain a stated limitation.

## D4 — Use unique nuisance colors and preserve color 2 as the anchor role

**Prior choice and rationale:** Canonical inputs identify the reference object by color 2; other object colors are semantically irrelevant.

**Decision:** Give each non-anchor object a distinct nuisance color, exclude output color 8 from inputs, and leave color 2 unchanged.

**Alternatives rejected:** Reusing one color for multiple separated objects would complicate object extraction and could create per-color aggregation shortcuts not present in the intended grammar. Randomly moving the anchor role to another color would contradict the authority.

**Failure mode:** Unique colors make component identity easy, so geometry must carry the actual selection burden. The two mandatory near-miss classes ensure that no non-anchor color consistently implies output status.

## D5 — Preserve canonical support with an explicit profile schedule

**Prior choice and rationale:** Purely broad random dimensions missed the profile-floor requirement even when semantics were correct.

**Decision:** Deterministically assign a small subset of anchor signatures to the two canonical dimension/palette profiles while retaining all eight anchor signatures and broad dimensions elsewhere.

**Alternatives rejected:** Copying canonical coordinates would risk memorization. Forcing large shapes or canonical dimensions in every sample would narrow diversity.

**Probe and failure mode:** The first schedule produced 14/60 exact profiles against a 15/60 floor; expanding the scheduled residue set made the final profile gate pass. The exact-profile schedule is covered in the focused suite.

## D6 — Do not change the Racket authority

**Prior choice and rationale:** The selected Racket program already matched all canonical pairs; the defect was in generation and lesson assembly.

**Decision:** Pin the normalized rule hash and verify selected-source synchronization and execution parity. No rule source, canonical data, or archival authority was edited.

**Alternative rejected:** Rewriting a correct authority to mirror generator internals would blur the independent-oracle boundary.

## D7 — Require query-rotation identifiability

**Prior choice and rationale:** The standard semantic smoke treats rotations as diagnostic because some curricula are intentionally ordered.

**Decision:** This task claims arbitrary query placement, so the final semantic gate uses `--require-rotations-identifiable`; the larger census uses `--rotate-query` with required policy.

**Probe and limits:** The census materialized 300 lessons, 1,200 production pairs, and 1,200 rotations with zero ambiguity or scoring/hook errors. This proves only the tested declared rivals and sampled support, not all possible rules.

## D8 — Keep the post-repair solve honest and source-bound

The solve was prepared only after generator hash `99dd3e…` was frozen. One visible-only implementation passed all three demonstrations. Because the rule had already been seen during repair, `earlier_rule_exposure=yes`; no generator, Racket source, reference solution, or private label was consulted during the solve.
