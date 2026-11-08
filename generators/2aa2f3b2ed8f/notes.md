# Current notes: 2aa2f3b2ed8f

## Current proposed parametric family

`workspace/parametric/` now contains a native adapter for episode-fixed
`mover=body|target`: consume the tail, then move either its rectangular body
(canonical) or the target (proposed alternative) across the inferred gap. The
body setting uses the exact canonical program text; production source and
canonical authorities are unchanged. Shared inputs across settings prevent
private-setting-dependent geometry. Two constructive demos reverse object-size
roles, direction, and color rank; ordinary use is three demos and four distinct queries.
Counts are independently supported at 2–6 demos and 1–4 queries with stable query
prefixes. The 2×4 to 30×30 query profiles include a dense, boundary-contacting
437-cell large scene, longer tails, and all four directions.

Use the task-local exporter for protected-Racket-checked examples and single-query
public turns; query labels/settings/programs and ordered reveal IDs stay private.
The README gives exact commands and scope. Focused source-bound tests and the
native evidence manifest retain actual results. An independent Racket-backed
review reproduced a lower-color shortcut at seed 17 in the initial two-demo
sampler; reversing palette rank in demo 0/1 fixes that teaching hole without
increasing demo count. The counterexample and failing-then-passing regression
remain in `checks/parametric-adversarial/` and `checks/parametric/`. Parameter acceptance and training
admission remain separate owner decisions. Next action: review and qualify these
exact prototype bytes through the existing native promotion workflow; the prior
canonical audit dispositions are unchanged.

## Intended rule

The input contains two differently colored non-background objects on color 0. One is a solid target rectangle. The other is a solid rectangular body with a straight, one-cell-thick tail that points toward the target and exactly bridges the positive gap. The transformation consumes the complete tail and translates only the body along that direction until the body is flush with the target.

The canonical Racket rule remains the authority and is pinned by `RULE_HASH = "f1cfb51e6ad7"`. This review did not alter its logic. It synchronized the training and augmented `racket_target.raw_code` / `target_code` copies to the exact canonical program text so authority checks no longer compare divergent duplicates.

## Reversed baseline decisions

The imported v2.0.1 sampler generated only a one-cell tail and its validator required exactly one tail cell. All eight usable canonical inputs have tails of length 3–5, so the validator rejected 8/8 canonical inputs even though default samples passed. The current v3.0.0 grammar accepts and generates the canonical gap-bridging tail.

The prior public schema advertised grid size, palette aliases, singleton color-count axes, booleans that were not observable, and degenerate textures. These controls were not a falsifiable description of the returned grid. The current public axes are only four constructive, recoverable quantities: `orientation`, `body_shape`, `target_shape`, and `tail_length`. Unknown, retired, mistyped, and out-of-domain controls fail loudly.

## Distribution decisions

Four slots of a private five-slot schedule reproduce the four distinct canonical canvas/geometry profiles. The fifth slot broadens padding and independently varies the four constructive axes. Broad slots cycle directions so short consecutive lesson windows do not rely on luck for directional coverage.

Advertised body shapes are restricted so the intended body remains the unique largest filled rectangle for every advertised orientation and tail length. Canonical 3x3 bodies remain validator-valid, but are not crossed with the longest generated tails because that can tie the reference program's largest-rectangle selection. Target shapes, colors, placement offsets, and difficulty-dependent padding still vary, while all grids remain within 30x30.

## Validation and teaching contract

`self_check` now validates rectangular ARC grids, exactly two connected colored objects, one target rectangle, one body-plus-tail creature, a straight complete bridge, positive body-to-target movement, and an unambiguous body. `observe_overrides` reconstructs every public axis from the grid.

The named near-miss rule `slide_one_cell` erases the tail but moves the body only one cell. `long_tail_requires_full_slide` is the executable witness. Three demonstrations are used per lesson. The final semantic smoke check found 12/12 ordered lessons identifiable against the declared rival and 0/48 ambiguous diagnostic query rotations. A larger production-sampler census found 0/300 ambiguous lessons and 0/1,200 ambiguous rotations, covering 1,191 unique inputs.

