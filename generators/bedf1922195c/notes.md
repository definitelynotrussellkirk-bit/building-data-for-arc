# Working notes: bedf1922195c

## 2026-10-05 review `review-5835e46a6b85e736`

The imported 1.2.1 generator was positive-only, two-color, missing a rule hash,
and advertised controls that were neither exact nor reliably observable. The
selected authority also had a comment-only `target_code` difference from the
canonical/raw source.

The reviewed 2.1.0 generator uses nine exact scene profiles across three bands.
Every generated input has two qualifying blue segments, including one length 7;
three scheduled branches pair even-blue, bent-blue, and nonblue-odd negative
objects. The AB/BC/CA cycle makes every three consecutive demos, and every
three-demo remainder from four consecutive pairs, refute all four declared
canonical-fitting rivals.

A cached exhaustive placer keeps objects orthogonally separated and avoids
retry-cap failures. Task-local tests and `workspace/reference_probe.py` cover
rule binding, authority synchronization, canonical pairs, exact overrides,
cyclic windows, query rotations, independent rival parity, malformed inputs,
purity, determinism, and diversity.

Final source SHA-256:
`d8b86859af5852a4ffe654b5ecbba94fd3aeceeb21da9584975f9dbca0a0b38d`.
See packet-root `REVIEW.md`, `DECISIONS.md`, and retained `checks/` evidence.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `d8b86859af5852a4ffe654b5ecbba94fd3aeceeb21da9584975f9dbca0a0b38d`.

# Decisions for `bedf1922195c`

## D1 — Bind the rule before changing the distribution

**Choice.** Pin `RULE_HASH = "6a1fd35b307c"`, keep the canonical Racket semantics unchanged, and make the selected authority `target_code` byte-for-byte equal to canonical `program_solution` and bank `raw_code`.

**Why.** The baseline rule executed correctly on canonical data; the authority failure was textual divergence, not a transformation error. Changing semantics would have solved the wrong problem.

**Alternatives rejected.** Keeping the comment-only divergence would retain a failing authority gate. Rewriting the Racket program for style would add semantic risk without evidence of a rule defect.

**Probe.** Final authority sync groups all three sources under one exact SHA and executes 5/5 labeled canonical pairs successfully.

**Failure mode.** A future canonical rule change must update the hash, Python mirror, rivals, and tests together; exact text synchronization alone cannot certify semantic correctness.

## D2 — Replace many nominal controls with one exact scene profile

**Choice.** Expose only `scene_profile`, with nine finite values encoding dimensions, palette size, difficulty band, and semantic branch.

**Why.** Baseline axes were not independently observable or reliably honored. A finite exact profile is replayable, recoverable from returned pixels, cheap to exhaust, and honest about the grammar.

**Alternatives rejected.** Independent `grid_h`, `grid_w`, count, orientation, and texture axes would create a large joint domain with infeasible or semantically redundant combinations. Silent clamping was rejected because it makes provenance false. Declaring broad axes plus many incompatibilities was less legible than one exact profile.

**Probe.** Every profile is exercised under every difficulty hint in task tests; `observe_overrides` returns the requested profile exactly. The shared override checker accepted 900/900 draws and rejected an unknown key.

**Failure mode.** Exact profiles intentionally limit free recombination. New profiles should be added only with a unique pixel signature and full replay tests.

## D3 — Match canonical size and palette support without copying layouts

**Choice.** Include exact canonical `(height, width, palette-size)` signatures in every band’s schedule while also retaining larger scenes. Inputs use background 0, blue 1, no input red 2, and one or two sampled distractor colors from 3–9.

**Why.** The baseline’s two-color scenes never reached the canonical palette floor. Matching coarse profiles restores empirical support without replaying canonical geometry.

**Alternatives rejected.** Copying canonical arrangements risks memorization. Using a fixed distractor color would create a color-position correlation. Very large grids only would pass diversity while remaining off-manifold.

**Probe.** Profile floor: 39/60 exact hits, with 10/20 easy, 12/20 medium, and 17/20 hard; all five canonical inputs pass strict validation.

**Failure mode.** Coarse profile matching does not match the full canonical distribution of object counts or spacing.

