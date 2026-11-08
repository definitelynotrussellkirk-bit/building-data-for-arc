# Working notes: 531905d00c4b

## Current parametric family: native qualified, owner acceptance pending

The separate `workspace/parametric/adapter.py` adds three fixed settings:
`canonical`, `larger_left`, and `larger_right`. The canonical generator and exact
Racket authority are unchanged. A resolves horizontal index neighbors through
the legend into occupied-cell counts; B uses that input-dependent comparison to
reflect each occurrence's tight crop before padding and mosaic placement. Ties
keep the original crop; absent neighbors have zero mass. Repeated tokens can
therefore have different orientations, excluding a fixed per-color remapping.

The sampler supports 2–6 demos and 1–4 queries independently, normally three/four.
Matched split/slot seeds preserve prefixes across settings and counts. It teaches
opposite contexts, both numeric-color ordering relations, equal masses across
different colors, cropping, padding and non-3x3 frames in the first two demos.
Connected paths/dense masks vary actual geometry. Four staggered 6x6 prototypes
and a dense 5x5 index give a real 30x30 input/output stress case. This separate
four-color grammar extends the production library-height domain; it does not
claim that the existing production validator accepts the new stress cases.

Evidence: `checks/531905d00c4b/` in the return. 33 focused tests passed; protected
Racket audit seed 17 verified 18 selected labels and refuted 24 extra per-policy
rivals on two demos; all 12 public files expose exactly one query. Native
qualification covers six jobs (three settings, seeds 0/17, three demos/four
queries), 42 selected labels and 78 executions. The protected causal witness replaces
occupied counts by bounding-box areas and changes the final answer.
`workspace/parametric/evidence/manifest.json` inventories the exact source; the
small `evidence/current/checks.json` binds the focused proof. Independent code
review found no blockers and checked current qualification/witness bindings.

Retain `audit.py` for focused future reviews. Its rule errors are failures,
never refutations; only demonstration-surviving rivals need query evaluation.
The native source closure requires helpers inside the parametric home, hence
`grid.py` reuses the pure routines from the existing task probe. See the local
README for commands and the sequential public projection.

Limits: finite seeds/rivals, four legend colors in this sampler, no universal
identifiability or measured learning benefit. Owner exact-source replay and
acceptance remain required; no training admission. Next action is native owner
intake/acceptance, not a redesign or a repeated production battery.

## Review `review-45842a59b486e21d` — 2026-10-03

### Defects found in imported version 3.0.0

- `self_check` required every prototype to touch every library row, rejecting four of the five canonical inputs even though the authority independently crops each prototype.
- The sampler generated only full-height/top-aligned prototypes, unpadded lower indices, and effectively fixed `3×3` canonical tiles. Three plausible rivals therefore fit all canonical pairs and were not reliably contradicted by generated lessons:
  - preserve absolute library-row offsets;
  - tile the uncropped lower area;
  - force every tile to `3×3`.
- `texture` advertised invalid/poisonous fixtures as ordinary exact overrides; unknown keys were accepted; several controls were difficulty-dependent or not observable.
- No canonical `RULE_HASH` or executable semantic contract was declared.

### Selected repair

Version 4.0.0 keeps the canonical Racket program unchanged and replaces the sampler/validator contract:

- four-cycle profile schedule (`canonical_core`, `shifted_prototype`, `padded_index`, `broad_tiles`);
- variable connected prototype crops with independent vertical placement;
- independently cropped dense lower matrix with optional top/left padding;
- strict exact override validation and pixel recovery;
- canonical-compatible `self_check` and `strict_canonical_like`;
- executable witnesses, rivals, canonical shortcuts, and lesson competitors;
- independent Python oracle and real-Racket parity tests.

### Measured evidence

- Before battery: 6 green, 1 advisory, 5 failed (`checks/before/checks/531905d00c4b_before_battery_summary.json`).
- Final battery: all 12 stages green (`checks/after/checks/531905d00c4b_after_battery_summary.json`).
- Source-bound qualification: 100 five-pair lessons per band, 1,500 distinct generated inputs total, zero validator/replay failures, and every lesson in every band refuted every declared competitor (`checks/qualification.json`).
- Racket parity: 53 canonical/generated inputs matched the independent oracle. The retained absolute-row witness differs from the authority in 36 cells (`checks/shortcut-witness.json`).

### Limits

