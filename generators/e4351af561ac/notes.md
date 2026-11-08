# Working notes: e4351af561ac

## Current rule and authority

The single blue (1) component is the shape template. Only green (3) components equal to it under translation and one of the four quarter-turn rotations survive; surviving cells become cyan (8), and every other cell becomes 0. Reflections are not accepted unless the shape is also rotationally equivalent. Matching components in other colors are distractors. The Racket authority was not changed; `RULE_HASH = f060a0eb09ab`.

## Repaired generator design

Version `4.0.0` replaces the prior broad but misleading contract with a constructive grammar:

- canvas `9..16 × 12..18`;
- one 3–5-cell blue template fitting a 3×3 box;
- `1..2` matching and `1..2` nonmatching green components;
- `0..1` rotationally matching component in another color;
- six separated 2×3 placement regions, so all advertised count combinations are realized without rejection sampling.

The only exact axes are `grid_h`, `grid_w`, `template_size`, `n_match`, `n_nonmatch`, and `n_other_match`. Unknown keys, booleans, non-integers, out-of-range values, and negative/non-integer `sample_index` values are rejected. `observe_overrides` recovers every axis from pixels.

## Lesson policy

`EXAMPLES_NEEDED = 3`, with a declared four-step schedule. Residues 0 and 2 use the canonical size/palette envelope; residues 1 and 3 add a matching non-green distractor. Every draw includes a nontrivial rotation and an equal-area nonmatch; teaching profiles prefer chiral templates, making a reflected nonmatch available. Declared rivals cover translation-only, reflection-allowed, all-green, color-agnostic, and size-only rules.

At final source SHA-256 `f1999eccef30a67200ff4f68537b52912d4ba68a63cb1c87c895303e080ef38f`, the fixed-seed schedule census checked all 12 band/start lessons and 48 query rotations with zero ambiguity. The larger production census checked 300 lessons / 1,200 query rotations, all with no declared-rival ambiguity and 1,200 unique inputs. These are finite checks against declared rivals, not a proof against every possible hypothesis.

## Reversed prior choices

- Prior metadata claimed that the template and all rotation-equivalent colors survive. That was false; the canonical rule keeps only matching color-3 components. Metadata, summary, tests, and semantic contract now state the actual rule.
- Prior axes included dead or ignored texture/count controls and band-specific ranges that rejected values advertised as legal. Those controls were removed rather than silently accepted; six exact observable axes remain.
- Prior random placement could underrepresent the canonical envelope and had no lesson-level semantic guarantee. The new constructive schedule supplies canonical-profile support and explicit rotation/reflection/color-role witnesses.

## Independent checks and limits

`workspace/reference_probe.py` is an independent Python geometry oracle and rival audit. It does not provide generation labels; Racket remains authority. Across 256 draws per band it found zero self-check failures or nondeterminism, 768 unique inputs, and full refutation of translation-only, reflection-allowed, all-green, and size-only rivals; color-agnostic is intentionally refuted on the two color-role schedule residues.

`counterexamples/multi_rival_witness.json` is a legal minimum-domain 9×12 fixture that combines a rotated positive, mirrored negative, and non-green rotational match. Its focused test refutes all five declared rivals, and `checks/counterexamples/e4351af561ac/racket.json` confirms its expected output with the pinned canonical rule.

Known limits: shapes are restricted to connected 3–5-cell forms fitting 3×3; object packing uses six coarse regions rather than a uniform spatial distribution; other-color distractors are at most one component; the finite rival set may miss future shortcuts. These bounds are deliberate and documented rather than advertised as general rule limits.
## Current reviewer considerations

Source SHA-256: `f1999eccef30a67200ff4f68537b52912d4ba68a63cb1c87c895303e080ef38f`.

# Decisions for e4351af561ac v4.0.0

All final-source measurements below bind to generator SHA-256 `f1999eccef30a67200ff4f68537b52912d4ba68a63cb1c87c895303e080ef38f`. The canonical Racket rule was not edited.

## D1 — Preserve the selected canonical rule; repair the generator contract

**Prior choice:** the old summary implied that the blue template and rotationally matching objects of multiple colors survived. The implementation had no `RULE_HASH`, while the selected Racket authority actually keeps only matching color-3 components and recolors them 8. The original rationale for that metadata mismatch is unknown.

**Decision:** pin `RULE_HASH = "f060a0eb09ab"` and rewrite the module documentation, summary, invariants, tests, rivals, and notes around the selected canonical behavior.

