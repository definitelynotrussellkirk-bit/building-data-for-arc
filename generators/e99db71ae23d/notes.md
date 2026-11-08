# Working notes: e99db71ae23d

## Review 2026-10-07

### Prior lead and current baseline

I used retained return `local-random-e3cebdab5d43` only as a lead. In particular, its notes suggested checking selected Racket authority synchronization and preserving a branch-complete three-demonstration schedule. I remeasured the pinned source rather than treating those earlier claims as current evidence.

The immutable before battery finished with 11 green stages and one failure: `authority_sync`. Canonical `program_solution` rows agreed exactly, while the two selected active `racket_target.target_code` records held a whitespace-compacted but execution-equivalent form. Their archival `raw_code` fields intentionally differed and were not rewritten.

A separate 100-seed-per-band default-lesson probe found a training-data concentration defect even though labels were correct. One fixed `public_sparse_3` grid occupied the second demonstration in every lesson. Across 400 pair instances per band, the baseline produced only 263 unique easy inputs, 272 medium, and 283 hard; the most repeated exact grid appeared 122, 114, and 100 times respectively.

### Repairs

1. **Selected authority synchronization.** Replaced only the two active `target_code` values with the canonical exact source. Preserved both archival `raw_code` values. The executable behavior and `RULE_HASH = 32f38f665cc3` did not change.
2. **Randomized load-bearing demonstration.** Added `general_edge_overlap_6`, an 11×14 six-piece profile that guarantees both clipping and a cross-color projection collision while remaining randomized. It replaces the fixed `public_sparse_3` demonstration.
3. **Canonical support without demonstration replay.** Removing the fixed public demonstration initially caused the hard-band profile-floor gate to lose its exact canonical anchor. The final hard query choices allocate two of six query choices to `public_dense_16`, restoring a deterministic 16×16 canonical-profile hit while leaving all three demonstrations randomized.
4. **Executable semantic contract.** Promoted the existing four wrong-rule implementations to `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`. Three semantic witnesses now name actual rivals they refute. Clipping and all-four-openings remain honest positive branch witnesses in `BRANCH_WITNESSES` rather than synthetic rival claims.
5. **Portable regressions.** Task tests use `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`, so they work in both the packet and isolated task-test runtime. New tests pin active authority text, the profile floor, the rival contract, randomized edge/collision support, and every cyclic query position.
6. **Reusable distribution probe.** `workspace/lesson_distribution_probe.py` source-binds the generator, hashes exact inputs, reports profile/replay concentration and duplicate lesson windows, and checks every cyclic query position.

### TDD and retained failures

- The portable authority test first failed on both stale selected authorities, then passed after exact synchronization.
- The randomized-demo test first failed because slot 1 replayed the same public grid, then passed with `general_edge_overlap_6`.
- The first complete after battery retained two useful failures: hard-band `profile_floor` lost canonical support, and the semantic gate rejected weak witness declarations. Both received focused failing tests before the final fixes.
- Final selected task stage: 24/24 collected tests passed. The stage collects the 12 selected tests plus a frozen fixture copy, so the raw count is not 24 independent logical test designs.
- Final battery: 12/12 stages green on generator SHA `c811b7c51c933fbdd410606ad97d98fec6d2f85046c88ecca6b5b4b8e04a01dd`.

### Final distribution and lesson checks

The task-local probe used seeds 0–99, four pair positions per lesson, and all three bands:

- easy: 361/400 unique exact inputs, maximum repeat 24;
- medium: 367/400 unique, maximum repeat 15;
- hard: 370/400 unique, maximum repeat 31;
- zero lesson windows with internal duplicate inputs;
- zero failures across 1,200 cyclic query checks.

The source-bound Racket census used its documented SHA-derived seeds and consecutive start residues:

- 300/300 lessons materialized;
- 1,200 labelled pairs;
- 0 production ambiguities or errors;
- 0/1,200 ambiguous query rotations;
- 1,099 unique exact inputs;
- every one of the four declared competitors was refuted in all 100 lessons of each band.

These are finite declared-rival checks, not proof that no other hypothesis can fit the demonstrations. The ordered production curriculum remains three role-specific demonstrations followed by one varied query. Rotation evidence shows the same materialized bundles also refute the declared competitors when each pair is held out once.

### Rejected alternatives

