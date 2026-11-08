# Working notes: da16c00eed25

## Review repair

The imported v2 sampler encoded two presentation accidents as if they were
semantic requirements: both row and column gaps were at least two, and the
rectangle never touched the top or left boundary. It also exposed dead/aliasing
axis metadata, accepted unknown overrides, had no `self_check`, no semantic
rival contract, and no pinned `RULE_HASH`.

The v3 repair keeps the Racket authority unchanged and makes the Python source
match the actual task domain. Public exact controls are now grid height, grid
width, row gap, column gap, missing corner, and corner color. Returned pixels
recover all six controls through `observe_overrides`; malformed and unknown
requests fail loudly, while impossible dimension/gap pairs use structured
incompatibility errors.

## Curriculum decision

The three strongest declared shortcuts all fit every usable canonical pair:

1. complete only when both gaps are at least two;
2. complete only a missing lower-row corner;
3. complete only rectangles strictly inside the frame.

A four-slot cyclic schedule reserves one ordinary sample as a joint rebuttal:
it has an adjacent row gap, a missing top corner, and top-boundary contact.
Because `EXAMPLES_NEEDED = 4`, every cyclic four-demo window includes that
sample. The remaining three slots use the broad weighted sampler so the
counterexample itself does not become the whole distribution.

## Retained checks

- Task-local regressions: `tests/test_generator_da16c00eed25.py`.
- Reusable Racket-backed lesson census: `workspace/lesson_probe.py`.
- Final finite census: 100 lessons per band, 300 total; every lesson refuted all
  declared competitors and passed `lesson_identifiable`. This is finite evidence,
  not a proof of universal induction.

## Limitations

The generator intentionally covers only the clean single-color, exactly-three-
corner domain. It does not teach distractor handling, multiple rectangles,
mixed colors, rotated/non-axis-aligned geometry, or malformed inputs. The
canonical rule itself is unchanged.
## Current reviewer considerations

Source SHA-256: `132432bd4c575b78ff4c6200e3052169f0e4c2e9804c4b4909520bf58073e3c6`.

# Decisions for `da16c00eed25`

The IDs below correspond to the findings in `REVIEW.md`. “Original rationale” means rationale visible in the inherited source; where none was documented, it is marked unknown rather than inferred.

## D1 — Preserve the clean three-corner semantic domain (R1, R3)

- **Choice:** Require exactly three nonzero cells, one shared color, exactly two rows, exactly two columns, and exactly one absent row-column product.
- **Original rationale:** The v2 summary described this rule, but its ordinary `texture` domain also included two-corner, four-corner, and collinear negative fixtures. No rationale explained why malformed negatives were advertised as valid generator inputs.
- **Alternatives considered:** Keep negative textures as ordinary controls; add distractors or multiple rectangles; loosen validation.
- **Probe:** Baseline defect lint reported `texture-domain-overlap`; final `self_check` accepted all three canonical inputs and rejected 56/56 destructive mutations.
- **Reason:** A generator used for labeled lessons should sample a coherent rule domain. Negative teaching fixtures belong in explicit diagnostics, not in the ordinary valid axis set.
- **Failure modes / limits:** This intentionally excludes robustness to distractors, multiple objects, mixed colors, and malformed scenes.

## D2 — Replace template axes with six pixel-observable exact controls (R1, R3)

- **Choice:** Expose `grid_h`, `grid_w`, `row_gap`, `col_gap`, `missing_corner`, and `corner_color`; recover all six through `observe_overrides`.
- **Original rationale:** Unknown. The inherited `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture` fields were template-like aliases or singletons; several never affected pixels.
- **Alternatives considered:** Mark dead fields diagnostic; retain palette aliases; expose row/column start controls too.
- **Probe:** Baseline override gate stopped before its matrix on three unprobeable declarations and accepted an unknown key. Final override gate ran 142,740 draws with zero findings or warnings; unknown keys are rejected.
- **Reason:** Every public exact axis should be independently observable in returned pixels. Start positions remain sampled rather than public because no requirement needed exact placement control.
- **Failure modes / limits:** Exact dimension/gap pairs can be impossible. Those combinations raise a structured incompatibility exception naming the conflicting axes rather than silently changing either request.

## D3 — Use the full lawful 4..14 size range with canonical weighting (R1)

- **Choice:** Allow both dimensions from 4 through 14, while weighting canonical heights/widths and band-appropriate sizes.
- **Original rationale:** The v2 metadata claimed 4..14 but defaults used only height 6..9 and width 7..11.
- **Alternatives considered:** Keep narrow defaults; sample 4..14 uniformly; force one canonical shape per lesson.
- **Probe:** Final profile floor found exact canonical-size/palette profiles in every band: 11/20 easy, 6/20 medium, and 1/20 hard.
- **Reason:** The range creates geometric variety, while weighting prevents hard-band sampling from losing all support for canonical profiles.
- **Failure modes / limits:** Hard-band canonical support is deliberately sparse (1/20 in the fixed census), so future weighting changes should rerun the profile-floor gate.

## D4 — Admit adjacent rows and columns (R1, R2)

