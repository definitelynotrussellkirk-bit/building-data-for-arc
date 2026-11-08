# Working notes: 8921bea21bbb

## Review repair `review-3fb645cb8bab611c`

Final generator SHA-256: `987e6c00f0a6a7066e11f454d5680b5aa140806dbb8d55ccbbf883a6f6f8c462`.
Canonical Racket rule hash: `adbc411a920b`; the authority source was not changed.

### Lead and baseline

The prior audit lead in `evidence/review_index.json` came from return `review-88c10647a6e11300:v0001` against baseline generator SHA-256 `2cc0d7f85295689a7e16ba26b9f8e6143567268830bdbb4d26dd88a503218ce9`. It reported that a divider-free 5×11 all-zero grid passed `self_check` but crashed the Racket rule. The current before battery reproduced the broader root cause: acceptance-only validation, no rule pin, no semantic contract, dead difficulty bands, no canonical-profile support, and a broken exact-override contract.

### Distribution and contract choices

- Replaced fill percentages with five directly observable exact axes: panel height/width 5–8, mask count 4–12, mask color 1–8, and right-panel zero count 0–4.
- Added strict rejection of unknown axes, invalid values, and unknown difficulty names.
- Added a deterministic four-profile schedule: canonical 5×5, non-color-2 sparse, canonical 6×6, non-color-2 dense. Every difficulty band receives both canonical profiles and non-color-2 witnesses.
- Kept generated masks 4-connected for compact, legible examples, but did **not** make connectivity a lawful-domain invariant: two of the three canonical inputs have disconnected masks.
- Kept at least two copied colors under the mask and at least one nonzero right-only cell. These make color copying and masking independently observable.
- Pinned `RULE_HASH`, added a Python mirror, exact-axis observability, strict canonical-profile recognition, declared rivals/witnesses, and a lesson-identifiability hook.

### Rivals and tests

The strongest canonical-fitting rival is `color2_only`: it matches all three canonical pairs because every canonical left mask uses color 2. Non-color-2 scheduled profiles refute it. Additional declared rivals are `copy_right` and `modal_mask`, refuted by right-only cells and multicolor overlap respectively.

`workspace/reference_probe.py` is an independent parser/rule mirror used by the task-local regression suite. The 25 tests cover canonical acceptance, exact axes in all bands, invalid-call rejection, canonical profile support, declared witnesses/rivals, all query holdouts across cyclic schedule starts, prior divider-crash impostors, determinism, fresh allocations, and global-RNG isolation.

### Measured final evidence

- After battery: 12/12 stages green.
- Portable task tests: 25/25 passed.
- Semantic battery: 303/600 strict canonical-like draws (50.5%), 12/12 lessons identifiable, 0/48 ambiguous diagnostic rotations.
- Large census: 300/300 lessons materialized, 0 ambiguous production lessons, 0/1,200 ambiguous query rotations, 1,193 unique inputs.
- Exact generated shortcut witness: seed 404, sample index 1, easy band; mask color 3. See `checks/shortcut-witness/finding.json` in the review return.

### Limits

The finite rivals are plausible task-linked alternatives, not a proof of unique induction against every imaginable rule. The validator intentionally recognizes a narrower training grammar than every mathematically executable input: monochrome left masks, 5–8 panel dimensions, 4–12 mask cells, and at most four right-panel zeros. Generated masks are connected even though canonical/legal masks need not be.
## Current reviewer considerations

Source SHA-256: `987e6c00f0a6a7066e11f454d5680b5aa140806dbb8d55ccbbf883a6f6f8c462`.

# Decisions for `8921bea21bbb`

Final generator SHA-256: `987e6c00f0a6a7066e11f454d5680b5aa140806dbb8d55ccbbf883a6f6f8c462`.
Canonical rule hash: `adbc411a920b` (unchanged).

## D1 — Keep the Racket authority; pin it explicitly

**Original rationale:** unknown. The baseline described the correct transformation but omitted `RULE_HASH`.

**Decision:** add `RULE_HASH = "adbc411a920b"`; retain the canonical Racket source unchanged. The canonical examples, Python mirror, rule smoke, authority sync, and exact witness all agree.

**Rejected alternative:** modify the Racket rule to tolerate the validator’s divider-free inputs. That would enlarge the task authority to accommodate a bad validator rather than repair the validator.

**Probe:** before lint failure and after rule-smoke/authority-sync logs under `checks/before/` and `checks/after/`.

## D2 — Replace percentage fills with exact semantic axes

**Original rationale:** the baseline sampled `grid_h`, `panel_w`, `mask_fill`, and `right_fill`; no retained note explains why those ranges were advertised more broadly than the implementation honored.

**Decision:** expose `panel_h`, `panel_w`, `mask_count`, `mask_color`, and `right_zero_count`. These values are observable without reverse-engineering probabilistic fill rates, and each is realized exactly through strict draws and checked after generation.

**Rejected alternatives:**

