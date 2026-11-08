# Working notes: fcd1f7b55d3b

## 2026-10-08 review repair

The imported version `2.0.0` advertised nine controls but directly honored only dimensions; unknown keys were accepted, four `texture` values produced intentionally invalid grids, and canonical-profile support was nearly absent outside easy. It also had no `RULE_HASH`, no executable semantic contract, and no lesson schedule protecting against rules that fit all five canonical pairs.

Version `3.0.0` keeps the canonical Racket authority unchanged (`RULE_HASH=d0be8e83eb5b`) and replaces the public surface with five exact, observable axes: `grid_h`, `grid_w`, `n_pairs`, `n_decoys`, and `orientation`. Every legal joint boundary combination is constructive. Unknown, mistyped, or out-of-range controls are rejected.

Lawful pair rectangles are placed in disjoint spatial slots. This removes output overwrite-order ambiguity while preserving the intended exactly-two-color bounding-box operation. A decoy, when present, lies outside every pair rectangle and appears once or three times.

The four-position curriculum is:

1. two backslash pairs, no decoy;
2. three slash pairs plus one decoy;
3. three pairs (four on hard), backslash, plus one decoy;
4. two slash pairs, no decoy.

With four demonstrations and one held-out example, every cyclic start and every query rotation contains evidence against `copy_then_fill`, `all_colors_bbox`, `backslash_only`, and `exactly_two_pairs`. Those competitors and their witnesses are executable in the generator. `counterexamples/canonical_shortcuts.json` retains one lawful final-source input that refutes all four and is replayed by a focused test.

`workspace/reference_probe.py` independently checks canonical answers, all 72 compact boundary override combinations, banded deterministic draws, declared rivals, and cyclic lesson rotations. The final 100-per-band shared census found no ambiguity among the declared rivals in 300 lessons / 1,500 rotations. These are finite checks over the declared rival set, not proof of unique induction against arbitrary programs.

Known domain choice: all pair colors within one generated scene share one orientation, although both orientations occur across the schedule and are exactly controllable. The canonical authority can define outputs for broader inputs; this generator intentionally supplies a clean, non-overlapping teaching manifold.
## Current reviewer considerations

Source SHA-256: `22a8cd0cf6bffcb1e6222a4727065d4bb7b0b672360fec4052042523047bf4a4`.

# Decisions for `fcd1f7b55d3b`

## D1 — Keep the canonical rule unchanged

**Prior state.** The imported generator omitted a rule pin, but the selected canonical rule and all canonical outputs were internally consistent.

**Choice.** Add `RULE_HASH="d0be8e83eb5b"` and retain the Racket authority exactly as supplied. The repair changes only generation, validation, tests, evidence, and teaching structure.

**Alternatives rejected.** Changing the Racket program to resolve generator overlap would alter task semantics without evidence. Instead the generator now avoids overlapping pair rectangles.

**Evidence and limits.** Rule smoke, Racket lint, and authority sync pass in the final battery. This does not claim the canonical rule is uniquely inferable from canonical examples alone.

## D2 — Replace the inherited nine-axis surface with five exact observables

**Prior state.** `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` were advertised but ignored or only aliases. Unknown keys were accepted. Several texture values deliberately returned invalid inputs.

**Choice.** Public axes are now `grid_h`, `grid_w`, `n_pairs`, `n_decoys`, and `orientation`. Every axis is recoverable from pixels, every compact joint boundary combination is constructive, and invalid types/ranges/keys fail immediately.

**Alternatives rejected.** Keeping decorative controls and documenting them as approximate would preserve a false exact-control contract. Declaring invalid textures as ordinary values would keep unlawful data in the production manifold. Palette selection remains internal because color identity is not part of the rule.

**Evidence and limits.** The independent probe enumerates 72 compact boundary combinations; the shared override stage passes and rejects unknown keys. The chosen domain intentionally limits pair count to 2–4 and decoys to 0–1 because only nine nonzero ARC colors exist and four disjoint slots make every combination reliable.

## D3 — Make pair rectangles disjoint