The qualification is a finite deterministic schedule, not a proof over every seed and override combination. The profile scheduler currently records its chosen default through `GenCtx._record` because the runtime has no public scheduled-value API; this is covered by tests and the official override gate but remains a maintainability dependency on a private method.
## Current reviewer considerations

Source SHA-256: `0a828b75ef0274502b74326a1cdd4605ba85fd88076fcad557ed7dcca8db90ab`.

# Decisions — 531905d00c4b

## D1 — Preserve the canonical Racket authority

**Choice.** Keep the selected Racket program byte-for-byte unchanged and pin its normalized hash as `2ace815dad55`.

**Rationale.** Independent Python reconstruction matched all five canonical pairs, and untouched rule smoke/authority checks were already green. The observed failures originated in the Python generator and validator, not the transformation authority.

**Rejected alternative.** Rewriting the rule to fit version 3's full-height prototype assumption would have encoded the generator defect into the authority and contradicted canonical shorter prototypes.

**Probe/failure mode.** `test_rule_hash_is_pinned_to_selected_authority`, canonical-pair oracle checks, 53-input Racket parity, and final authority-sync. A future authority change must update the pin and parity evidence deliberately.

## D2 — Use an explicit four-profile teaching schedule

**Choice.** Repeat `canonical_core`, `shifted_prototype`, `padded_index`, and `broad_tiles` by `sample_index % 4`.

**Rationale.** Each profile has one semantic job:

- `canonical_core` guarantees exact canonical size/palette support in every difficulty band;
- `shifted_prototype` refutes retaining absolute library-row offsets;
- `padded_index` refutes tiling uncropped lower padding;
- `broad_tiles` refutes a fixed `3×3` tile rule.

A five-pair lesson necessarily spans all four profiles from every cyclic start, so shortcut support is lesson-local rather than merely frequent in the global pool.

**Rejected alternatives.** Pure random mixing could leave individual lessons without a critical witness. A larger profile taxonomy added combinations without addressing another identified canonical shortcut.

**Probe/failure mode.** `workspace/qualify.py` tests all four cyclic starts and 100 lessons per band. The remaining limitation is finite seed coverage; schedule coverage does not prove how a learner will generalize.

## D3 — Keep the exact axis surface small, lawful, and band-independent

**Choice.** Advertise only pixel-observable controls:

- `library_h`: 3–5;
- `prototype_count`: 3–5;
- `prototype_w`: maximum cropped width 2–4;
- `index_h`, `index_w`: 2–5;
- `index_top_padding`, `index_left_padding`: 0–2;
- `vertical_layout`: `top_aligned`, `bottom_aligned`, or `mixed`.

Every value is legal in easy, medium, and hard. Unknown keys and wrong types/ranges raise immediately. `observe_overrides` independently recovers every requested value from pixels.

**Rationale.** Version 3 advertised generic/poisonous controls that either did not alter the intended domain or created malformed rule inputs. Exact controls should be honest interventions, not test fixtures.

**Rejected alternatives.** Keeping `texture=missing_separator|zero_in_index|unknown_index_color` as ordinary domains was rejected; those are negative validator tests, not training samples. Difficulty-specific override ranges were also rejected because the same exact request should not silently become invalid in another band.

**Probe/failure mode.** The official override matrix is green, including unknown-key rejection. Task tests force the same extreme exact override in all four band values (`None`, easy, medium, hard).

## D4 — Construct prototypes by independent crop geometry

**Choice.** Generate 3–5 separated same-color connected objects with varied crop heights, widths, and row offsets. At least one full-height anchor prevents an accidental all-zero row inside the library; shorter objects create crop witnesses. Shapes are connected walks grown within an exact bounding box.

**Rationale.** The authority keys tiles by independently cropped objects. Absolute placement should vary without changing tile semantics. One full-height anchor makes the first all-zero separator unambiguous while still allowing other prototypes to shift.

**Rejected alternatives.** Full-height rectangles reproduce the original shortcut. Arbitrary disconnected pixels make object identity ambiguous. Allowing a blank library row before the separator would make parsing underdetermined.

**Probe/failure mode.** `self_check` validates connected components, separation columns, dimensions, and separator position. The independent probe—not generator helpers—reconstructs crops and compares to Racket.

## D5 — Crop-relevant lower padding is a first-class axis

**Choice.** Generate a dense 2–5 by 2–5 token matrix using only prototype colors, optionally preceded by 0–2 blank rows and columns.

