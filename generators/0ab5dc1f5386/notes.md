# Working notes: 0ab5dc1f5386

## Baseline reproduced

Baseline generator SHA-256 was `9a25bad14926f161b9e8353909c699ade38201467342054921b22275b6fe3dae`. The required before battery produced 5 green, 1 advisory, and 6 failed stages. The actionable roots were:

- canonical inputs were rejected by the task validator;
- the generator omitted the canonical `RULE_HASH`;
- documented override bounds did not match constructive support, and unknown overrides were silently accepted;
- defaults did not reliably hit canonical-size profiles in every band;
- no executable rival/witness curriculum established what each lesson taught;
- `target_code` differed from canonical authority only by a comment in `crop-cells`, causing authority synchronization failure.

No prior return was used as an implementation source. Packet evidence and the canonical row were treated as authority.

## Repair design

Version `4.1.0` replaces the narrow random object mix with a deterministic period-four semantic schedule. Four isolated quadrants separated by a zero cross make component boundaries constructive while still allowing layout jitter, varied connected masks, density differences by difficulty, and varied colors. Default grid profiles are canonical-scale; exact size and texture overrides are validated before generation.

The curriculum declares and executes five rivals:

1. rotate a transposed crop to fit;
2. choose the last equal-size crop;
3. reuse one crop for every matching frame;
4. flatten a multicolor crop to one color;
5. track byte-identical source occurrences separately instead of marking their crop value used.

The fifth rival was found during final self-review. A regression was written first and failed against version `4.0.0`; `single_use` was then changed to emit two byte-identical loose crops and two matching frames. Under the canonical rule only the first frame fills because `used` stores the full crop value. Version `4.1.0` therefore teaches the actual value-equality semantics instead of the more intuitive occurrence-identity rule.

## Authority decision

The Racket behavior was not changed. The sole authority-file edit removes the comment that made `target_code` byte-diverge from the canonical `program_solution`; `raw_code`, callable behavior, rule hash `1529a4ef373b`, and canonical outputs are unchanged.

## Reusable probes

`workspace/reference_probe.py` independently implements the intended transformation and all five rivals, loads the canonical examples, computes the normalized rule hash, observes profiles/crops, and can request real Racket outputs when the protected runtime is available. `tests/test_generator.py` uses this helper rather than trusting the generator's own mirror.

## Final measurements

Final generator SHA-256: `a4b6e6fe9ddca55ec8349902dc6ae62d3b0a81b757c9bcb7e4ce401b083ad897`.

- Full after battery: 12/12 green.
- Protected task-local suite: 44 passed.
- Production lesson census: 300 materialized lessons, 100 per band, 1,500 unique inputs, 0 ambiguous, 0 errors; all five semantic competitor names were refuted in every lesson in every band.
- Explicit shortcut witness: seed 1201, sample index 2, `single_use`; the occurrence-identity rival fits all 5 canonical pairs but differs from Racket in 4 cells.
- Fresh visible-only post-repair solve: 4/4 demonstrations in one revision; prior rule exposure declared yes, reference consultation during the solve declared no.

## Limits

The census is finite declared-rival evidence, not a proof of universal identifiability. Its standard runner does not rotate every pair into every possible query position, so the task-local suite separately checks all four cyclic starts of the period-four curriculum. The four-quadrant layout intentionally favors isolated objects; it does not sample touching frame/source components or arbitrary clutter outside the canonical task domain. Training approval remains unchanged.
## Current reviewer considerations

Source SHA-256: `a4b6e6fe9ddca55ec8349902dc6ae62d3b0a81b757c9bcb7e4ce401b083ad897`.

# Decisions for 0ab5dc1f5386

## D1 — Keep the canonical Racket behavior

**Original rationale:** The original author intent is not recorded. The baseline Racket implementation, canonical pairs, `raw_code`, and normalized rule hash all agreed on size-matched copying with source retention and value-based one-use.

**Decision:** Do not rewrite the rule. Remove only the comment that made bank `target_code` text differ from canonical authority.

**Alternatives rejected:** Changing `used` to source indices would make the intuitive occurrence-use rule true but would alter canonical semantics. Editing canonical data to match the bank comment divergence would be authority churn with no behavioral value.

**Probe:** Canonical pairs were checked with an independent Python oracle and the protected Racket bridge; final rule smoke and authority sync are green.

**Failure modes and limits:** Text synchronization can conceal a behavior change if only hashes are checked, so tests also compare canonical outputs and 24 generated outputs against independent semantics.