- **Choice:** Set `row_gap` and `col_gap` domains to 1 through the largest value that fits the chosen dimension, with gap 1 deliberately favored.
- **Original rationale:** The inherited source required gaps of at least two, apparently matching canonical presentation; no semantic justification was documented.
- **Alternatives considered:** Preserve minimum gap 2; make adjacency diagnostic-only; use uniform gaps.
- **Probe:** The exact input in `checks/shortcut_counterexample.json` has both gaps equal to one. Racket adds the fourth corner while `min_gap_two` returns the input unchanged. The rival nevertheless matches all 3 canonical pairs.
- **Reason:** Adjacency is lawful under the row/column-product rule and is the strongest simple counterexample to the inherited spacing shortcut.
- **Failure modes / limits:** Favoring adjacency could itself dominate. The broad sampler and 1,479/1,500 unique-input lesson census guard against a single repeated geometry, but do not prove absence of every distributional shortcut.

## D5 — Cover all missing corners and frame boundaries (R1, R2)

- **Choice:** Sample all four missing-corner indices and allow rectangles to touch any outer boundary; boundary starts are weighted.
- **Original rationale:** Missing corners were nominally random, but the inherited placement always excluded top and left contact. No rationale was documented.
- **Alternatives considered:** Interior-only scenes; boundary cases only in tests; uniform starts without deliberate boundary support.
- **Probe:** Final semantic gate measured `top_missing` in 373/600 draws and `edge_touching` in 581/600; all bands fired. Each linked rival claim held in 60/60 Racket comparisons.
- **Reason:** Top-missing and edge-touching examples directly distinguish `bottom_missing_only` and `interior_only`, both of which fit all canonical pairs.
- **Failure modes / limits:** Boundary weighting is strong. It is intentional curriculum support, but future consumers should not reinterpret frequency as part of the puzzle rule.

## D6 — Reserve one joint rival counterexample in every four-demo window (R2)

- **Choice:** Use a four-slot cyclic schedule: one `rival_counterexample` followed by three broad `free_*` positions. `EXAMPLES_NEEDED` is four.
- **Original rationale:** The inherited generator had no declared lesson-level curriculum or rivals.
- **Alternatives considered:** Pure random sampling; one dedicated slot per rival (three constrained slots); make every sample a counterexample.
- **Probe:** Task regression exhausts every cyclic start. The source-bound Racket probe checked all 12 band/start combinations and 300 independent lessons; every lesson refuted all three rivals and passed `lesson_identifiable`.
- **Reason:** One combined witness guarantees teaching support without consuming most of the lesson with constrained fixtures.
- **Failure modes / limits:** The guarantee covers the three declared rivals, not all conceivable programs. The finite 300-lesson census is not a uniqueness proof.

## D7 — Keep the Racket authority unchanged

- **Choice:** Pin `RULE_HASH = "b83881c49fb4"` and change only the Python sampler/contract.
- **Original rationale:** The canonical rule already correctly completes the unique missing corner.
- **Alternatives considered:** Broaden or rewrite the rule; modify canonical examples.
- **Probe:** Final rule smoke applied 120 cases without error; authority sync was green; the authority-set SHA is unchanged from baseline.
- **Reason:** The observed defects were all sampler and contract defects. Changing a correct authority would add risk without addressing root cause.
- **Failure modes / limits:** The archival bank contains a pre-existing divergent copy, but the selected canonical authority and execution parity remain synchronized.

## D8 — Add task-local regressions and a production-path lesson probe (R1–R3)

- **Choice:** Add six focused tests and `workspace/lesson_probe.py`, which stages the portable runtime, reads live rival declarations, and labels through selected Racket.
- **Original rationale:** No task tests or source-bound lesson census existed.
- **Alternatives considered:** Rely only on the generic battery; write a source-only Monte Carlo script; copy rival names into the probe.
- **Probe:** The tests were observed failing before the repair and pass afterward. The lesson tool verified generator source/staged hashes, all usable canonical shortcut fits, 100 lessons per band, unique-input counts, and every cyclic start.
- **Reason:** Generic smoke samples are too small to establish lesson-level rival coverage. Reading declarations from the live generator prevents the audit from silently drifting from production semantics.
- **Failure modes / limits:** The tool currently uses private runner bridge helpers because no public source-bound Racket-probe API exists; see F1 in `FEEDBACK_TO_CODEX.md`.

## D9 — Treat the fresh solve as exposed, not blind (R4)

- **Choice:** Record `earlier_rule_exposure = yes` and `reference_consulted_during_solve = false`.
- **Original rationale:** The required solve occurs after generator review, so prior rule exposure is unavoidable.
- **Alternatives considered:** Claim a blind solve; skip the solve; consult the reference again during solving.
- **Probe:** `solve/summary.json` binds the episode to final generator SHA `132432bd…`; revision 1 passed 4/4 visible examples.
- **Reason:** This preserves useful implementation evidence without overstating independence. Masked-query correctness remains unknown.
- **Failure modes / limits:** Visible fit is not private-label verification, and the solve is not evidence about an unexposed model's inference ability.