**Prior state.** Independently sampled endpoints could create intersecting bounding boxes. Since the authority paints colors sequentially, the output at overlap cells depends on color iteration order rather than a task-visible selection rule.

**Choice.** Place each pair in one of four non-overlapping row/column slots, with at least a 3×3 bounding rectangle. Decoys are placed outside every pair box.

**Alternatives rejected.** Preserving overlaps and imposing a color-rank priority would introduce a new semantic rule. Rejecting samples after arbitrary placement would be slower and would make exact small-grid controls unreliable.

**Evidence and limits.** All joint boundary tests assert pair-box disjointness. This is a teaching-manifold choice; the canonical authority can still execute broader inputs.

## D4 — Use a deterministic four-role curriculum

**Choice.** Consecutive profiles are canonical backslash, selective slash with decoy, selective backslash with decoy, and canonical slash. Hard selective-backslash scenes use four pairs; other selective scenes use three. `EXAMPLES_NEEDED=4` means a five-pair lesson contains four demonstrations and one query.

**Why.** The five canonical pairs all have two backslash pairs and no ignored colors. They therefore cannot distinguish copying the input before filling, filling all color bboxes, handling only backslash pairs, or requiring exactly two pair colors.

**Alternatives rejected.** Pure random variation could leave complete lessons shortcut-compatible. Increasing lesson length was unnecessary. A fixed canonical-only schedule would retain the defect.

**Evidence and limits.** Every cyclic start and every held-out rotation is tested locally; the shared 100-per-band census found zero ambiguity for the declared rivals. Ordered schedules can still encode other correlations, so the probe records profile counts and source hashes.

## D5 — Preserve canonical profiles in every difficulty band

**Choice.** Two schedule slots use rotating canonical-size anchors, while selective slots use wider band-shaped dimensions.

**Why.** The baseline profile-floor check observed only 2 exact canonical hits out of 60 and none in medium/hard. Training should retain mechanical overlap with the authority examples without collapsing diversity.

**Alternatives rejected.** Using canonical dimensions for every draw would reduce diversity. Using only broad dimensions would leave the canonical support gap.

**Evidence and limits.** Final profile-floor passes in each band; the independent probe reports 12 exact canonical-profile hits per 24 draws in each band. Palette identities vary internally and are not fixed to canonical colors.

## D6 — Declare executable rivals and witnesses

**Choice.** Add `copy_then_fill`, `all_colors_bbox`, `backslash_only`, and `exactly_two_pairs` to `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, with witnesses for decoys, slash orientation, and more than two pairs.

**Why.** Each rival fits all five canonical pairs, so prose-only warnings would not protect future schedule changes.

**Alternatives rejected.** A single hand-written fixture without executable competitors would not participate in the semantic gate. An unbounded program search is too expensive and ill-defined for routine generator checks.

**Evidence and limits.** Canonical-fit tests, the retained single-grid counterexample, semantic gate, local probe, and large census all exercise these rivals. The set is deliberately finite and should grow when a new plausible shortcut is found.

## D7 — Retain a reusable independent probe

**Choice.** `workspace/reference_probe.py` imports the selected source by path, uses an independent oracle, enumerates exact controls, checks deterministic/legal banded draws, and tests cyclic lesson rotations.

**Why.** The shared battery is broad but its lesson sample is intentionally small. Future agents need a fast source-bound reproducer that fails when the generator or contract drifts.

**Alternatives rejected.** Copying generator helper outputs into evidence would create circular verification. Hard-coding only current hashes would detect changes but not explain behavioral regressions.

**Evidence and limits.** Its focused test failed before the tool existed and passes after creation. The final CLI report records source hash `22a8cd...` and status `PASS`. It does not invoke Racket for every draw; Racket parity is established separately by the battery.

## D8 — Version the distribution and contract change as 3.0.0

The public axes, lawful manifold, and deterministic stream all changed materially, while task semantics did not. A major generator version prevents historical seeds from appearing reproducible under a different contract. Exact 2.0.0 streams are intentionally not preserved; the before battery and source hash retain their audit identity.