- Keep fill percentages and estimate realized density. This leaves accepted controls probabilistic and makes exact replay/diagnosis harder.
- Silently clamp out-of-range values. That conceals typos and violates the override contract.
- Preserve all legacy advertised ranges. Heights below 5 and widths below 5 were unnecessary for canonical support and made contrast constraints fragile.

**Failure modes addressed:** unknown axes accepted, declared range endpoints rejected, and missing provenance for realized axes. The final override gate is green; task tests check minimum, maximum, and interior tuples in every band.

## D3 — Use a deterministic four-profile teaching schedule

**Decision:** cycle through `canonical_5`, `non_two_sparse`, `canonical_6`, and `non_two_dense`. Difficulty changes the noncanonical dimensions/counts/holes while canonical anchors remain present in every band.

**Rationale:** random draws alone gave 0/60 exact canonical profiles and did not guarantee a lesson would refute the color-2-only shortcut. A short deterministic cycle makes profile coverage and rival refutation falsifiable.

**Rejected alternatives:**

- Pure random sampling with minimum probabilities: too weak for three-example lessons and hard to audit.
- Only canonical-size examples: preserves appearance but fails to broaden the rule beyond color 2/full right panels.
- Put the witness only in the query: demonstrations could still leave the rival alive.

**Probe:** task test `test_any_three_of_four_scheduled_pairs_eliminate_every_lesson_competitor` checks every held-out position for eight starts in each band. The large census additionally rotates all 1,200 materialized pairs.

## D4 — Generate connected masks, but do not require connectivity

**Decision:** `_connected_mask` generates compact, legible masks. `self_check` accepts disconnected masks.

**Reason:** the first implementation made connectivity a validator invariant; the canonical regression immediately failed on two canonical pairs. Component enumeration showed those masks had two and three components, so connectivity was a sampler preference, not part of the rule.

**Rejected alternative:** weaken the canonical test or special-case canonical grids. That would preserve a false invariant and create two definitions of lawful input.

**Retained limitation:** generated defaults do not explore disconnected masks, even though the rule and validator allow them. This is explicit rather than accidental.

## D5 — Make masking and color copying separately observable

**Decision:** require at least one nonzero right-panel cell outside the mask and at least two distinct nonzero right colors under the mask. Right-panel holes are placed only outside the mask.

**Rationale:** right-only cells refute “copy the whole right panel”; multicolor overlap refutes “paint the mask with one representative color.” Keeping holes outside the mask preserves two copied colors even at the maximum hole override.

**Rejected alternatives:** arbitrary right zeros, which can erase the mask/right overlap and produce zero-valued “kept” cells; fully dense right panels only, which omit an useful axis and remain canonical-looking everywhere.

## D6 — Use a strict, task-semantic validator

**Decision:** validate grid shape/types, exactly one full-height color-9 separator, equal panel widths, explicit dimension/count/color limits, monochrome nonempty left mask, right palette/holes, copied-color contrast, and right-only contrast.

**Rationale:** the prior validator returned success for missing separators and all minimal impostors. The selected grammar is intentionally narrower than the mathematical rule’s entire executable domain, but every restriction is visible and testable.

**Rejected alternatives:** acceptance-only structural checking; accepting blank/no-divider degenerates; requiring generated-only connectivity.

**Probe:** 25 task tests plus the battery’s destructive mutation and minimal-impostor checks. The prior divider-free all-zero witness is specifically rejected.

## D7 — Declare finite plausible rivals and witnesses

**Decision:** declare `color2_only`, `copy_right`, and `modal_mask`; map them to `non_two_mask`, `right_only_cells`, and `multicolour_overlap` witnesses; require all lesson competitors to be eliminated by demonstrations.

**Rationale:** `color2_only` exactly fits every canonical pair, so correctness of individual labels is not enough. The other two are simple, high-probability visual shortcuts that the grammar can refute cheaply.

**Rejected alternatives:** claim semantic uniqueness without executable rivals; enumerate many artificial rules with no task plausibility; treat a finite census as a proof.

**Limit:** undeclared rivals remain unknown. Reports consistently call this finite evidence, not universal identifiability.

## D8 — Build an independent review probe and regression frontier

**Decision:** add `workspace/reference_probe.py` and `tests/test_generator.py`. The probe does not call generator semantic helpers; it independently validates/splits panels and computes the intended and color-2-only outputs.

**Rationale:** testing a mirror against itself would not detect coordinated implementation errors. The portable task-test stage snapshots the tests, workspace, public API, frozen fixtures, and source hashes.

**TDD evidence:** the baseline produced 24 failures/1 pass (`checks/tdd-red.log`). The first implementation produced 2 failures because of the false connectivity invariant (`checks/tdd-green-attempt1.log`). The corrected final source passes 25/25 (`checks/task-tests/result.json`).

## D9 — Do not add a second qualification executable

**Decision:** keep one reusable independent probe plus pytest, instead of duplicating them in another `qualify.py` command.

**Reason:** the battery and lesson-census already provide source-bound JSON evidence. A second task-local runner would repeat logic and risk drifting from the tests; future agents can import `workspace/reference_probe.py` or run the portable task-test stage directly.