## Verification and limits

Final generator SHA-256: `43ae2ae11fb6b9bab871204e652aeb4b9f5a54b9ba10b51e579c01045209e09e`. The complete final battery is 12/12 green; the isolated task suite is 36/36 passing; a 300-lesson census has no declared-rival ambiguity. Evidence is under `checks/after-final/`, `checks/task-tests-final/`, and `checks/lesson-census-final.json`.

These finite checks establish compatibility with the canonical examples and the tested rival family, not unique induction against every imaginable program or every seed. The catalog's approval/training-safety state is derived elsewhere and was not edited by this review. The post-repair visible-only solve used the final generator bytes, matched all three visible demonstrations in one revision, declared earlier rule exposure, and did not consult the reference during that solve.
## Current reviewer considerations

Source SHA-256: `43ae2ae11fb6b9bab871204e652aeb4b9f5a54b9ba10b51e579c01045209e09e`.

# Decisions for 2aa2f3b2ed8f

## D1 — Treat the canonical gap-bridging tail as the grammar

**Prior choice:** the imported generator created exactly one tail cell and `self_check` required exactly one. The rationale was not recorded; it appears to have been a simplifying synthetic approximation.

**Alternatives considered:** keep the one-cell sampler and merely loosen validation; permit arbitrary tail lengths unrelated to the target; or make the tail exactly occupy the positive body-to-target gap.

**Decision:** generate and require a straight tail that exactly bridges the gap. The entire creature is erased, then only the rectangular body is translated by that gap until flush with the target.

**Probe/evidence:** the baseline rejected every one of 8 canonical inputs with reported tail counts 3, 4, or 5 (`checks/before/..._selfcheck.log`). The replacement accepts all 8 and its independent test oracle reproduces every canonical label (`checks/task-tests-final/`).

**Failure modes/limits:** a malformed creature can contain several plausible rectangles. The validator therefore requires the intended body to be unambiguous under the same first-maximum geometry used by the reference program.

## D2 — Advertise only exact, observable constructive axes

**Prior choice:** expose grid dimensions, palette aliases, singleton color counts, booleans, texture aliases, and degenerate modes. Some did not affect output or could not be recovered from the returned grid.

**Alternatives considered:** keep all names and add metadata-only observability; mark many pairwise incompatibilities; or narrow the schema to the semantic controls that construction can honor for every band.

**Decision:** expose exactly `orientation`, `body_shape`, `target_shape`, and `tail_length`. Implement `observe_overrides` from pixels. Reject all unknown, retired, mistyped, and out-of-range inputs, and validate `sample_index` and `difficulty` strictly.

**Probe/evidence:** baseline lint reported singleton and unobservable axes. The final override stage is green, and task tests exercise one exact cross-axis request in all four difficulty settings plus invalid-key/type/domain cases.

**Failure modes/limits:** colors, offsets, padding, and overall dimensions still vary but are intentionally not exact public controls. Adding them later should require a pixel-level observer and full difficulty-band matrix first.

## D3 — Restrict generated body shapes to avoid reference ties

**Prior choice:** small 2x2/2x3/3x2 bodies were sampled independently of tail geometry.

**Alternatives considered:** change the Racket body-selection rule; accept ties and mirror its enumeration accident; or choose a domain where the body is always the unique largest rectangle.

**Decision:** keep the authority unchanged and advertise body shapes whose area/geometry dominate every legal straight tail line for all advertised tail lengths/orientations. Canonical 3x3 inputs remain accepted, but 3x3 is not generated across the full long-tail domain.

**Probe/evidence:** a test-first cross-product exposed cases where a long tail line could tie or beat the intended small body. `BODY_SHAPES` now excludes that ambiguity; final grammar, defect-lint, and authority stages are green.

**Failure modes/limits:** this is a deliberate distribution restriction. It preserves the canonical 3x3 validator domain but does not promise random generation of every authority-accepted morphology.

## D4 — Mix canonical-profile anchors with controlled breadth

