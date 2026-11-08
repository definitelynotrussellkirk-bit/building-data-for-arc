# Current notes: 8c069ab108a1

## Intended rule and authority

The selected Racket program is unchanged and remains the label authority. The
input has exactly one color-9 anchor. For every other colored cell, the output
contains that cell's color at the 0°, 90°, 180°, and 270° rotations around the
anchor; color 9 itself is removed. `RULE_HASH = 9bb2dc983950` pins that selected
program. The Python `rule_mirror` is test support, not a replacement authority.

## Reversed distribution decision

**Prior choice (v1.2.0):** generate several disconnected colored motifs near a
roughly central anchor. That layout was inherited from an earlier “gallery
pack” design; the exact original rationale is unknown. It was a poor match to
the cellwise rotation rule: multiple motif cells frequently occupied the same
rotational orbit, differently colored cells overwrote one another in scan
order, and many rotations fell outside the grid.

**Current choice (v2.0.0):** construct the input from complete, distinct
four-position rotational orbits and select exactly one representative cell from
each orbit. Anchors retain a two-cell boundary margin. This makes every source
cell visible in all four rotations, removes cross-color overwrite aliases, and
keeps labels about rotation rather than clipping or iteration order.

Evidence: the retained 3,000-draw source-bound census changed from 2,668 grids
with clipping, 1,822 with cross-color orbit collisions, and only 46 clear grids
to 0 clipping, 0 collisions, and 3,000 clear grids. See
`workspace/orbit_integrity_probe.py` and the review's
`checks/orbit-integrity-{before,after}.json`. A minimal baseline reproducer is
in `counterexamples/review-34f601b1f83910ae-v0001/`.

## Curriculum and exact controls

The truthful public axes are `grid_h` and `grid_w` (7..14), `n_cells` (2..6),
and `n_colors` (1..4). Unknown keys are rejected. `n_colors > n_cells` is the
only declared incompatibility when both are explicitly requested; when only one
count is overridden, the unspecified dependent count adapts so the requested
axis remains exact.

A four-slot schedule alternates two canonical-scale one-color scenes with two
multicolor, off-center-anchor scenes. Any four consecutive pairs therefore
contain at least two counterexamples to the canonical-fitting
`first_color_only` and `monochrome_first_color` shortcuts, while every lawful
pair refutes `half_turn_only`; off-center slots refute `center_anchor_only`.
`EXAMPLES_NEEDED = 3`, and focused tests hold out every query position from
every cyclic four-pair window.

## Assumptions and known limits

- The ordinary curriculum intentionally excludes clipped rotations and shared
  orbits. The selected rule can produce boundary/overwrite behavior on arbitrary
  grids, but the three canonical pairs do not teach a collision priority or a
  useful clipped-orbit concept.
- Inputs use colors 1..8 for seeds and reserve 9 for the anchor.
- The named rival set is finite. Passing it does not prove uniqueness against
  every imaginable hypothesis.
- The final 300-lesson census used three demonstrations and rotated each of four
  materialized pairs through the query position: 0/300 production ambiguities
  and 0/1,200 rotated-query ambiguities against the declared rivals. One pair
  duplication occurred (1,199 unique inputs among 1,200).
- Authority sync reports the selected source synchronized with execution parity;
  an older archival raw-code copy remains divergent and was not edited here.

## Verification state

Generator SHA-256:
`3653fb25d9b6b53e79b47c4d631394cf2c743a18bd2a586a5bf3f99aa115058b`.
The final 12-stage battery is all green, and the portable task-test snapshot
passes 15/15 tests. No Racket authority file changed.
## Current reviewer considerations

Source SHA-256: `3653fb25d9b6b53e79b47c4d631394cf2c743a18bd2a586a5bf3f99aa115058b`.

# Decision ledger — review-34f601b1f83910ae

## D1. Preserve the selected Racket authority

- **Original state:** the selected program already matched all three canonical
  pairs and rule smoke passed. An older archival raw-code copy is divergent, but
  it is not the selected authority.
- **Decision:** do not edit Racket; pin the normalized selected rule as
  `RULE_HASH = 9bb2dc983950` and use a Python mirror only for tests and rivals.
- **Alternatives considered:** rewrite the rule to forbid clipping/collisions, or
  synchronize the unrelated archival copy. Rejected because the observed defect
  was the input distribution, not canonical label authority, and task scope
  permits only justified rule changes.
- **Evidence/failure mode:** final authority sync and execution parity are green.
  Remaining limitation: arbitrary noncanonical grids can still expose boundary
  or overwrite behavior; the ordinary sampler deliberately avoids them.

## D2. Replace motif placement with constructive orbit placement

- **Prior choice:** v1.2.0 placed disconnected 3–5-cell motifs and then applied a
  cellwise rotation rule. The source comment suggests this was adapted from an
  earlier motif/gallery generator; the exact original rationale is unknown.
- **New choice:** enumerate complete four-position orbits around a margin-safe
  anchor, sample distinct orbit keys, and place one representative cell per key.