**Rejected alternative:** modify Racket to match the stale prose. That would change authority despite the canonical program and selected target already agreeing and solving all four canonical pairs.

**Probe/evidence:** baseline lint (`checks/before/checks/e4351af561ac_before_lint.log`), canonical independent parity (`checks/reference-audit.json`), final rule smoke and authority sync (`checks/after-final/checks/`).

**Failure mode/limit:** an archival raw program remains textually divergent. Execution parity passes, and the selected canonical/target authorities are synchronized, so this is documented rather than rewritten.

## D2 — Replace rejection-heavy stochastic placement with six constructive slots

**Prior choice:** the old sampler drew broad dimensions and counts, then placed components opportunistically. Some advertised combinations were rejected or silently not realized, and provenance for exact axes was incomplete. Its original reason was likely implementation convenience, but no retained rationale establishes that.

**Decision:** partition every canvas into 2×3 regions separated by one blank row/column, place at most one component per region, and keep the maximum component count at six. This makes every advertised count product feasible on the minimum 9×12 canvas and guarantees diagonal separation without retries.

**Rejected alternatives:**

1. Keep rejection sampling and declare many incompatibilities. Rejected because legal controls should be constructive when the domain is this small.
2. Grow the canvas dynamically to fit failed draws. Rejected because it would make exact dimension overrides unreliable.
3. Use fixed absolute locations. Rejected because it would create stronger positional shortcuts; each component instead gets a shuffled region and random legal offset.

**Probe/evidence:** `test_minimum_canvas_supports_every_count_product`, 22,320-draw override gate, and independent `observe_overrides` parity.

**Failure mode/limit:** coarse region occupancy is not spatially uniform and excludes tightly interleaved components. This is a documented sampler restriction, not a claimed rule restriction.

## D3 — Expose exactly six recoverable axes

**Prior choice:** the previous contract advertised palette, distinct-color, density, position-bias, and texture controls that were dead, overlapping, ignored, or accepted malformed values.

**Decision:** expose only `grid_h`, `grid_w`, `template_size`, `n_match`, `n_nonmatch`, and `n_other_match`; validate types/ranges before entering the generator context; reject unknown keys; provide `observe_overrides` so the gate can recover values from pixels.

**Rejected alternative:** preserve legacy names as aliases. Rejected because a compatibility alias that does not correspond to an independently observable property recreates the original silent-control defect.

**Probe/evidence:** baseline defect/override logs; final 248 cases × 3 bands × 30 seeds with zero findings; explicit invalid-key/scalar tests.

**Failure mode/limit:** callers using removed controls now receive an error instead of an approximate behavior. This is intentional fail-fast compatibility breakage inside an unapproved generator.

## D4 — Use connected 3–5-cell shapes fitting a 3×3 box

**Prior choice:** old shape generation had a wider but weakly specified object distribution and did not guarantee reflection/rotation teaching cases.

**Decision:** enumerate all four-connected 3–5-cell shapes in a 3×3 universe, quotient by rotation, and choose non-rotationally-symmetric templates. Default teaching phases use chiral 4- or 5-cell shapes when available; explicit `template_size=3` remains supported even though triominoes cannot provide the same chirality distinction.

**Rejected alternatives:**

1. Enumerate larger polyominoes. Rejected for this round because constructive packing and exhaustive exact-axis support would become more expensive without addressing a known failure.
2. Treat reflections as matches. Rejected because the canonical Racket rule accepts rotations only.
3. Use arbitrary equal-area noise as the sole negative. Rejected because a reflected negative is a more targeted counterexample to a plausible rule.

**Probe/evidence:** rotation/reflection task test, semantic witnesses, retained multi-rival witness, and Racket rule smoke.

**Failure mode/limit:** the generator does not cover large or high-aspect-ratio components. Future expansion should preserve exact packing and rerun schedule identifiability.

## D5 — Alternate canonical-profile and color-role phases

**Prior choice:** baseline random draws produced only 7/60 exact canonical-profile hits and zero hard-band support, while no schedule guaranteed a non-green rotational match.

**Decision:** declare a four-step schedule:

1. `canonical_chiral_a` — canonical size/palette/count envelope;
2. `color_role_a` — broader dimensions/counts plus one matching non-green distractor;
3. `canonical_chiral_b` — another canonical-profile draw;
4. `color_role_b` — another color-role draw.

Canonical phases ignore difficulty for dimensions because every band must retain source-like support. Color-role phases scale the broad canvas range with difficulty.