- **Keep the fixed public demonstration:** rejected because it consumed one quarter of every lesson with an identical grid and masked the replay concentration from small diversity samples.
- **Use `general_edge_6`:** rejected for the replacement slot because it teaches clipping but not collision priority.
- **Use only `general_overlap_8`:** rejected because it teaches collision priority but intentionally has no clipping.
- **Make every lesson position fully unconstrained random:** rejected because it would make branch-complete teaching probabilistic.
- **Restore profile floor by returning a fixed public demonstration:** rejected in favor of a weighted varied-query anchor, which preserves canonical support without training-demo replay.
- **Attach rivals to clipping or orientation witnesses:** rejected because those witnesses establish branch coverage but do not by themselves distinguish a concrete wrong transformation.
- **Change the Racket rule:** rejected; canonical outputs and execution parity already supported the existing rule. The defects were authority text synchronization and lesson generation.

### Remaining limitations

The three demonstration roles and their ordering are fixed, so a learner could potentially exploit position correlations not represented by the four declared semantic rivals. The 1,200 rotation checks reduce that concern for the declared competitors but do not prove universal induction. Exact public profiles still repeat by design as canonical anchors; their measured multiplicity is reported rather than treated as zero-replay data.
## Current reviewer considerations

Source SHA-256: `c811b7c51c933fbdd410606ad97d98fec6d2f85046c88ecca6b5b4b8e04a01dd`.

# Decisions: e99db71ae23d

## D1 — Preserve the transformation law; synchronize active authority text

**Original rationale:** The canonical examples, canonical `program_solution` rows, selected Racket execution, and Python mirror agreed on the same law. The before failure was exact text synchronization, not output disagreement.

**Decision:** Copy canonical exact source into the two selected active `racket_target.target_code` fields. Leave `raw_code` untouched and retain `RULE_HASH = 32f38f665cc3`.

**Alternatives considered:**

- Treat whitespace-equivalent source as acceptable: rejected because the selected-authority gate intentionally requires a single exact active authority.
- Rewrite `raw_code` too: rejected because it is archival evidence, not the active executable target.
- Change the canonical Racket program: rejected because no semantic defect was reproduced.

**Failure mode controlled:** Future selected execution cannot silently drift from the canonical source while archival variants remain available for provenance.

## D2 — Replace the fixed public demonstration with a randomized combined witness

**Original rationale:** The earlier schedule correctly reserved three demonstrations for orientation, clipping, and collision priority, but its second slot was a byte-identical public grid for every lesson.

**Decision:** Add `general_edge_overlap_6` and schedule it at demonstration position 1. It combines clipping and cross-color collision in one randomized six-piece scene.

**Alternatives considered:**

- Keep `public_sparse_3`: rejected after the 100-seed probe measured 100–122 exact replays per band.
- Use `general_edge_6`: rejected because it guarantees clipping but explicitly forbids overlap, so it cannot teach collision priority.
- Reuse `general_overlap_8`: rejected because it guarantees collision but intentionally has no clipping.
- Draw every demonstration from the full profile pool: rejected because teaching support would become probabilistic.

**Failure mode controlled:** Correct labels no longer conceal a low-entropy quarter of the lesson stream; the second demonstration remains load-bearing for two branches.

## D3 — Restore hard-band canonical support through the varied query sampler

**Probe:** The first full after battery showed 0 hard-band exact canonical hits in the pinned 20-draw profile-floor sample.

**Decision:** Reorder the six hard query choices so two positions select `public_dense_16`. The three demonstration profiles remain randomized and unchanged.

**Alternatives considered:**

- Put a fixed public grid back into the demonstrations: rejected because it recreates the replay defect.
- Lower or waive the profile floor: rejected because the linked canonical manifold should remain represented.
- Add an entirely new canonical-sized random profile: rejected as unnecessary; exact canonical support, not merely size support, was the gate's purpose.

**Failure mode controlled:** Every band retains canonical-size/palette support while exact public replay is confined to the varied query distribution and reported explicitly.

## D4 — Distinguish semantic rival claims from branch coverage

**Decision:** Export all four existing wrong-rule functions as `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`. Attach named rivals only to three witnesses that actually demonstrate output disagreement. Put edge clipping and all-orientation support in `BRANCH_WITNESSES`.

**Alternatives considered:**

- Declare every witness as a rival refutation: rejected because clipping and orientation frequency do not, by themselves, define a wrong output function.
- Add synthetic rivals solely to satisfy the gate: rejected because they would overstate what the witness proves.
- Leave the existing private `_COMPETING_RULES` undeclared: rejected because the shared census and semantic gate could not retain their predictions.

**Failure mode controlled:** Semantic reports now separate “feature occurred” from “this named plausible rule was falsified.”

## D5 — Keep three ordered demonstrations plus one varied query

**Decision:** Preserve `EXAMPLES_NEEDED = 3` and the ordered demonstration roles:

1. all orientations for both source colors;
2. clipping plus cross-color overlap;
3. unclipped overlap and green-over-yellow precedence;
4. difficulty-weighted varied query.

**Why:** Three demonstrations provide deterministic support for every queried branch without increasing lesson size. The production assembler is ordered, while the repair also verifies every cyclic held-out position because downstream reuse may rotate pairs.

**Limitation:** Fixed roles can create positional correlations. The 1,200 required rotations refute the four declared competitors in every held-out position but do not prove that no position-based or undeclared hypothesis exists.

## D6 — Add a cheap exact-input concentration probe alongside the authoritative census

**Decision:** Build `workspace/lesson_distribution_probe.py` rather than relying only on the small battery sample or the much heavier Racket census.

**Why:** The defect was exact replay concentration, which a label-correct semantic check can miss. The probe runs the actual default sampler, hashes every input, reports max multiplicity and within-window duplicates, and tests all cyclic query positions.

**Alternatives considered:**

- Count only profile names: rejected because a single profile may still generate diverse grids, while a public profile may be exactly fixed.
- Count only unique complete lessons: rejected because one fixed pair can be hidden inside otherwise unique windows.
- Replace the Racket census: rejected because the Python mirror is not authority and cannot retain authoritative rival predictions.

**Domain limit:** Exact grid hashes do not collapse rotations, translations, or other semantic equivalences. The report therefore measures literal replay, not all forms of near-duplication.

## D7 — Test portability rather than packet-relative depth assumptions

**Decision:** Resolve roots and canonical data through `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.

**Why:** The task-test stage copies selected tests into an isolated runtime. Fixed `Path.parents[n]` guesses initially failed before reaching the intended authority assertion.

**Failure mode controlled:** The same regression tests execute in the source packet, the isolated stage, and the final fresh-copy handoff check.

## Review 2026-10-24 — native parametric direction policy

### Decision and implementation

Preserved production `generator.py` at SHA-256 `c811b7c51c933fbdd410606ad97d98fec6d2f85046c88ecca6b5b4b8e04a01dd` and the canonical default program at SHA-256 `cf1fede330cf21f285c5f013480a0d0bf966010286fe80e887e61f6fda55ad64`. Added a native adapter whose episode-fixed parameter is `direction_policy`:

- `gray_toward_red_away` is the canonical Racket program byte-for-byte;
- `gray_away_red_toward` preserves the grammar, connected-component discovery, missing-corner intermediate, fill colors, clipping, and green-last collision precedence while swapping which source color moves toward its opening.

The sampler is setting-neutral: both settings receive identical inputs for the same seed/counts. It supports 2–6 demonstrations and exactly four distinct queries. Constructed scenes deliberately exercise both policy-specific collision motifs; the 30×30 query contains 16 pieces, all four orientations for both colors, clipping under both settings, full row/column span, and all four quadrants.

### Sequential dependency and shortcut control

A discovers every L-tromino and its missing 2×2 corner. The load-bearing intermediate is the ordered set of per-piece opening vectors. B cannot select projection sites until it has those input-dependent vectors; it then keeps or negates each vector according to color and the hidden setting. The protected-Racket witness uses a qualified six-piece query with four distinct opening directions and shows that replacing them all with fixed southeast changes the final grid.

Visible demonstrations were checked against the other declared setting plus six plausible rivals: both colors toward, both away, reversed collision precedence under each setting, and fixed-southeast opening under each setting. Only the selected setting survives each retained 2-, 3-, and 6-demonstration audit job. This is a finite authored rival set, not a proof of universal identifiability.

### Retained verification

- Original baseline task tests: 12 passed before the parametric addition.
- Final changed-target stage: 20/20 passed (12 existing plus 8 focused parametric tests).
- Protected-Racket audit: 6 jobs, 368 evaluations, both settings, seeds 0/17/41, demo counts 2/3/6, and six plausible rivals.
- Native qualification: 4/4 jobs passed for both settings at seeds 0 and 17 with 3 demonstrations and 4 queries.
- Public projection checker: two hash-named challenges passed with masked query outputs and no private fields.
- Sampler stress: 300 episodes and 2,300 visible pairs across 50 seeds, both settings, and demo counts 2/3/6; deterministic regeneration and all lesson certificates passed.
- Protected sequential replay: 1/1 wrong-intermediate case changed the final output; 2 Racket evaluations.

### Remaining limits and next action

Owner native acceptance has not yet run, and `training_admitted` remains false. The next useful action is to integrate the returned source delta and run the owner admission path against the exact qualification and witness bytes. Optional peer reviews `6145142974ff` and `6d19cd1698b1` were not run because MAIN quality and native evidence took priority.
