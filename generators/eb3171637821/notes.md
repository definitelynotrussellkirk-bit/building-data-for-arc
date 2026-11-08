# Working notes: eb3171637821

## Review repair `review-53083473b3612763`

The imported `2.2.0` sampler generated only one-cell separators, exposed dead or malformed pseudo-axes, accepted unknown overrides, had a permissive validator, lacked a pinned rule hash and executable semantic contract, and left the selected target-code mirrors textually divergent from the canonical Racket authority. The canonical demonstrations therefore also admitted the strong rival “treat every full divider row or column as a separate separator.”

The selected repair is generator version `3.2.0`, SHA-256 `18dcef177f13525085c354ca39c6e27c93843d0aab2ac814a7bad2e3ba91e59a`:

- pinned `RULE_HASH = "f7892897a4d5"` without changing the canonical Racket program;
- replaced pseudo-controls with six exact observable axes: row/column band counts, row/column divider thicknesses, and row/column boundary modes;
- constructs the complete lawful Cartesian lattice grammar, including 1–2-cell divider runs and boundary dividers;
- rejects unknown, mistyped, and out-of-range overrides and recovers every advertised axis from pixels;
- strengthens `self_check` to require exactly two nonzero colors, one unique divider color, exact Cartesian divider coverage, 2–8 positive bands per axis, and uniform thickness 1 or 2 on each axis;
- keeps ordinary draws in the canonical modal-cell morphology while leaving dense cases available by exact override;
- alternates thick-run and unit-run profiles by sample index, so every consecutive three-demo window contains a witness against line counting;
- declares the canonical shortcut, semantic rival, witness, and lesson competitor as executable functions.

## Retained failures and decisions

The first blind-solve hypothesis for the unrelated task connected arbitrary aligned endpoints and passed only 1/4 examples; the corrected local `4,0,4` rule passed 4/4. During this repair, an early generator passed focused tests but failed distribution morphology because dense divider lattices made the cell rectangles appear as many nonmodal objects. Restricting ordinary draws to modal-cell profiles fixed the root cause while preserving the full exact override domain. A later 300-lesson census found 13 ambiguous lessons under random thickness draws; the deterministic alternating cadence fixed that teaching defect. Both failures remain under `checks/`.

The two selected base-solution `racket_target.target_code` fields were synchronized byte-for-byte to the unchanged canonical `program_solution`. Archival `raw_code` fields were deliberately preserved; final authority sync reports selected synchronization with archival divergence and execution parity.

## Final evidence

- 12/12 after-battery stages green: `checks/after/checks/eb3171637821_after_battery_summary.json`.
- 97/97 selected task tests: `checks/task-tests/result.json`.
- 300/300 source-bound lessons, 1,200 unique inputs, zero declared-rival ambiguity or scoring errors: `checks/lesson-census.json`.
- 720 cyclic three-demo/query windows, zero ambiguity: `checks/cyclic-lesson-audit.json`.
- Exact rival witness checked by independent Python and live Racket: `checks/question/`.
- Final visible-only post-repair solve: 1 revision, 3/3 demonstrations, generator hash bound in `solve/summary.json`.

Imported associated notes remain in `evidence/associated_notes.jsonl`; `evidence/review_index.json` was used only as a lead and all current claims were remeasured.
## Current reviewer considerations

Source SHA-256: `18dcef177f13525085c354ca39c6e27c93843d0aab2ac814a7bad2e3ba91e59a`.

# Decisions for `eb3171637821`

## D1 — Preserve the selected rule; repair the input curriculum

**Choice.** Keep canonical Racket rule hash `f7892897a4d5` unchanged. The rule already matched all canonical pairs and correctly counts positive non-divider row and column bands.

**Rationale.** Baseline `rule_smoke` passed, and direct application to canonical pairs and repaired witnesses agreed with an independent geometry oracle. The defects were distribution, validation, controls, lesson identifiability, and selected-authority text synchronization—not transformation semantics.

**Rejected alternatives.** I did not rewrite the rule to count full divider lines, because that is precisely the canonical-fitting shortcut. I did not broaden the Racket rule to arbitrary noisy grids because the canonical task is a clean two-color Cartesian lattice and such a change would add unsupported semantics.

**Probe/evidence.** `checks/question/racket.json`, final task tests, and `checks/after/checks/eb3171637821_after_rule_smoke.json`.

## D2 — Model contiguous divider runs, not one-cell separators

**Choice.** Permit uniform horizontal and vertical divider-run thickness independently in `{1,2}`.

