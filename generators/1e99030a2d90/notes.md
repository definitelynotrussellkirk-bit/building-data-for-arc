# Working notes: 1e99030a2d90

## Review identity and authority

Review `review-c3005a6f67773c6a`, 2026-10-08. Original version 1.3.0; selected replacement 2.1.0. No predecessor review was used as a lead: the supplied notes were placeholders, associated notes were empty, and there was no task review index.

Final generator SHA-256: `24bf72620cb4334d6e170c2c1565e57cb0946baec217a7826cfe71487c17d1a0`.
Original generator SHA-256: `fd9e92a73152b502e0adb511ede7e2fcd988c25be469d8af3829f1be0d1f1212`.
Canonical Racket hash: `54991f3f258a`, unchanged. The Python rivals are deliberately wrong alternatives, and the test oracle uses an independent intersection of shifted red-coordinate sets. Neither supplies production labels.

## R1: restore meaningful exact controls

The original generator silently ignored several advertised controls and replaced others with difficulty-dependent defaults. The baseline battery failed lint, defect lint, and override checks, with profile and semantic advisories. The new control surface contains only three supported quantities: height, width, and the number of actually qualifying blank centers. Unknown or retired controls fail explicitly. Booleans and coerced strings/floats are rejected instead of becoming integer controls.

Constructive placement makes target counts exact. Each target uses a reserved 3×3 slot; missing dimensions expand when needed. The joint capacity is `floor(h/3) * floor(w/3)`. This is deliberately a sampler-support restriction: lawful shared-arm patterns can exceed that count. Incompatible requests identify the conflicting supplied axes. Small/dense requests keep exact geometry and counts but may lack complete negative evidence.

## R2: teach the cardinal predicate instead of a pristine template

The canonical data has four labeled training pairs and one labeled test pair, all with palette 0/2 and dimensions 10×10 or 11×11. All 18 final declared rivals fit all five canonical labels. A perfect isolated diamond template is therefore a plausible shortcut, as are accepting any nonzero arms, ignoring the center's existing color, wrapping around edges, and ignoring a direction.

Default generation deliberately includes: a real target with an occupied diagonal; one incomplete cross for each omitted arm; a red occupied center; and a boundary cell that qualifies only under wrapping. The period-four schedule uses canonical 10×10 inputs at residue 0, color counterexamples at residue 1, canonical 11×11 inputs at residue 2, and color counterexamples at residue 3. Only the latter introduce non-red arms. Fixed colors 0, 2, and output 4 keep their semantic roles; there is no general color permutation.

Motif positions use randomized slack and reflections. Additional free-position red clutter is accepted only when it preserves the exact target count and protected witness cells. This adds context and connections without making a rejection sampler responsible for correctness. The slot construction, profile/palette correlation, and always-present default cues remain distribution restrictions.

## R3: repair an intermediate query-only color shortcut

Version 2.0.0 (`b59addf9812f5c9f43a4da3bf69ee80daf148734165bea773f61b22cac7ce9d5`) passed 57 task cases, the battery, and a 300-lesson census against its nine original rivals. Independent review then found a stronger alternative: accept arm colors in `{2,4,7,9}`. With seed 0, easy difficulty, and indices 1..5, the first four examples used foreign colors 3 and 8 but the query used 7. The rival fit every demonstration and painted an extra query cell at zero-based (15,15). The public Racket apply command confirmed the whole five-pair witness. The subsequent regression genuinely failed before the fix.

Version 2.1.0 chooses the foreign arm color from the family seed and keeps it fixed as sample indices advance. `warm_arms` and all eight `red_or_COLOR` variants were added to the declared competitors. A five-pair consecutive window has two or three color-counterexample inputs, so every one-pair holdout retains a demonstration of the same foreign color. Unused-color rivals can survive a family while agreeing on all its queries; the claim is absence of query disagreement among these rivals, not that every rival is eliminated.

Exact minimal witnesses are in `counterexamples/minimal-cardinal-witnesses.json`. The failed full lesson is in `counterexamples/warm-color-lesson-v2_0.json`. Both identify which source was used for reference execution and which source's rivals were evaluated.

## Final measured evidence

The return's `checks/` contains the complete reports, including earlier failures. All final measurements below bind to the final SHA above.

