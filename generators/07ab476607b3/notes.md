# Working notes: 07ab476607b3

## Review outcome

Version `4.0.0` replaces retry-dependent sampling with construction-by-invariant. The final battery is 12/12 green. Canonical Racket behavior was preserved; the selected bank text was synchronized exactly to canonical source after execution parity had already passed.

## Public generation contract

- `grid_h`: `10..13`
- `grid_w`: `11..15`
- `a_size`: `4..7`
- `texture`: `plain | disjoint_b | clip | empty_diff`
- difficulty: `easy | medium | hard`
- unknown axes and invalid values: rejected

Defaults cycle the four canonical profiles in every band. A-size schedules vary by band. The first three sample indices cycle `plain`, `disjoint_b`, and `clip`, so a short lesson cannot omit a decisive semantic branch by chance.

## Semantic intent

- `plain`: source objects are physically separated, but normalized A and B have a nonempty proper overlap. This defeats positional subtraction.
- `disjoint_b`: normalized objects do not overlap, so every A cell survives. This defeats assuming that one overlap must always be removed.
- `clip`: a nonempty residue is only partly in bounds at the anchor. This defeats moving or shrinking the stamp to fit.
- `empty_diff`: normalized A equals B and output is blank.
- `no_anchor`: constructible only as a malformed diagnostic; `self_check` must reject it.

Executable witnesses, rivals, and `lesson_identifiable` encode these claims. `analyze` is the single shared interpretation used by validation, override observation, witnesses, and the Python rule mirror.

## Construction

Compact fixed polyominoes up to size seven are enumerated and cached. Shape pairs are filtered by the requested normalized relation before placement. Red and yellow objects are placed with a one-cell visual gap. Anchor candidates are then filtered for full fit or partial clipping as required. No semantic branch depends on an eventually-successful random retry.

## Evidence

- `tests/test_generator_07ab476607b3.py`: six focused regressions.
- `workspace/semantic_probe.py`: independent semantic census for future reviewers.
- `workspace/semantic_probe_report.json`: passing 20-sample-per-band report.
- `workspace/shortcut_counterexample.json`: exact positional-subtraction counterexample checked against canonical Racket.
- packet-level `checks/before` and `checks/after`: required battery evidence.

## Known limits

The shape library is bounded to sizes `4..7` and bounding boxes at most `4x4`. It is designed to teach coordinate normalization, subtraction, anchoring, and clipping rather than approximate every possible connected-shape distribution. Output uniqueness is 91% in the final diversity probe because small residue and clipped-output structures can recur; input uniqueness remains 100%.

Imported associated notes, if any, remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `a109f4485d7230a4a282be3379f707d3ac67e728269264d409120201edf2acc4`.

# Decision ledger for 07ab476607b3

This ledger records each consequential input choice, the inherited rationale where it could be recovered, alternatives considered, the probe used, and known failure modes.

## D1. Preserve the canonical Racket rule

**Inherited state and rationale:** The selected rule hash was already `11cea0a09738`. The canonical and bank Racket texts differed, but the baseline authority probe found sampled execution parity.

**Decision:** Keep canonical behavior unchanged and copy the canonical source text into the selected bank authority. Pin `RULE_HASH = "11cea0a09738"` in the generator.

**Alternatives considered:** Rewrite or beautify the Racket implementation; keep two behavior-equivalent source variants. Both add provenance risk without improving the task.

**Probe:** Canonical Python mirror checks, 120-draw rule smoke, Racket lint, and authority synchronization.

**Failure modes and limits:** Sampled parity cannot prove arbitrary-program equivalence, which is why the active text was made exact rather than merely accepted as equivalent.

## D2. Grid dimensions

**Inherited state and rationale:** The old declared `grid_h` range was written as `8-16`, which the checker could not parse. Default sampling produced only 5/60 canonical-size examples and none in hard mode. The original reason for that broad default is unknown.

**Decision:** Declare exact ranges `grid_h=10..13` and `grid_w=11..15`. In every band, default indices cycle canonical profiles `(10,11)`, `(10,12)`, `(11,11)`, `(11,12)`; explicit overrides still reach all boundaries.