**Prior choice:** unconstrained random dimensions/layouts did not reproduce the canonical tail/body/target profiles.

**Alternatives considered:** copy only canonical templates; use fully independent random axes; or interleave canonical anchors with broader constructive examples.

**Decision:** use a private five-slot schedule: four slots reproduce the four distinct canonical canvas/geometry profiles, and one broad slot varies padding and axes. Broad slots cycle orientation across successive schedule cycles.

**Probe/evidence:** the profile-floor stage is green in every band. Task tests check 24 consecutive samples per band for a canonical profile and all four directions. The 300-lesson census observed 1,191 unique inputs.

**Failure modes/limits:** the generic census did not enumerate the private period across all seeds. The focused consecutive-window test supplies local schedule coverage, while the random census supplies wider sampled evidence.

## D5 — Add an executable one-step teaching rival

**Prior choice:** no task-level semantic witness/rival contract existed.

**Alternatives considered:** rely only on structural validity; add many speculative rivals; or capture the closest mechanism error: erase the tail but move the body one cell.

**Decision:** declare `slide_one_cell` as the semantic rival and `long_tail_requires_full_slide` as its witness. Retain three demonstrations per lesson.

**Probe/evidence:** semantic smoke: 586/600 witness hits, 12/12 ordered lessons identifiable, 0/48 ambiguous diagnostic rotations. Larger census: 300/300 production lessons and 1,200/1,200 rotations distinguish the declared rival.

**Failure modes/limits:** one rival is not a completeness proof. Future audits should add genuinely canonical-compatible alternatives when found rather than inflating a decorative list.

## D6 — Preserve authority logic; synchronize duplicated source text

**Prior choice:** canonical, training target, and augmented target fields contained semantically related but textually different Racket programs.

**Alternatives considered:** leave duplicates divergent; rewrite the canonical program; or copy the exact canonical program into all selected task target fields.

**Decision:** synchronize `racket_target.raw_code` and `target_code` in the selected training and augmented records to the canonical source. Do not change the canonical rule or normalized `RULE_HASH`.

**Probe/evidence:** the first authority-sync check failed on divergence; the corrected rerun and the complete final battery pass. Rule smoke also passes on 120 generated inputs.

**Failure modes/limits:** this edits shared selected-task solution records, so the patch must be replayed together with the generator. It is source synchronization, not a new transformation.

## D7 — Keep failed and interrupted evidence distinct from final passes

The before battery recorded two real failures, then stalled with a running aggregate. Intermediate lint, authority, defect, and semantic attempts also exposed issues later corrected. They remain under distinct paths rather than being overwritten. Only `checks/after-final/` is cited as the complete 12-stage final battery, and only `checks/task-tests-final/` as the final isolated test pack.
## D8 — Replay the emitted source patch in a clean packet

**Risk:** verification in the working tree could pass while the return archive omits a file, depends on untracked state, or contains a patch that cannot be applied by the maintainer.

**Decision:** package a draft, extract its exact `patches/source.patch`, apply it to a fresh extraction of the issued packet with `git apply --check`, and rerun the focused portable test suite there. Retain a small parameterized helper (`checks/fresh-replay/replay_source_patch.sh`) so future reviewers can repeat the gate with any packet/return pair.

**Probe/evidence:** the first helper invocation caught a shell typo before it could be relied on; that failed transcript is retained. The corrected helper applied all five patch paths, reproduced generator SHA-256 `43ae2ae11fb6b9bab871204e652aeb4b9f5a54b9ba10b51e579c01045209e09e`, and reported 36 passed.

**Failure modes/limits:** the helper assumes `unzip`, `git`, and a Python environment with the packet's test dependencies. It validates the source patch and focused tests, while the full 12-stage battery remains bound to the original final working snapshot.

## Maintainer selection

Keep the original archived `racket_target.raw_code` in both the training and augmented authority records. The return synchronized those fields too; only `target_code` is selected for execution and synchronization. The original archival programs are preserved while the repaired generator and selected canonical target remain accepted with reviewer-reported evidence.