- Public battery: 12/12 green, with required query rotations; no advisory stage.
- Task-local regression file: 12 test functions, 58 collected cases; 58 passed, zero failed/errors/skipped in the public isolated runtime.
- Exact-control probe: all 4,800 combinations of height 5..24, width 5..24, and target count 1..12 at seed 17, index 9, medium difficulty; 4,196 exact successes, 604 documented capacity rejections, zero errors, six deterministic replays passed.
- Semantic sample: 600 inputs, 200 per band; zero crashes, 301 strict-canonical palette inputs, and the seven non-color witness predicates each present in 600/600. Foreign-color witnesses occurred in 299/600 and warm-color witnesses in 105/600. Racket confirmed each declared witness/rival claim on 60 checked witnesses per claim.
- Larger lesson census: 100 lessons per band, indices 0..99, seeds derived by the recorded census recipe; 300/300 materialized, 1,500 distinct inputs, zero production ambiguities and zero ambiguities in all 1,500 holdouts against the 18 distinct rivals.
- Finite schedule check: seed 0, all four declared start residues, all three bands; 12 lessons and 60 holdouts, zero ambiguity. These overlapping windows contain 23 distinct inputs. This does not exhaust other seeds.

The declared schedule has period 4. The census's generic residue-reporting field `sampler.period=6` is its diagnostic modulus, not the generator period; `schedule_coverage.period=4` is the explicit schedule enumeration binding.

## Use and limits

Production lesson contract: same family seed, fixed difficulty, four consecutive demonstrations followed by a query; the tested rotation policy holds out each of the five labeled pairs while preserving the remaining order. The guarantee does not cover arbitrary cross-family shuffling, fewer demonstrations, incompatible or cue-starved overrides, undeclared hypotheses, every possible legal input, or model learning outcomes.

The strict hook accepts lawful 0/2 inputs with at least one target, including every canonical pair in every band. Extended foreign-color inputs pass the general validator but are explicitly outside the strict canonical palette. `MIN_STRICT_FRAC=0.3` is a declared floor; the measured final rate is 301/600, not an assertion that all draws are canonical.

See `workspace/README.md` for reusable reproduction commands. The catalog remains the approval authority.
## Current reviewer considerations

Source SHA-256: `24bf72620cb4334d6e170c2c1565e57cb0946baec217a7826cfe71487c17d1a0`.

# Decisions for review-c3005a6f67773c6a

## Scope and authoritative rule

Repair only `1e99030a2d90`; keep both independently drawn audit targets findings-only. The canonical rule already expresses the intended local predicate, so changing it would redefine the task instead of repairing its sampler. No reference authority, canonical record, root test, shared runtime, or catalog approval was changed.

The rule accepts arbitrary lawful arm context more broadly than the chosen sampler. The distinction is deliberate: the general validator accepts canonical inputs and extended color witnesses, while generation uses a smaller constructive support whose limitations are documented.

## R1: exact controls and construction

**Chosen:** retain only `grid_h`, `grid_w`, and `n_diamonds`, validate exact Python integers, and honor every supplied compatible value. Count actual qualifying cells after construction. Unknown/retired keys fail explicitly.

**Rejected:** keeping aspirational or ignored axes for backwards appearance; silently clipping a request; interpreting requested count as a number of attempted placements. Each would preserve the interface defect. The original failures and the independent 4,800-case negative/positive probe make the difference observable.

**Chosen:** disjoint 3×3 slots with randomized slack, reflections, protected witnesses, and free red clutter that preserves the count. This gives a direct construction and clear rejection boundary. A request may fail when `n_diamonds > floor(h/3)*floor(w/3)` even if an overlapping shared-arm arrangement would be lawful under Racket. The exception states a sampler incompatibility; it must not be advertised as mathematical impossibility.

**Rejected:** exhaustive unconstrained rejection sampling for exact counts. It creates unpredictable runtimes at dense boundaries and makes teaching cues accidental. A richer overlapping-target sampler is a future extension requiring its own count/witness controls, not a claim made by this repair.

## R2: canonical support and negative evidence

