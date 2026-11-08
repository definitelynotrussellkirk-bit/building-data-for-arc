# Working notes: f4dc936dfcbb

## Intended rule

Rows with exactly two color-2 cells define inclusive horizontal spans; columns
with exactly two color-3 cells define inclusive vertical spans. The output is a
new all-zero grid with color 8 at a selected row/column coordinate only when
both span-containment conditions hold. Colors other than 0, 2, and 3 are ignored
input distractors. The input markers themselves do not persist.

## Review diagnosis

Baseline `2.1.1` had four blocking classes of failure:

1. `RULE_HASH` was absent and the selected `target_code` differed textually from
   the canonical program despite execution parity.
2. Advertised exact axes were not consumed; dimensions and span counts came from
   one opaque layout RNG, unknown keys were accepted, and no observer existed.
3. The default distribution hit none of the five canonical shape/palette
   profiles, while invalid no-component/disjoint cases were advertised as
   ordinary textures.
4. There was no executable semantic contract, and the summary incorrectly said
   endpoints and decoration remained in the output.

Baseline evidence: `checks/before/checks/f4dc936dfcbb_before_battery_summary.json`
(6 green, 2 advisory, 4 failed).

## Current decisions

- Version `3.0.0` pins canonical `RULE_HASH = "b804c88a8a55"`.
- The selected base-solution `target_code` is now byte-identical to canonical
  `program_solution`. `raw_code`, canonical data, expected outputs, and executed
  behavior were not changed.
- Exact axes are limited to observable controls: `grid_h`, `grid_w`,
  `n_row_spans`, `n_col_spans`, and `n_distractors`. Unknown, wrong-type, and
  out-of-range overrides fail before generation.
- Ordinary draws use two or three row/column spans. The first full row/full
  column create a positive crossing; a lower right-only row and right lower-only
  column create separate horizontal-only and vertical-only rejection witnesses.
  Exact one-span overrides remain constructive but are not claimed as rich
  teaching examples.
- All distractor cells use one ignored color, preserving canonical palette size
  four. They are placed away from selected row/column coordinates so their
  irrelevance is visible rather than accidentally overwritten.
- Two-thirds of default draws use one of the five canonical dimensions; the
  broad branch retains all declared sizes with difficulty weighting.
- `self_check` accepts all five canonical inputs, requires exact endpoint pairs,
  one ignored color, 1–4 distractors, and at least one true crossing.
- Named rivals are `all_span_pairs`, `horizontal_only`, and `vertical_only`.
  Both gate-specific witnesses fire in every default draw.

## Verification

Final generator SHA-256:
`30f13596807e2d0d5b28b090d1cf738d6d482b2f3d02448d9cd9f68517842e8a`.

- After battery: 12/12 green, 0 advisory, 0 failed.
- Profile floor: 40/60 exact canonical profiles and 40/60 envelope hits.
- Override matrix: 38,790/38,790 accepted draws, 431 cases, zero findings.
- Semantic smoke: 600/600 strict inputs; both witnesses fired 600/600; 12/12
  lessons and 48/48 rotations had no declared-rival ambiguity.
- Larger census: 300/300 lessons, 1,200 unique pairs, 1,200/1,200 rotations,
  zero ambiguity, hook warning, scoring error, or materialization error.
- Portable task tests: 34/34 passed.

## Limits and open findings

The finite rival set does not prove unique induction against every imaginable
wrong rule. Role colors 2, 3, and 8 remain fixed because they are semantic, not
interchangeable palette roles. Generated inputs intentionally exclude malformed
or vacuous no-span cases from training. No blocking finding remains.
## Current reviewer considerations

Source SHA-256: `30f13596807e2d0d5b28b090d1cf738d6d482b2f3d02448d9cd9f68517842e8a`.

# Decisions for f4dc936dfcbb

## D1 — Preserve the rule; synchronize its selected source

**Prior state.** The canonical and selected programs were execution-equivalent,
but the generator omitted `RULE_HASH` and selected `target_code` differed by
comments/representation. The baseline authority gate failed.

