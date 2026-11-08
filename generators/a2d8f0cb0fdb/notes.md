# Working notes: a2d8f0cb0fdb

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `f75a61911b0d15581cb3b745412e9f989521edcaf6149a7587649bf349191d07`.

# Decisions for `a2d8f0cb0fdb`

All final behavioral choices below are bound to generator SHA-256 `f75a61911b0d15581cb3b745412e9f989521edcaf6149a7587649bf349191d07`. The selected Racket authority was not edited.

## D1 — Preserve and pin the selected authority

**Choice.** Keep the canonical Racket program unchanged and declare `RULE_HASH = "b1048663f6a3"`.

**Original rationale.** The baseline omitted the required pin. No retained decision record explained that omission.

**Probe.** The baseline lint identified the exact current hash; canonical replay and rule smoke then compared the Python mirror and generated inputs against the selected Racket execution.

**Alternatives rejected.** Changing the Racket rule to match the baseline's “exactly one legend marker” description would have narrowed the authority to a canonical coincidence and erased the meaningful first-header ambiguity.

**Failure mode/limit.** A future authority change must deliberately update the pin and rerun parity, canonical replay, solve provenance, and all semantic evidence.

## D2 — Replace nine misleading axes with one exact semantic axis

**Choice.** Remove `grid_h`, `grid_w`, `palette_kind`, `n_ones`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` from the advertised exact-control surface. Expose only `scene_profile`.

**Original rationale.** The baseline comments called the old fields “combinatorial axes,” but no evidence showed they were independent or exact. Several were constants, aliases, or had declared ranges that conflicted with per-band generation.

**Probe.** The before override gate found 16,372 categorized findings in its summary, including requested dimensions not realized, degenerate textures rejected by `self_check`, and an accepted unknown-key policy. The final override gate passes.

**Alternatives rejected.** I did not retain cosmetic controls merely to satisfy metadata. Dimensions and counts remain deterministic latent choices because they are useful diversity, but they are not promised as exact public overrides.

**Failure mode/limit.** Consumers that relied on undocumented old override behavior must use `scene_profile` or default scheduling instead.

## D3 — Use four observable scene profiles

**Choice.** Define profiles by exact counts `(nonzero header cells, body distractors)`:

- `canonical_anchor = (1, 0)`
- `header_choice = (3, 0)`
- `body_filter = (1, 2)`
- `combined = (3, 2)`

**Original rationale.** Unknown; the baseline supported only `(1, 0)` and supplied no lesson-level identifiability argument.

**Probe.** Focused tests request each override and check `observe_overrides`. The large census recorded all expected profile counts with no observation errors.

**Alternatives rejected.** Two header markers would also distinguish first from last, but three make “first” versus “last/only” visually less accidental while remaining compact. One body distractor would suffice logically, but two reduce the chance that a solver dismisses it as noise.

**Failure mode/limit.** Count-coded profiles are intentionally discrete. They do not claim that all legal header or distractor cardinalities are sampled.

## D4 — Use a five-slot schedule with two anchors

**Choice.** Schedule `anchor, header, body, anchor, combined`; use three sequential demonstrations per lesson.

**Original rationale.** The baseline had no semantic schedule. The assignment required lesson evidence but supplied no required sequence.

**Probe.** I enumerated all five cyclic starts. Every length-three window contains both distinctions. The task-local probe tests 100 lessons per band with each start exactly 20 times.

**Rejected first attempt.** A four-profile one-each cycle provided semantic coverage but did not meet the canonical-profile floor reliably in every band. The retained failure is in `checks/targeted-profile-1/`.

**Failure mode/limit.** A different lesson assembler that does not take sequential triples must separately verify witness coverage; individual profile frequency is not enough.

## D5 — Preserve canonical anchors in every difficulty band

**Choice.** Let `canonical_anchor` draw only 4x5 or 4x6 grids in all three bands, matching the canonical shape/palette envelope. Let the other profiles increase size with difficulty up to 9x12.

**Original rationale.** The baseline sampled near the canonical dimensions, apparently to maintain visual similarity, but no explicit rationale was retained.

**Probe.** Final profile-floor results are easy 6/20, medium 7/20, hard 4/20 exact hits, with no zero-support band.

**Alternatives rejected.** Making hard examples uniformly large caused zero hard-band canonical support. Making every example canonical-sized would pass the profile check but provide less structural diversity.

**Failure mode/limit.** Difficulty changes scale and signal count, not the underlying operation; it is not a calibrated cognitive-difficulty measure.

## D6 — Select target colors from 2–9 and reserve blue 1 as signal

**Choice.** The first nonzero header color is sampled from 2–9. Body signal cells are literal value 1. Distractor colors are sampled from 2–9 excluding all header colors.

**Original rationale.** The baseline already treated 1 as signal and a non-{0,1} color as the legend; this matches the canonical demonstrations. It did not explain why every generated body nonzero had to be 1.

**Probe.** Canonical replay, Racket parity, and the body-distractor witness verify the distinction. A defect-lint failure additionally showed that a first legend value of 1 is a misleading minimal impostor; `_analysis` now rejects it.

**Alternatives rejected.** Allowing target 1 collapses signal and legend roles. Reusing a header color as a body distractor creates an extra copy-color interpretation unrelated to the selected rule.

**Failure mode/limit.** The generated curriculum does not teach what happens when later header markers equal body distractors; the authority still handles such inputs by its literal first-header/blue-only semantics.

## D7 — Use banded signal counts and sparse sampling

**Choice.** Sample blue cells without replacement: easy 3–5, medium 4–8, hard 6–12, capped by capacity after reserving distractor cells.

**Original rationale.** The baseline used sparse 3–8 blue cells. Its exact historical rationale is unknown; sparsity appears intended to make the recoloring mask visually legible.

**Probe.** Distribution, diversity, grammar, strict semantic, and 1,200-input lesson checks all pass with no duplicates in the large census.

**Alternatives rejected.** Dense masks can obscure whether distractors are independently cleared. Very small masks produce near-trivial examples and increase accidental symmetries.

**Failure mode/limit.** Density is not an exact axis and the generator does not explore saturated bodies.

## D8 — Separate authority grammar from teaching grammar

**Choice.** `self_check` accepts rectangular ARC grids with at least one nonzero header cell whose first color is not 1 and at least one body 1. `teaching_check` additionally enforces the generated size/profile/count envelope.

**Original rationale.** The baseline's single validator encoded its one-marker distribution as though it were the rule's full legal domain.

**Probe.** Canonical inputs pass `self_check`; generated examples pass both; malformed inputs and minimal impostors are covered by focused tests and defect lint.

**Alternatives rejected.** A single strict validator would wrongly reject legal multi-header/distractor witnesses. A permissive validator with no teaching check would make profile claims unfalsifiable.

**Failure mode/limit.** `self_check` is a practical authority-level grammar, not a proof that every accepted 30x30 grid is pedagogically useful.

## D9 — Declare executable rivals and witnesses

**Choice.** Declare:

- `last_header_nonzero`
- `recolor_all_nonzero_body`
- `preserve_body_distractors`

Attach `multiple_header_markers` and `body_distractors` witnesses, expose the same functions as `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, and require `lesson_identifiable`.