**Rejected alternatives:**

1. Put a non-green distractor in every grid. Rejected because it would remove direct canonical-palette support.
2. Sample profiles independently with low probability. Rejected because finite lesson windows could omit the only color-role witness.
3. Use only canonical scenes. Rejected because `color_agnostic` would survive lessons containing only colors 0, 1, and 3.

**Probe/evidence:** final profile floor 32/60 with support in every band; color-agnostic witness 303/600 semantic draws; schedule/lesson censuses.

**Failure mode/limit:** phase is periodic in `sample_index`. It is not visible in the grid, but downstream exporters should vary start indices rather than always presenting the same phase order.

## D6 — Require three demonstrations and support every query rotation

**Prior choice:** no `lesson_identifiable` hook, competitor set, schedule period, or demonstration minimum existed. Individual labels could therefore be correct while a plausible wrong rule fit the whole lesson.

**Decision:** set `EXAMPLES_NEEDED = 3`, declare a four-pair schedule, define five pure competitors, and make every single-pair holdout identifiable. The supported policy is stronger than ordered-only production: any one of the four pairs may be the query.

**Rejected alternative:** certify only the final scheduled pair as query. Rejected because arbitrary rotation support costs little for this small period and makes data assembly safer.

**Probe/evidence:**

- fixed seed 0, all 12 band/start lessons and 48 rotations: zero ambiguity (`checks/schedule-census.json`);
- 100 lessons per band, 300 lessons and 1,200 rotations: zero ambiguity (`checks/lesson-census.json`);
- final semantic gate run with `--require-rotations-identifiable` and the schedule receipt.

**Failure mode/limit:** only declared rivals are scored. A future shortcut hypothesis must be added to both the competitor contract and retained tests before claiming it is covered.

## D7 — Retain one compact witness that breaks all five rivals

**Decision:** add `counterexamples/multi_rival_witness.json`, a legal minimum-domain 9×12 grid containing a chiral template, rotated green positive, mirrored green negative, and matching color-2 distractor.

**Why:** generated census evidence is broad but cumbersome. A single stable fixture gives future agents a fast semantic smoke test and makes each distinction visually inspectable.

**Probe/evidence:** task test `test_retained_counterexample_refutes_all_declared_rivals`; canonical Racket receipt `checks/counterexamples/e4351af561ac/racket.json`; verification report alongside it.

**Rejected alternative:** store only a random seed. Rejected because later RNG/framework changes could obscure the semantic witness even when the intended contract remains valid.

**Failure mode/limit:** one witness cannot characterize the whole distribution; it complements rather than replaces the 600-draw semantic gate and lesson censuses.

## D8 — Add an independent authoring probe, but keep Racket authoritative

**Decision:** add `workspace/reference_probe.py` for component extraction, rotation classes, independent expected outputs, rival outputs, exact-axis observation, deterministic replay, and canonical parity.

**Why:** the shared battery is authoritative but expensive to inspect when debugging. The probe supplies a small reusable diagnostic for future agents and writes source-bound JSON.

**Rejected alternative:** have generation call the Python oracle for labels or validity. Rejected because that would couple the sampler to a duplicated rule implementation and undermine Racket authority.

**Probe/evidence:** 768 draws, 768 unique inputs, zero self-check failures/nondeterminism/canonical mismatches (`checks/reference-audit.json`).

**Failure mode/limit:** the Python transcription could itself be wrong. Canonical pairs and `arcpuzzles apply` are therefore used to cross-check it, and report text explicitly labels it supplementary.

## D9 — Leave both adversarial audit targets unchanged

- `dc050b56cac4`: no issue found in the task-test + strict semantic scope checked. No repair ownership was implied by the audit.
- `ea957ff0d072`: production ordering is identifiable, but 9/60 diagnostic query rotations are ambiguous because some holdouts remove the sole marker-attachment color-key witness. This is a downstream assembly-policy question, not a defect under its documented ordered curriculum.

Exact findings and limits are in `AUDIT.md`; no audit-target source bytes were changed.

## Open limits

- Spatial layouts are constructive and region-based, not uniform over all legal packings.
- Shape support is connected 3–5-cell forms inside 3×3.
- At most one other-color rotational match appears in a grid.
- The strict canonical-like fraction is deliberately about one half because the other half teaches color-role rejection.
- Finite declared-rival checks do not establish identifiability against every possible program.
- Catalog approval remains a maintainer action; this return reports checks but does not self-approve training admission.