**Alternatives considered:** Retain `8..16`; sample all dimensions uniformly; restrict all outputs to canonical sizes. Uniform broad sampling recreates profile drift, while canonical-only dimensions unnecessarily remove useful override coverage.

**Probe:** 11,520-draw override matrix, 60-draw profile floor, and the task-local semantic probe.

**Failure modes and limits:** Defaults are intentionally not uniform over the full declared dimension ranges. Consumers seeking larger grids must request them explicitly.

## D3. A-object size

**Inherited state and rationale:** The prior generator varied shapes but did not make the advertised size choice independently testable. The exact original size curriculum rationale is unknown.

**Decision:** Expose `a_size=4..7`. Use deterministic band schedules: easy `(4,5)`, medium `(4,5,6)`, hard `(5,6,7)`. Explicit overrides take precedence in every band.

**Alternatives considered:** Uniform size sampling; one fixed canonical tetromino; include sizes below four or above seven. A fixed shape invites memorization. Larger exhaustive libraries increase cost sharply without being needed to teach the rule.

**Probe:** Boundary override tests in all bands, semantic probe, diversity stage, and timing in rule smoke.

**Failure modes and limits:** Difficulty is represented mainly by shape size, not by a proven human difficulty model. Size seven is a practical construction boundary, not a semantic boundary of the task.

## D4. Texture as a semantic branch, not decoration

**Inherited state and rationale:** The previous labels included `plain`, `disjoint_b`, `clip`, `empty_diff`, and `no_anchor`, but their effects were not all guaranteed and `no_anchor` overlapped the ordinary valid domain. The labels appeared intended to cover edge cases.

**Decision:** Lawful `texture` values are exactly:

- `plain`: nonempty proper normalized overlap and at least two surviving A cells;
- `disjoint_b`: zero normalized overlap;
- `clip`: nonempty residue with some, but not all, stamped cells clipped;
- `empty_diff`: normalized A equals B.

Ordinary defaults cycle only the first three. `empty_diff` is an exact boundary override.

**Alternatives considered:** Treat texture as a weak bias; use rejection sampling; expose separate Boolean flags. Weak biases make metadata dishonest, rejection can silently fall back, and independent flags create incompatible combinations.

**Probe:** Branch-specific regression tests, `observe_overrides`, 600-draw semantic gate, and semantic-probe witness counts.

**Failure modes and limits:** The four labels cover the highest-value rule boundaries, not every possible relation between A, B, anchor, and canvas.

## D5. Construct shapes exhaustively

**Inherited state and rationale:** Prior random construction produced variety, but no contract proved the requested normalized relation. The original randomization rationale was likely diversity, but it was not documented.

**Decision:** Enumerate fixed 4-connected polyominoes up to size seven, normalize them, retain compact shapes no larger than `4x4`, and prefilter pairs by the requested normalized relation.

**Alternatives considered:** Random walks with retries; hand-written shape templates; exhaustive free-polyomino symmetry reduction. Random retries make semantic guarantees probabilistic. Hand templates are shortcut-prone. Free-polyomino reduction would remove orientation variety that is useful here.

**Probe:** Focused semantic tests, 600 strict samples, 300-pair diversity probe, and 120-call timing probe.

**Failure modes and limits:** The library omits larger or long-thin shapes. Cached exhaustive enumeration is practical only because the maximum size is seven.

## D6. Separate physical placement from normalized comparison

**Inherited state and rationale:** The rule compares normalized shapes, but a model can incorrectly subtract at their physical coordinates. The old generator did not guarantee a decisive counterexample to this shortcut.

**Decision:** Place red and yellow objects with a one-cell visual gap while allowing their normalized forms to overlap. In `plain`, the physical cell sets are disjoint and normalized overlap is mandatory.

**Alternatives considered:** Permit touching or overlapping source objects; place both at the same origin. Those alternatives blur object extraction or make positional subtraction accidentally correct.

**Probe:** The exact seed-2718 shortcut counterexample, the `normalized_partial_overlap` witness, and 60/60 checks against the `positional_subtraction` rival.

**Failure modes and limits:** The visual gap makes segmentation easy. The curriculum tests the coordinate-frame distinction rather than hard object segmentation.

## D7. Anchor and clipping policy

**Inherited state and rationale:** Canonical behavior clips out-of-bounds residue cells. The prior `clip` label did not guarantee a partially clipped, still-informative result.