- **Why:** motif connectivity is irrelevant to the authority, while neighboring
  motif cells often alias under rotation or leave the grid.
- **Alternatives:** retain motifs and rejection-sample until footprints are clear;
  allow overlaps with explicit priorities; clip at edges. Constructive sampling
  was chosen because it is finite, deterministic, exact, and makes invalid states
  unrepresentable. Priority/clipping alternatives would need canonical or
  generated evidence that teaches those semantics.
- **Evidence:** baseline versus final 3,000-draw probe: clear grids 46→3,000;
  clipping 2,668→0; cross-color duplicate orbits 1,822→0.

## D3. Publish only observable exact axes

- **Prior choice:** nine axes included dead palette/texture aliases, fixed-token
  controls, and degenerate fixtures advertised as ordinary data.
- **New choice:** `grid_h`, `grid_w`, `n_cells`, and `n_colors` only, with global
  exact ranges and strict unknown-key rejection. Remove helpful/degenerate
  textures from the ordinary API.
- **Why:** controls should describe independent observable properties, not metadata
  inherited from another generator.
- **Alternative:** keep compatibility aliases. Rejected because no existing
  task-specific tests or notes established a compatibility requirement, and the
  aliases obscured rather than controlled this rule.
- **Failure mode/limit:** `n_colors > n_cells` is impossible and is declared.

## D4. Adapt an unspecified dependent count instead of rejecting a partial override

- **Failed first implementation:** if `n_cells=2` was requested while a schedule
  default chose three colors, generation raised an incompatibility even though
  the caller did not request `n_colors`. Conversely, `n_colors=4` could collide
  with a two-cell canonical default.
- **Decision:** when only `n_cells` is explicit, cap the default color count;
  when only `n_colors` is explicit, raise the default cell count. Reject only an
  explicitly requested pair with `n_colors > n_cells`.
- **Alternatives:** declare every partial combination incompatible, or silently
  violate the explicit value. Both defeat exact controls.
- **Evidence:** a new red test failed in all three bands, then passed; the shared
  override matrix is green in isolation and in the final battery.

## D5. Use a four-slot teaching schedule

- **Profiles:** canonical two-seed, multicolor off-center A, multicolor
  off-center B, canonical three-seed.
- **Decision:** every four consecutive materialized pairs contain two multicolor
  and two off-center counterexamples. With three demonstrations, holding out any
  one pair still leaves evidence against each named shortcut.
- **Why:** all canonical pairs use one seed color, so `first_color_only` and
  `monochrome_first_color` reproduce every canonical answer. A purely canonical
  schedule cannot distinguish them.
- **Alternatives:** random multicolor occurrence or one adversarial slot per
  period. Rejected because a query could remove the only refuting example.
- **Evidence:** focused tests exhaust 25 cyclic starts × 4 query positions in
  each band. The source-bound census found 0/300 production ambiguities and
  0/1,200 rotated-query ambiguities against the declared rivals.
- **Limit:** this is finite rival coverage, not proof against all hypotheses.

## D6. Declare executable rivals and witnesses

- **Rivals:** `first_color_only`, `monochrome_first_color`, `half_turn_only`, and
  `center_anchor_only`.
- **Witnesses:** multiple colors, an anchor whose location changes the answer,
  and necessity of quarter turns.
- **Decision:** connect every witness to the rival(s) it claims to refute and
  score the same rivals in `lesson_identifiable`.
- **Why:** presence-only morphology is not evidence that a wrong rule predicts a
  different label.
- **Evidence:** final semantic gate accepts all 3 canonical inputs, reports
  strict 600/600, all 3 witnesses firing, all 3 rival claims verified, 12/12
  smoke lessons identifiable, and 0/48 diagnostic query rotations ambiguous.

## D7. Retain a source-bound probe and minimal historical counterexample

- **Decision:** add `workspace/orbit_integrity_probe.py` and a baseline fixture
  at `counterexamples/review-34f601b1f83910ae-v0001/`.
- **Why:** the shared gates did not directly expose the core geometric aliasing,
  and future agents need to compare arbitrary historical source files without
  trusting their `self_check`.
- **Evidence:** the probe is covered by focused tests, records source hashes and
  replay seeds, and the fixture contains both five clipped seeds and two
  cross-color duplicate orbits.
- **Limit:** it is task-specific and should not be generalized without an
  explicit conflict-policy hook.

## D8. Stop conditions and unresolved limits

Work stopped after the final generator hash passed all 12 battery stages, 15
portable task tests, the 3,000-draw orbit census, the 300-lesson/1,200-rotation
census, and the exposed visible solve. The exact provisional patch then passed
`git apply --check`, applied in an isolated fresh extraction, reproduced the
final and frozen-solve hash, and passed 15/15 focused plus 15/15 wrapped task
checks there. No Racket source changed. The curriculum
does not cover intended collision priority, clipped-edge semantics, more than
six seed cells, or undeclared rivals; those remain out of scope rather than
claimed solved.