**Rationale.** Canonical examples alone have no lower padding, so an uncropped-index rule fits them all. Scheduled padding makes the need to crop visible without introducing zero holes inside the matrix.

**Rejected alternatives.** Internal zeros were rejected because zero is background, not a prototype token, and would add a separate missing-token policy not present in the authority.

**Probe/failure mode.** `self_check` rejects zero holes and unknown token colors. The padded profile refutes `uncropped_index` in every lesson.

## D6 — Make canonical support constructive rather than accidental

**Choice.** `canonical_core` fixes a 3-row, 3-prototype, max-width-3, top-aligned library with zero index padding and widths yielding `6×11` or `7×11` inputs with four colors including background.

**Rationale.** The official profile floor checks only 20 draws per band; relying on low-probability random matches is brittle. A scheduled exact profile gives deterministic support while other profiles carry semantic diversity.

**Rejected alternative.** Forcing all profiles to canonical dimensions would pass the floor but keep the fixed-size shortcut.

**Probe/failure mode.** Final profile floor is green. The large qualification recorded 151/125/125 exact canonical profiles in easy/medium/hard respectively; counts differ because some non-core easy samples also happen to match the same coarse size/palette signature.

## D7 — Align `self_check` with the authority and generated domain

**Choice.** Accept canonical shorter prototypes; validate ARC shape/colors, first blank separator, 3–5 separated prototype components, crop widths, lower dense bbox, padding limits, known tokens, and output bounds. `strict_canonical_like` delegates to this check.

**Rationale.** A validator should describe lawful inputs, not construction details such as “every object touches every library row.” It must also reject malformed inputs diagnostically rather than throw.

**Rejected alternative.** A minimal presence-only validator would let ambiguous separators, fragmented prototypes, unknown tokens, and oversize outputs pass.

**Probe/failure mode.** Canonical acceptance, five malformed-grid cases, unknown-token and zero-hole tests, 1,500 generated self-checks, and official self-check/strict-profile gates.

## D8 — Declare rivals as executable contracts

**Choice.** Declare three functions in both `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`:

1. `absolute_row_padding`;
2. `uncropped_index`;
3. `fixed_3x3`.

Map each to an executable witness predicate.

**Rationale.** All three rivals exactly fit all five canonical pairs. Naming them in prose alone would not verify that claim or ensure generated lessons contradict them.

**Rejected alternative.** A copied rival-name list in the probe was rejected; the qualification tool iterates the generator's actual declarations, so contract drift becomes visible.

**Probe/failure mode.** Qualification first proves each declared shortcut fits every canonical pair, then checks per-input disagreement and per-lesson refutation. The strongest exact witness is retained separately with real Racket output.

## D9 — Add independent, reusable test tooling

**Choice.** Keep transformation reconstruction in `workspace/reference_probe.py`, separate from production helpers, and provide `workspace/qualify.py` as a one-command source-bound audit.

**Rationale.** Testing generator output with generator-internal parsing can reproduce the same bug twice. The independent probe performs its own component search, cropping, padding, tiling, and rivals. Real Racket parity remains mandatory for authority claims.

**Rejected alternative.** Treating the Python oracle as replacement authority was explicitly rejected. It is supplementary and the `--racket` mode never silently falls back.

**Probe/failure mode.** The tool records generator/probe/rule hashes, exact sampling formulas, unique-input manifests, and Racket mismatch indices. Its own task-local tests went red before implementation and green afterward.

## D10 — Fresh solve and audits remain evidence, not approval

**Choice.** Run one honest visible-only solve after freezing generator bytes, and retain two findings-only audits without editing those targets.

**Rationale.** The solve checks whether a finite generated lesson exposes the intended rule to a Python reasoner. The audits test review discipline on unrelated generators. Neither changes catalog approval or admits training data.

**Solve result.** One revision passed all 3 visible examples; masked labels remain unknown. Earlier rule exposure is honestly declared `yes` and reference consultation during solve `no`.

**Audit results.** Both assigned targets have exact Racket-backed counterexamples in `checks/`; neither target was modified.

## Remaining implementation dependency

The scheduled default must be recorded into generation provenance. `GenCtx` exposes typed random draws but no public “record this scheduled exact choice” method, so `_draw_axis` uses private `ctx._record`. Official lint/override tests accept the behavior, but a runtime refactor could break it; feedback F1 proposes a public API.