## D4 — Teach positives and the strongest canonical-fitting negatives

**Choice.** Generate two blue positive segments; make one length exactly 7 and the other length 3 or 5. Pair two of three negative types in each scene: an even blue line, a bent odd blue object, and an odd straight nonblue line.

**Why.** Canonical examples alone allow four concise wrong rules: ignore color, parity, straightness, or generalize only to observed lengths 3/5. The generated objects make each condition independently observable.

**Alternatives rejected.** Positive-only generation preserves all four shortcuts. Placing every negative in every scene would be identifiable but repetitive and less useful for lesson-level reasoning. Making length 7 only occasional would let some 3-demo windows preserve the 3/5 shortcut.

**Probe.** The declared shortcuts reproduce every canonical pair. Final semantic sampling saw the length-7 witness 600/600; other witnesses fired 391–406/600, with each rival claim verified 60/60 when sampled.

**Failure mode.** These four rivals are not exhaustive. Finite rival elimination is evidence, not a proof that a human or model must infer the intended rule.

## D5 — Use an AB/BC/CA curriculum cycle

**Choice.** Cycle branches `parity_shape`, `shape_color`, and `color_parity` within each difficulty band.

**Why.** Any three consecutive demonstrations contain all three branch witnesses. In any four consecutive samples, holding out one pair still leaves three demonstrations that cover all three; the length witness is present in every sample.

**Alternatives rejected.** IID branch draws can accidentally omit a needed witness. A fixed branch per difficulty confounds difficulty with semantics. A longer cycle increases the minimum lesson size.

**Probe.** Task tests enumerate every cyclic start and all four query positions for `None`, easy, medium, and hard. Shared semantic smoke reports 12/12 identifiable lessons and 0/48 ambiguous rotations; the larger census reports 0/1,200 ambiguous rotations.

**Failure mode.** This guarantee assumes the downstream lesson assembler uses consecutive samples or a subset retaining at least three scheduled examples. Arbitrary filtering can still destroy coverage.

## D6 — Construct placements exhaustively, then optimize traversal

**Choice.** Precompute all translations of each immutable shape, sort larger objects first, and perform exhaustive backtracking with a keyed cyclic starting offset and direction. Objects have a one-cell orthogonal gap.

**Why.** A retry-capped random placer can fail valid profiles nondeterministically. Full search guarantees either a placement or a real grammar infeasibility. Caching removes repeated geometry work while keyed traversal preserves diversity.

**Alternatives rejected.** The first uncached exhaustive draft was correct but too slow under high-volume checks. Unbounded naive random retry has unpredictable runtime; bounded retry introduces false failures.

**Probe.** 4,000 final stress draws produced 4,000 unique valid inputs; shared diversity and full battery pass. Earlier slow/interrupted battery attempts were retained rather than hidden.

**Failure mode.** Adding many more objects or larger shape libraries can make backtracking expensive. New grammar additions need a stress benchmark before acceptance.

## D7 — Keep the Python rule mirror small and independently tested

**Choice.** Implement a pure component-based `rule_mirror`, robust `self_check`, executable rivals, witnesses, and `lesson_identifiable`; test them against a separately written test oracle in `workspace/reference_probe.py`.

**Why.** The mirror supports fast semantic checks, but testing it only against itself would be circular. The independent probe has separate component traversal and rival implementations.

**Alternatives rejected.** Calling Racket for every unit test would be slow and obscure geometry bugs. Trusting only generated labels would not detect mirror drift.

**Probe.** Racket smoke applies 120 generated inputs: 120 fired, 120 distinct outputs, 120/120 mirror parity, zero mutations or crashes. The focused tests compare all four production rivals with independent versions.

**Failure mode.** Python and Racket could share a conceptual misunderstanding; canonical execution parity and exact witness applications reduce but do not eliminate that risk.

## D8 — Scope and stopping decision

The selected generator, its tests/workspace helpers, and its selected authority record were changed. Audit targets were inspected but not edited. Work stopped after final-source task tests, full battery, large census, supported Racket witnesses, and the post-repair solve all passed. Remaining uncertainty is limited to undeclared rival rules and intentionally ungenerated geometric regimes, documented in `REVIEW.md`.