## D2 — Use canonical-scale defaults and honest exact axes

**Original rationale:** Unknown; the baseline advertised `grid_h=10..18` and `grid_w=12..22` but could not construct every declared boundary and missed per-band canonical support.

**Decision:** Defaults rotate among `(12,16)`, `(13,17)`, and `(13,18)`. Exact override rectangles are `grid_h=12..18` and `grid_w=16..22`.

**Alternatives rejected:** Keeping broader nominal bounds with ad hoc rejections would preserve a misleading contract. Sampling only one canonical size would satisfy the floor but reduce scale diversity.

**Probe:** Boundary tests cover both corners of the rectangle, all textures, and four difficulty values. Ninety-six default draws per band must hit all three canonical profiles and at least 90 unique grids.

**Failure modes and limits:** Default profiles are deliberately concentrated around canonical support rather than uniformly sampling the full override rectangle. Exact large-size support is tested but less frequent by default.

## D3 — Four isolated slots with a zero cross

**Original rationale:** The baseline used free placement, but its intended component semantics require frames and loose sources not to merge accidentally.

**Decision:** Place at most four tiles in quadrants separated by one zero row and column, with slot shuffling and within-slot jitter.

**Alternatives rejected:** Unconstrained rejection sampling was harder to make deterministic and could silently bias masks/positions. A fixed unjittered layout made position shortcuts too easy.

**Probe:** Constructive generation calls `self_check` before returning. The default distribution test requires high exact-grid uniqueness, varied mask densities, and many crops without both bbox corners occupied.

**Failure modes and limits:** Isolation is a real domain restriction. The generator does not teach how the rule should behave when frame/source components touch or when unrelated clutter bridges components.

## D4 — Period-four semantic curriculum

**Original rationale:** The imported summary named several textures, but selection was random and no complete lesson was guaranteed to distinguish the named rules.

**Decision:** Every four consecutive default examples contain `orientation_decoy`, `scan_order`, `single_use`, and `multicolor` exactly once. `EXAMPLES_NEEDED=4` makes the intended lesson size explicit.

**Alternatives rejected:** Random texture draws can produce lessons that never show a decisive case. A longer schedule would consume demonstration budget without adding a presently identified rule dimension.

**Probe:** Tests inspect all four cyclic starts for every difficulty and require every declared competitor to disagree on at least one demonstration. The 300-lesson production census independently checks assembled lessons.

**Failure modes and limits:** The finite competitor set can miss unimagined shortcuts. Adding a new canonical-fitting rival should require adding a scheduled witness or explicitly documenting why no generator witness is possible.

## D5 — Connected, bbox-exact masks with difficulty-dependent density

**Original rationale:** The baseline pinned corners and used a narrow path-like mask family, making crop detection easier than the canonical task requires.

**Decision:** Connect randomly chosen anchors on all four bbox sides to a random center, then grow a connected frontier to a density drawn around a band-specific mean. Colors are placed so every requested color occurs.

**Alternatives rejected:** Full rectangles would erase zero-pattern semantics. Independent Bernoulli masks would require repair/rejection and could split into multiple components.

**Probe:** Tests count multiple density pairs, corner-free crops, exact self-check acceptance, determinism, and Racket parity.

**Failure modes and limits:** Difficulty currently changes density, not object count or frame dimensions. It should not be interpreted as a calibrated human difficulty model.

## D6 — Reject unknown or dishonest overrides

**Original rationale:** Unknown. The baseline accepted typo keys and advertised values outside the actual `draw_int` domains.

**Decision:** Validate override names and primitive types first; exact values are then passed through keyed context draws. There are no declared incompatible combinations because every documented cross-product is constructive.

**Alternatives rejected:** Silently ignoring unknown keys makes misspelled experiments appear successful. Declaring broad incompatibilities would hide construction weaknesses rather than fix them.

**Probe:** Parametrized tests cover all texture/size/difficulty combinations at both boundary corners and explicit invalid key/type/range cases. Final override battery is green.

**Failure modes and limits:** `observe_overrides` can directly recover grid size but not texture from arbitrary grids. The battery verifies texture behavior through its semantic effects and generation receipts.

## D7 — Broaden `self_check` to the canonical task, not just generator style

**Original rationale:** The baseline validator encoded its own narrow shape conventions and rejected lawful canonical examples.