**Original rationale.** The imported sampler’s effective one-cell-only distribution made “number of divider lines” indistinguishable from “number of cell bands.” Canonical data alone cannot resolve that ambiguity because all canonical runs are unit-thick.

**Rejected alternatives.** Thickness up to 3 or arbitrary per-run thickness would also refute the rival, but adds complexity not needed for a decisive witness and moves farther from the canonical morphology. A single handcrafted witness without ordinary sampling would satisfy a local check but would not teach the rule reliably.

**Failure mode found.** Randomly choosing thickness was insufficient: the first 300-lesson census found 13 lessons whose three demonstrations were all unit-thick while the query was decisive. This is retained in `checks/lesson-census-ambiguous-v3.1.compact.json`.

**Final mitigation.** Alternate profiles by `sample_index`: even indices contain at least one thick axis; odd indices are unit-thick. Every consecutive three-demo window therefore contains both a decisive witness and a canonical-looking example. `checks/cyclic-lesson-audit.json` tests every start 0–11 for seeds 0–19 in all three bands.

## D3 — Include boundary divider runs as exact observable axes

**Choice.** Add `row_boundary_mode` and `col_boundary_mode`, each with `none|start|end|both`.

**Rationale.** The selected rule counts positive cell bands, so an outer divider run does not create an extra output band. Boundary cases exercise the same semantic distinction as internal thick runs and cover a branch present in canonical geometry. Modes are exactly recoverable from pixels and constructively compatible with every declared band/thickness combination under the 30×30 limit.

**Rejected alternatives.** A Boolean “has boundary” axis loses which edge is used; four independent edge Booleans duplicate state and make compatibility harder to audit.

**Probe/evidence.** Parameterized task tests cover all 4×4 boundary-mode pairs with both thickness values, and `observe_overrides` recovers them exactly.

## D4 — Expose only semantic, recoverable controls

**Choice.** Replace imported pseudo-axes with six exact axes: row/column band counts, row/column divider thicknesses, and row/column boundary modes. Reject unknown keys, wrong types, and out-of-range values.

**Rationale.** The baseline advertised controls that were dead, singleton, diagnostic-only, or capable of generating malformed one-color grids. A control is now advertised only when its value can be reconstructed from the returned grid.

**Rejected alternatives.** I did not expose palette values because the shared keyed color draw already provides diversity and no stable public palette override was needed. I did not retain aliases for the broken controls, because silent compatibility would preserve typo acceptance and non-observable behavior.

**Probe/evidence.** The baseline override stage recorded 8,850 findings over 52,200 draws; the final override stage has zero findings and rejects the unknown-key probe (`checks/after/checks/eb3171637821_after_battery_summary.json`).

## D5 — Use a strict lattice validator

**Choice.** `self_check` now requires a nonempty rectangle no larger than 30×30; exactly two distinct nonzero ARC colors; exactly one color having at least one full row and one full column; divider color exactly on the union of those rows/columns; 2–8 positive cell bands per axis; and uniform divider-run thickness 1 or 2 on each axis.

**Rationale.** The old validator admitted impostors and failed to encode the grammar needed by exact override observation and independent semantic probes.

**Rejected alternatives.** A permissive “two colors and some full lines” check would accept holes, extra divider pixels, zero-size bands, and ambiguous divider colors. Validating against generation metadata would not protect externally supplied grids.

**Probe/evidence.** Task tests include malformed palettes, holes, non-Cartesian pixels, ambiguous colors, invalid band counts, and mixed thicknesses.

## D6 — Keep ordinary morphology canonical-like; preserve full stress reachability by override

**Choice.** Ordinary draws select only profiles where the cell color is strictly modal. Dense lawful lattices remain reachable when exact overrides are supplied.

**Rationale.** The first repair made dense divider layouts common. The distribution gate then measured a median of 3.5 nonmodal objects versus canonical 1 because the metric treated separated cell rectangles as objects. Keeping the cell color modal restores the canonical “one connected divider lattice on a background” morphology without reducing the declared exact domain.

**Rejected alternatives.** Weakening the distribution gate or changing only its object metric would hide a real morphology drift. Removing dense cases entirely would make advertised overrides incomplete.

**Failure evidence.** `checks/after-failed-morphology-authority/`. Final default-morphology tests and the full battery are green.

## D7 — Anchor scale without replaying canonical layouts

**Choice.** Use a frequent 27×27 scale profile in every difficulty band, while randomizing band counts, widths/heights, boundary modes, thicknesses, and colors. Broad profiles extend to 18×18 easy, 24×24 medium, and 30×30 hard.

