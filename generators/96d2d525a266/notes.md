# Working notes: 96d2d525a266

## Review repair

- Kept the canonical Racket rule unchanged (`RULE_HASH = c060c7f67bbd`).
- Replaced ignored/dead sampler controls with four observable exact axes.
- Broadened `self_check` to the true canonical domain, so all retained canonical examples validate.
- Added independent-oracle, malformed-input, override, distribution, and actual-Racket parity regressions.
- Added explicit rivals for aligned exact pairs, 3+ cell bounding boxes, background-only painting, and numeric color order.
- A first repaired five-profile sampler still produced 3 ambiguous lessons out of 12; that source and report are retained under `WORK/checks/after-semantic-failure-v1`.
- Replaced it with a declared two-slot schedule. Every four-pair lesson has complementary decoy and interaction controls even when each pair is rotated into the query position.
- Exact overrides bypass profile minima, preserving requested counts such as `n_decoy_colors=0`.

Imported associated notes and prior evidence remain under `evidence/`.
## Current reviewer considerations

Source SHA-256: `eb15cc04ebcd9bfe69a1c4c04bc4db97588a9e549e5719c6b52857ac3de70d2f`.

# Decisions: 96d2d525a266

## D1 — Preserve the canonical authority

**Original choice:** The task already had a canonical Racket rule, but the generator did not pin its hash. The rationale for omitting the pin was not retained.

**Decision:** Keep the Racket expression unchanged and pin `RULE_HASH = "c060c7f67bbd"`.

**Why:** Canonical outputs and an independent Python oracle agree. The defects were in the input distribution, validation, controls, and lesson assembly, not the authority.

**Alternatives rejected:** Rewriting the rule to match the old restricted sampler would have removed lawful 3+ cell decoys, overlap, and overwrite semantics. That would change the task rather than repair its data.

**Evidence/limits:** Authority smoke, Racket lint, and authority sync are green. Oracle/Racket parity covered 69 grids, not the entire legal input manifold.

## D2 — Replace fake controls with four observable exact axes

**Original choice:** The baseline advertised texture-like controls including `position_bias` and `decoration_density`, but they were unprobed/dead and exact requests were ignored. Original rationale is unknown.

**Decision:** Expose only `grid_h`, `grid_w`, `n_pair_colors`, and `n_decoy_colors`. Every value is recoverable from the returned grid; unknown, mistyped, and out-of-range requests fail loudly.

**Why:** These are task-relevant, measurable dimensions and support exact experiment stratification.

**Alternatives rejected:** Keeping diagnostic-only cosmetic axes adds metadata without causal support. Allowing approximate controls would make sampling receipts misleading.

**Evidence/limits:** The compact override matrix covered 373 joint cases and 33,570 draws with zero findings. Joint support is bounded to the declared ranges and colors 1..9.

## D3 — Validate the rule domain, not the old sampler subset

**Original choice:** Baseline `self_check` rejected multi-cell decoys, overlapping rectangles, and overwrite cases; it rejected all five canonical inputs.

**Decision:** Accept any rectangular ARC grid containing at least one exact two-cell diagonal pair; keep sampler-specific curriculum requirements out of `self_check`.

**Why:** Validation must recognize lawful canonical inputs and cannot define away difficult rule branches.

**Alternatives rejected:** A strict sampler validator would continue hiding legal cases. A nearly unconstrained validator with no qualifying pair would admit examples where the transformation is vacuous.

**Evidence/limits:** All five canonical inputs validate. The validator intentionally accepts legal shapes outside the sampler's 10..20 ordinary size range, up to ARC's 30×30 limit.

## D4 — Construct semantic interactions explicitly

**Decision:** Build two kinds of ordinary sample:

1. `decoy_controls`: an aligned exact pair and a three-cell non-collinear decoy in a protected 4×4 corner; qualifying rectangles cannot overlap that region.
2. `interaction_controls`: two overlapping qualifying rectangles whose row-major first-occurrence order differs from numeric color order, plus a singleton placed on a future outline to force overwrite behavior.

**Why:** Random frequency was insufficient. A geometric feature only teaches the rule when its rival produces a different visible answer after all overwrites.

**Alternatives rejected:** Merely increasing random draw count left examples where later rectangles erased the distinguishing pixel. Lowering rival strictness would have hidden a real teaching defect.

**Evidence/limits:** The independent probe counted observable rival disagreement, not raw geometry. In 2,048 final draws, every target feature occurred hundreds of times.

## D5 — Use a two-slot lesson schedule

**Original repair attempt:** Five profile types varied features globally, but a three-demo window could omit the one witness needed for its query. The semantic gate found 3 ambiguous lessons out of 12.

**Decision:** Declare `LESSON_SCHEDULE_PERIOD = 2` and alternate complementary decoy and interaction controls. Any four consecutive pairs contain two of each type, so removing any one as query leaves at least one of each in the demonstrations.

**Why:** Lesson identifiability is a property of the assembled demonstrations/query, not marginal feature frequency.

**Alternatives rejected:** Resampling only failed lessons would make replay behavior more complex and could bias acceptance. Increasing demonstrations would raise token cost. Weakening rivals would not improve teaching.

**Evidence/limits:** Final semantic smoke is 12/12 with 0/48 ambiguous rotations. Fixed-seed period enumeration is 6/6 lessons and 0/24 rotations. This exhausts schedule residues at one seed only.

## D6 — Preserve exact override boundaries

**Decision:** Profile minima apply only to ordinary draws. Explicit overrides such as `n_decoy_colors=0` and `n_pair_colors=1` remain exact even when they remove a teaching control.

**Why:** Exact controls are an experimental API; silently coercing them would be worse than producing a deliberately sparse diagnostic sample. Production lessons use ordinary draws and retain the controls.

**Failure mode:** A caller can intentionally create an under-informative isolated grid with exact overrides. The lesson-level gate, not the scalar generator call, is responsible for production teaching support.

## D7 — Add reusable independent tooling

**Decision:** Add `workspace/reference_probe.py` and focused tests that load a selected source, implement an independent oracle, measure observable axes/features, execute declared rivals, and optionally compare against the real Racket runtime.

**Why:** Future reviewers can distinguish generator bugs, mirror bugs, and authority mismatches without relying on prose.

**Limit:** The Python oracle is test tooling, never label authority. Racket remains authoritative.