**Decision:** For non-clip samples, choose an unoccupied anchor where the entire residue fits. For `clip`, choose an unoccupied lower/right-edge anchor where at least one residue cell remains in bounds and at least one is clipped. Avoid `(0,0)` so the maroon anchor cannot be mistaken for background in naive bounding logic.

**Alternatives considered:** Allow completely off-grid stamps; relocate the stamp to fit; wrap around. Only partial clipping directly tests the actual rule while preserving visible evidence.

**Probe:** `clipped_stamp` witness, `fit_stamp_inside` rival, branch regression test, and semantic gate.

**Failure modes and limits:** The generator emphasizes lower/right clipping because the anchor is a top-left offset. It does not manufacture negative-coordinate clipping, which the rule’s representation cannot express.

## D8. Negative `no_anchor` fixture

**Inherited state and rationale:** `no_anchor` was present as both an ordinary texture and a degenerate texture. The selected Racket rule requires an anchor and fails on this malformed input.

**Decision:** Keep `DEGENERATE_TEXTURES = ("no_anchor",)` for diagnostics, but remove it from the lawful axis domain. Build it through a separate negative-fixture path and require `self_check` to reject it.

**Alternatives considered:** Delete the fixture; make it lawful by changing the Racket rule; include it in ordinary sampling. Deletion loses a useful robustness probe. Changing the rule would alter authority. Ordinary sampling would generate examples with no defined answer.

**Probe:** Dedicated regression test and defect-lint stage.

**Failure modes and limits:** Calling `generate(..., texture="no_anchor")` is intentionally a diagnostic escape hatch outside `AXES['texture'].valid`.

## D9. Deterministic scheduling plus keyed randomness

**Inherited state and rationale:** The API is seed/index based, but the baseline did not guarantee that semantically important branches appeared in short lessons.

**Decision:** Use `sample_index` to schedule canonical profiles, A-size bands, and the three helpful textures. Use the generator context’s keyed RNG for selecting concrete shapes and legal placements. Never mutate Python’s module-global RNG.

**Alternatives considered:** Fully random branch choice; a static finite bank. Fully random choice can omit a lesson. A static bank is deterministic but easy to memorize and has poor variety.

**Probe:** Fresh-return/RNG-purity test, repeated-call equality, per-band schedule test, and 100% unique input diversity result.

**Failure modes and limits:** The first three sample indices are deliberately predictable at the semantic level. Concrete geometry remains seed-dependent.

## D10. Executable semantic contract

**Inherited state and rationale:** Baseline semantic gate reported `NO_CONTRACT`.

**Decision:** Define three witnesses and three rival implementations:

- `normalized_partial_overlap` vs. `positional_subtraction`;
- `normalized_disjoint` vs. `assume_one_overlap`;
- `clipped_stamp` vs. `fit_stamp_inside`.

Require the first three demonstrations to cover all witnesses and reject all linked rivals through `lesson_identifiable`.

**Alternatives considered:** Rely on prose invariants; only compare outputs to the authoritative rule. Output correctness alone does not establish that a lesson identifies the intended abstraction.

**Probe:** Repository semantic gate, focused lesson test, and `workspace/semantic_probe.py`.

**Failure modes and limits:** The named rivals are the strongest obvious shortcuts, not an exhaustive hypothesis space. A novel rival could still fit the generated curriculum.

## D11. Analyzer and observability

**Inherited state and rationale:** The baseline `self_check` accepted generated examples but did not expose exact axes or all structural reasons for acceptance.

**Decision:** Add a total `analyze` function that returns extracted objects, normalized forms, overlap, residue, anchor, clipping, output, inferred texture, and errors. Build `self_check`, `strict_canonical_like`, `observe_overrides`, witnesses, and the mirror on that shared interpretation.

**Alternatives considered:** Duplicate extraction logic in every hook; inspect private generation metadata. Duplicated logic drifts, while hidden metadata proves only what was requested, not what the grid contains.

**Probe:** Canonical pairs, destructive mutations, exact override recovery, analyzer/mirror agreement in the semantic probe.

**Failure modes and limits:** The analyzer assumes the intended palette and one connected object per source color; this is appropriate for the canonical grammar but not a general ARC parser.