**Rationale.** This satisfies canonical-profile support and keeps every difficulty tied to the observed scale while avoiding memorized canonical pixel arrangements.

**Rejected alternatives.** Exact replay of canonical examples would inflate support metrics without increasing coverage. Restricting every draw to 27×27 would erase useful scale diversity.

## D8 — Make the strongest shortcut executable

**Choice.** Declare `count_individual_divider_lines` in `CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; link it to a `thick_divider_run` witness.

**Rationale.** The rival fits all eight usable canonical pairs and directly captures the ambiguity created by unit-only separators. Executable declarations let the shared census and task-local auditor score the actual function rather than a prose approximation.

**Rejected alternatives.** I did not add contrived palette- or coordinate-specific rules. Finite rival sets do not prove universal induction, so declarations focus on the strongest natural canonical shortcut.

**Probe/evidence.** `checks/lesson-census.json`, `checks/cyclic-lesson-audit.json`, and `checks/question/`.

## D9 — Synchronize active target text, preserve archival evidence

**Choice.** Replace only `racket_target.target_code` in the two selected base-solution records with the unchanged canonical `program_solution`. Preserve `racket_target.raw_code` and the canonical ledger.

**Rationale.** Baseline execution parity already passed, but active target text occupied two exact groups. Selected runtime authorities should be textually synchronized; archival source variants should remain as evidence.

**Rejected alternatives.** I did not normalize or overwrite `raw_code`, and I did not edit the canonical program. Both would erase provenance without changing behavior.

**Probe/evidence.** Final authority status is `selected_synchronized_archival_divergent`, with execution parity PASS, in `checks/after/checks/eb3171637821_after_authority_sync.json`.

## D10 — Retain reusable independent probes

**Choice.** Add `workspace/reference_probe.py` and `workspace/audit_lessons.py` plus a 97-test focused suite.

**Rationale.** Future agents need an oracle that is independent of generator internals, a supported live-Racket parity path, and a cheap audit over all cyclic starts. The tools dynamically import live rival declarations so new competitors are not silently omitted.

**Limitations.** The census and cyclic audit cover finite seeds, schedule starts, and declared rivals. They do not establish that every human or model will infer the intended rule. Ordinary draws deliberately preserve modal-cell morphology, so very dense legal cases rely on explicit override coverage rather than natural frequency.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/eb3171637821/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Parametric MAIN review `review-30e4da5ff3c2fe77` (2026-10-24)

### D11 — Preserve the exact canonical default and add an area-parity encoding

The native parameter is `encoding = solid_count | area_parity`.
`solid_count` returns the byte-exact canonical Racket program (SHA-256
`da9f6ae6f31dc78a860e0b96f157a56ff75e6fd704c4804a9c392bff4663e2fc`).
The alternate keeps the same divider-lattice segmentation but measures the
ordered positive row- and column-band sizes.  Its compressed cell is the cell
color when `row_size × column_size` is odd and the divider color when it is
even.  Thus step B's color choice cannot be made before step A has recovered the
input-dependent band-size intermediate.

The input curriculum is shared exactly between settings, deterministic by seed,
and supports 2–6 demonstrations plus 1–4 prefix-stable queries.  Every example
is constructed to distinguish the two declared settings, and every four-query
episode contains a substantive exact 30×30 lattice.  The default generator and
canonical authority were not edited.

### Current bounded evidence and limits

- Focused task suite: 126/126 passed in `checks/eb3171637821-tests/result.json`.
- Family review: 20 seeds, all supported count boundaries, 240 episodes, 1,480
  examples, 740 matched-setting comparisons, 120 exact 30×30 stress instances,
  1,080 shortcut-rival checks, and 28 protected-Racket evaluations; zero failures.
- Native qualification: two settings × two fresh seeds, three demonstrations and
  four queries per job, status `qualified`; execution SHA-256
  `c419937fb31b872a65aeed2dfb5b00514de2b62d1243f970e06d1e434237ffc8`.
- Sequential witness: two measured-intermediate ablations and four protected-
  Racket evaluations, status `owner_replayed`; both ablations change the final
  output.
- Public projection: four exact visible-byte files passed schema, masked-query,
  content-ID, distinct-input, and duplicate-payload checks.  Settings, seeds,
  programs, and query outputs are absent from public files.

These checks are finite and source-bound.  They do not prove uniqueness against
all possible programs or downstream training gain.  Exact-source owner
integration and fresh native acceptance remain pending; `training_admitted` is
false.  Optional peer tickets were left unrun after finishing MAIN.