**Decision:** Validate rectangular ARC grids, exact hollow color-8 frames, initially empty frame interiors, and at least one loose nonzero component. Do not require generator-specific profile, palette, corner, or count choices.

**Alternatives rejected:** A permissive “rectangular grid only” validator would admit malformed color-8 objects. Retaining generator-style checks would continue rejecting canonical support.

**Probe:** Every canonical input must pass, generated outputs must pass, malformed grids and malformed frames are exercised by the shared battery.

**Failure modes and limits:** The validator intentionally does not prove that a matching source exists for every frame; unmatched frames are lawful. Semantic correctness still requires rule execution or an independent oracle.

## D8 — Independent probe and explicit rivals

**Original rationale:** The baseline had comments about possible mistakes but no executable, independently checkable rival catalog.

**Decision:** Add `workspace/reference_probe.py` with an independent intended oracle, canonical loader/hash helper, Racket adapter, crop/profile inspectors, and five rivals. Generator declarations are checked against this probe.

**Alternatives rejected:** Testing generator `_intended` against generator rivals would allow shared bugs to pass. Using private runner internals would make the tool nonportable and violate the supported interface.

**Probe:** Declared rivals must agree with independent implementations on witnesses; real Racket must match the independent intended oracle on canonical plus 24 generated inputs.

**Failure modes and limits:** The probe exposes canonical answers and must never be opened during a visible-only solve. It is a review/test tool, not production generation code.

## D9 — Teach one-use by crop value, not source occurrence

**Original rationale:** The baseline explicitly noted value-equality semantics but avoided byte-identical shapes, so the data actually taught only the easier occurrence-use interpretation.

**Decision:** `single_use` emits two byte-identical 2x2 source occurrences and two matching frames. The intended rule fills one frame because the first crop value enters `used`; the occurrence-index rival fills both.

**Alternatives rejected:** Keeping distinct colors/crops would leave occurrence identity observationally equivalent. Changing the rule to occurrence identity would be an unjustified authority change.

**Probe:** The new regression first failed against version 4.0.0, then passed after the profile change. The exact Racket witness at seed 1201/sample 2 differs in four cells, and `occurrence_use` is refuted 100/100 lessons per band.

**Failure modes and limits:** Equal-valued copies are generated only in `single_use`, so a learner still depends on seeing the full four-example curriculum. The schedule guarantees that for default lessons.

## D10 — Preserve decisive evidence compactly

**Original rationale:** The shared census records full grids and repeated aliases; one final 300-lesson JSON was 14,128,283 bytes.

**Decision:** Keep a human-scale summary, deterministic gzip of the complete final JSON, and a manifest with original/compressed sizes, hashes, and restoration command. Keep the genuine before failure and interrupted after run intact; summarize and remove the obsolete successful v4.0 census raw file.

**Alternatives rejected:** Dropping the final full census would prevent replay. Keeping both large intermediate and final JSON files would exceed the return budget without improving the final claim.

**Probe:** The manifest records original SHA-256 `d54b9c0d8c60918c77b99fe6d32cb84e98de74633960900e1ce52a7d744f7e76` and compressed SHA-256 `418f12a1ee3d104156e06f0de3a44b2c06ea990c5414d7242f5c291d6178f97a`.

**Failure modes and limits:** A maintainer must restore the gzip to inspect per-lesson grids. The compact summary deduplicates rival aliases by semantic name and is not itself a substitute for the full report.

## Native parametric source-order family — review-ad1be2ac4da16d7d

Built a source-bound native family under `workspace/parametric/` without changing
`generator.py` or canonical authority. `source_order=row_major` returns the exact
canonical Racket source. `source_order=column_major` changes only the ordering of
loose source crops while retaining canonical frame order and full-value single-use
state. The first assignment therefore determines the used-crop intermediate
consumed by every later frame.

The sampler supports independently selected 2–6 demonstrations and 1–4 stored,
prefix-stable queries with matched inputs between settings. Query four is a
substantive 30x30 case. A finite protected-Racket audit covered four seeds, both
settings, the opposite setting and two executable no-used-state rivals: 98
executions, zero findings. The portable task suite passed 71 tests. Native
qualification passed two settings at seeds 0 and 17 (40 protected labels), replayed
byte-identically, and the protected wrong-intermediate witness changes 80 final
cells. Sixteen independent single-query public views verified with no future-query
or private-setting exposure. This is reviewer-ready only; owner integration,
fresh acceptance, and any training decision remain pending.