**Decision.** Pin `b804c88a8a55` and make selected `target_code` byte-identical
to canonical `program_solution`. Leave canonical JSONL, `raw_code`, expected
outputs, and semantics untouched.

**Rejected alternative.** Keeping the commented equivalent and weakening exact
source synchronization was rejected because it leaves two textual authorities
for no behavioral benefit.

## D2 — Advertise only controls recoverable from pixels

**Prior rationale.** Unknown. Version `2.1.1` named palette, density, texture,
position, and count axes that were constant, aliases, dead, or bypassed through
an opaque RNG.

**Decision.** Keep five integer controls: height, width, row-span count,
column-span count, and distractor-cell count. Validate unknown keys, booleans,
floats, strings, and bounds before constructing a context; consume every valid
override through typed keyed draws; recover each value in `observe_overrides`.

**Rejected alternative.** Declaring the old labels diagnostic would make the
checker quiet without making the training distribution controllable.

## D3 — Generate positive and independent negative branches constructively

**Decision.** Use a full-span upper row and full-span left column for a positive
crossing. When at least two spans are present, add a lower row restricted to the
right half and a right column restricted to the lower half. This yields:

- upper row × right column: horizontal true, vertical false;
- lower row × left column: horizontal false, vertical true;
- lower row × right column: both true.

Third spans use complementary half spans. Marker endpoints occupy reserved
boundary/cut coordinates, so row and column endpoints cannot overwrite each
other. Exact one-span overrides remain valid and yield one positive crossing.

**Rejected alternative.** Random endpoint placement plus retry was rejected: it
can silently collapse endpoint counts, miss one-gate negatives, and make exact
joint overrides probabilistic.

## D4 — Match canonical profiles without narrowing the domain

**Decision.** A keyed branch selects one of the five canonical dimensions and
uses a single repeated distractor color, guaranteeing palette size four. A broad
branch retains every dimension in 8..18 by 9..20, with difficulty weights but
full support in every band. Ordinary span counts are 2..3; exact 1 remains an
override for canonical/count boundary coverage.

**Rejected alternative.** Memorizing complete canonical layouts was rejected.
Only dimensions and palette cardinality are anchored; marker geometry and
locations remain generated.

## D5 — Make the strict manifold explicit

**Decision.** `self_check` rejects malformed/ragged grids, noninteger colors,
input color 8, lone or overfull endpoint sets, too many spans, zero/multiple
ignored colors, distractor-count drift, and no-crossing cases. The same predicate
serves `strict_canonical_like` and accepts all five canonical inputs.

**Limit.** The training manifold intentionally excludes vacuous/no-span and
malformed cases. These are not useful ordinary examples for this positive rule.

## D6 — Treat plausible shortcuts as executable contracts

**Decision.** Declare three rivals:

1. `all_span_pairs` ignores both containment gates;
2. `horizontal_only` ignores vertical containment;
3. `vertical_only` ignores horizontal containment.

Two witnesses detect a pair that passes exactly one gate and bind it to the
relevant rivals. The same rivals are lesson competitors and canonical shortcuts.
Every ordinary draw fires both witnesses.

**Rejected alternative.** A prose-only claim that spans “usually vary” was
rejected because it cannot be scored at the lesson/query boundary.

## D7 — Test first and retain both red and green evidence

**Decision.** Add 34 task-local tests before implementation. The red run failed
for missing hash/hooks and ignored controls. The green suite checks canonical
oracle parity, exact controls in all bands, malformed mutations, distribution,
and rival disagreement. The supported portable runner passed all tests.

## D8 — Measure lesson assembly, not just individual grids

**Decision.** Run 100 lessons per band and rotate every one of the four labeled
pairs into the query. Report production and rotation verdicts separately.

**Result.** 300/300 lessons, 1,200 unique pairs, and 1,200/1,200 rotations had no
declared-rival ambiguity. This finite result does not prove identifiability
against undeclared hypotheses.

## D9 — Keep audit targets isolated

The assigned audit targets were read and measured only. No audit source was
patched. A reproducible right-origin counterexample for `11447f24cd43` is kept
under `checks/audit/11447f24cd43/`; `2a41d6b25262` is reported clean under the
checks actually run.