**Original rationale.** None existed in version 1.1.1; the semantic gate was advisory because no contract was present.

**Probe.** Each rival was first verified to fit all 3/3 canonical pairs. The 600-draw semantic gate confirms witness disagreements; the 300-lesson census confirms every lesson's demonstrations refute all three rivals.

**Alternatives rejected.** Generic geometric rivals such as rotation and reflection do not fit the canonical pairs, so they are weaker than the task-specific ambiguities and were not used as the primary teaching contract.

**Failure mode/limit.** These are the strongest simple canonical-fitting rivals found, not an exhaustive program space.

## D10 — Add a source-bound, production-shaped lesson probe

**Choice.** Add `workspace/lesson_probe.py`, using `runner.run_one`, a persistent Racket bridge, source hashes, deterministic seed derivation, three demos plus one query, and every cyclic schedule start.

**Original rationale.** The assignment explicitly required at least 100 lessons per band when plausible rivals fit canonical pairs. No task-local tool existed.

**Probe.** `checks/lesson-probe/a2d8f0cb0fdb_lesson_probe.json` records 300/300 materialized lessons, 1,200 unique inputs, zero execution/validation/hook failures, and 100/100 rival refutation per band.

**Alternatives rejected.** Sampling isolated grids would measure witness frequency but not whether complete lessons teach the distinction. Reimplementing the sampler or hard-coding rival names would risk testing a different distribution or stale contract.

**Failure mode/limit.** The census is deterministic and finite. It records replay formulas and source hashes but cannot establish universal identifiability.

## Parametric reviewer build — largest-component header relay (2026-10-25)

**Choice.** Preserve `first_header_all` as the byte-exact canonical default and add `largest_component_indexed_header`. The variant segments the blue body, retains the unique largest component and its size `k`, uses `(k - 1) mod 3` to select one of three visible header colors, and paints only that retained component.

**Why this is a real sequential dependency.** Component segmentation and ranking determine both the later output mask and the header index; the color-selection/render stage cannot be computed from a fixed location or scalar setting alone. A protected-Racket counterfactual selecting the smallest component instead changes eight final cells on an exact qualified query.

**Teaching/self-review.** The deterministic family supports 2–6 demonstrations and four prefix-stable queries. Across seeds 0, 17 and 101 and every supported demo count, 30 episodes produced 270 declared-rival checks with no surviving query-changing rival, 120 masked public projections, 30 substantive 30×30 cases, and 44 protected-Racket evaluations. The rival inventory includes fixed header indices, first/last header, smallest component, component count, all-component painting and the canonical rule.

**Qualification.** Native qualification passed both settings at seeds 0 and 17 (4/4 jobs, 40 protected-Racket evaluations). This is reviewer-reported ready evidence only; exact-source owner acceptance and any training admission remain separate.