**Chosen:** keep exact 10×10 and 11×11 0/2 profiles in every difficulty band, alternating with larger foreign-arm examples. `strict_canonical_like` distinguishes canonical palette from accepted extensions. Final measured strict support is 301/600; the minimum declared floor is 0.3. Exact-profile checks found support in every band.

**Chosen:** all four missing-arm directions, a nonzero diagonal at a real target, a red occupied center, and an edge wrapping trap in each default input. Each corresponds to an executable rival that fits all five canonical labels and a Racket-verified distinguishing witness. This tests the actual cardinal predicate rather than relying on visual variety alone.

**Rejected:** random color shuffling of the entire input or output. Red 2 and output yellow 4 are fixed semantic colors. Only a separately added false cross has a non-red color, and Racket confirms it stays unchanged. Such extended inputs pass the domain validator but are not counted as strict-canonical palette.

**Remaining restriction:** normal inputs always contain several teaching cues and shapes correlate with schedule phase/palette. Small/dense exact overrides retain exactness but may omit cues. These choices support a bounded curriculum; they do not enumerate all legal inputs or furnish a guarantee for arbitrary overrides.

## R3: teachable family palette and lesson assembly

**Chosen:** four demonstrations plus one query from one seed, one difficulty, and consecutive sample indices. The period-four schedule is canonical10, foreign, canonical11, foreign. The larger census materializes that production assembly and rotates every labeled pair into the query position, keeping the remaining order.

**Rejected after evidence:** independently redrawing the foreign color at each sample index. In v2.0.0, seed 0/easy/start 1 had foreign colors 3 and 8 in demonstrations, then 7 in the query. A rule accepting `{2,4,7,9}` arms agreed on all demonstrations and disagreed at query (15,15). `checks/color-ambiguity-v1/` preserves authoritative outputs and the genuine failed regression; task counterexamples retain the exact input arrays.

**Final choice:** latch the foreign color to `seed % 8`, using the eight non-red ARC colors. A five-pair window includes two or three foreign examples; any one-pair holdout retains at least one demonstration of the same color. The rival set expands from nine to 18 distinct competitors, including warm-color and red-or-C alternatives. This does not imply that an unused-color alternative is refuted in every family: it can survive while agreeing on all answers in that family.

The measured production and rotation verdicts are both no ambiguity found: 300 materialized lessons and 1,500 holdouts across three bands. A separate affordable enumeration covers all four schedule starts at seed 0 in each band: 12 lessons/60 holdouts, with only 23 unique inputs because windows overlap. Neither sample proves identifiability against undeclared rules or supports shuffling inputs from independently seeded families.

## Tests and reusable tooling

The task-local suite uses `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` so it works from the library tree and the isolated public test runtime. Its independent oracle intersects shifted red coordinate sets, rather than importing the generator's own center helper. There are 12 named test functions and 58 collected cases. Failed baseline and intermediate results are retained.

`workspace/probe_exact_controls.py` is the concrete reusable tool built for later reviewers. It supports an alternate generator path, reports exact source hashes and selected seed/band/index, refuses to overwrite evidence, and separates ordinary success from documented construction rejections. Its six repeat draws test deterministic replay. It deliberately does not claim to generate authoritative output labels.

The selected-source change did not justify a whole-repository test run. The required 12-stage battery, explicit public task-test invocation, larger lesson/schedule censuses, and independent fresh-patch replay target the actual risks. Fresh replay must use a new environment and fresh offline Racket runtime, with the isolated Git root checked before `git apply`.

## Evidence, exposure and acceptance

Keep all genuine failures and every solve revision. The blind solve has no earlier exposure; the repaired-task solve has earlier repair exposure but no reference consultation during its visible solve phase. Hidden-query correctness stays unknown. No intentional wrong program is presented as an accidental solver failure.

Large reports are losslessly compressed with exact original path/size/SHA mappings and a tested restorer. This keeps the return small while retaining complete failures and exact census instances. Runtime installations and duplicate repository trees are omitted.

Shared follow-up F1 proposes opt-in role-aware rival generation in the semantic tools, motivated by R3; it is a maintainer decision and is not silently patched into this task return. F2 improves the wrapper's documented interpreter path. Audits A1 and A2 are separately reproduced findings, not additional source repairs or acceptance blockers for the selected task.
