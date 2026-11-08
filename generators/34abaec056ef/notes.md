# Current account: 34abaec056ef

## Intended rule

Locate the unique color-2 origin and the adjacent color-3 and color-4 cells.  The
vectors `2→3` and `2→4` define ordered local coordinates.  Return a fixed 3×3
grid whose cell `(row, col)` is color 8 exactly when the input contains color 8
at local coordinate `(col-1, row-1)`.  Other colors and color-8 cells on the
radius-2 ring are ignored.  The selected canonical Racket authority is unchanged
and pinned by `RULE_HASH = 8623727f72da`.

## Repair decisions

The imported 1.5.0 generator exposed diagonal bases, swallowed unknown controls,
accepted invalid scalar types, advertised mostly dead controls and never produced
the canonical 9×9/five-color profile.  Its distractors were kept outside the
3×3 local window, so the strongest canonical-fitting rival—“mark every occupied
non-frame local cell, regardless of color”—also fit ordinary generated lessons.

Version 2.0.0 replaces that design with:

- the eight ordered **cardinal orthogonal** frames accepted by the authority;
- seven strict, observable controls (`grid_h`, `grid_w`, `orientation`,
  `n_markers`, `n_outer_markers`, `n_local_distractors`,
  `n_exterior_distractors`) and rejection of unknown/non-integral controls;
- constructive placement for the full declared cross-product;
- a four-sample schedule containing one clean 9×9/five-color profile and three
  local ignored-color witnesses;
- a deterministic 62-output default sweep, covering every nonempty/non-full
  subset of the six available local cells in the standard lint horizon;
- executable self-check, override observer, independent Python mirror, declared
  rival/witness contracts and lesson-identifiability checks.

This reverses the prior implicit decision to treat diagonal 2-3-4 arrangements
as interchangeable with the canonical cardinal frame.  A live Racket probe showed
that such inputs do not implement the intended local-coordinate interpretation,
so they are excluded rather than taught as broad support.

## Strongest shortcut and retained witness

All three canonical pairs are also fit by the rival that maps **any** occupied
non-frame local cell to output color 8.  The retained lawful 9×9 witness puts
color 5 at local `(-1,-1)` and color 8 at `(1,-1)`.  The selected Racket rule
returns only a top-right 8; the rival also returns a top-left 8.  See
`counterexamples/color-agnostic-local-cell.json` and
`checks/shortcut-witness/racket.json`.  Production witness slots emit this class
of distinction through `n_local_distractors=1`.

## Known limits

- The semantic claims are finite and source-bound: one named canonical-fitting
  rival plus the checker’s bounded searched candidates are not a proof of unique
  induction against every possible program.
- Generated color-8 support is intentionally restricted to the six free cells of
  the local 3×3 window plus a radius-2 ring; the authority may execute on broader
  inputs that are outside this training domain.
- The curriculum is ordered in four-sample windows.  Query-rotation and fixed-seed
  schedule evidence are retained separately; neither establishes every seed or
  undeclared rival.
- Difficulty changes dimensions and nuisance density, not the semantic operation.
## Current reviewer considerations

Source SHA-256: `bc8a2d1e37c1551c3f666c4b572f2a06fd3aafbb99f60dbb6de277388b7b9c2c`.

# Decisions for 34abaec056ef

## D1 — Preserve the selected Racket authority

**Original state.** The selected rule already matched all canonical labels and
rule-smoke/authority checks.  An archival base copy diverges, but the selected
canonical authority is internally synchronized.

**Choice.** Do not edit Racket.  Pin `RULE_HASH = 8623727f72da` and repair only
the input distribution and contracts.

**Alternatives rejected.** Broadening or rewriting the rule would change task
authority without a reproduced rule defect.  Treating the archival divergence as
permission to edit the selected rule was also rejected.

**Evidence/limits.** Before and after authority-sync and real-Racket parity logs.
Passing parity covers canonical and generated probes, not arbitrary malformed
inputs.

## D2 — Cardinal frames only

**Original state.** Version 1.5.0 sampled diagonal “basis” vectors even though the
canonical pairs use cardinal adjacent 2-3-4 frames.

**Choice.** Enumerate the eight ordered orthogonal unit-cardinal bases.  Reject
diagonal, duplicate or missing frame cells in `self_check`.

**Alternative rejected.** Keeping diagonal inputs as augmentation.  A retained
manual Racket probe showed those coordinates are not interpreted by the selected
program as the intended frame geometry; teaching them would attach labels to a
misdescribed operation.

**Failure mode/limit.** This is a training-domain restriction.  It does not claim
the executable authority is undefined on every noncardinal input.

## D3 — Replace broad/dead metadata with seven exact controls

**Original state.** Unknown keys were swallowed; booleans/floats/strings and
negative call scalars were accepted; several advertised axes were dead or
partially ignored; grid overrides were clipped by difficulty.

**Choice.** Keep only dimensions, orientation and four observable object-count
controls.  Validate exact types/ranges before generation.  Explicit overrides use
the full declared domain in every band; defaults remain difficulty-aware.

**Alternative rejected.** Declare the broken combinations incompatible.  The
new placement is constructive, so the whole declared cross-product is feasible
and no incompatibility exception is needed.

**Evidence.** The red focused suite initially had 12 failures; final portable
task tests exercise every exact control in every band, invalid scalars, unknown
keys, freshness and RNG purity.

## D4 — Teach color selection inside the output window

**Original state.** Distractors were placed only outside the local 3×3 region,
leaving a color-agnostic occupancy shortcut unrefuted in canonical and generated
examples.

**Choice.** Use one clean canonical-profile slot followed by three slots with one
non-8 local distractor.  Keep a named rival, witness predicate and
`lesson_identifiable` hook in production code.  Four demonstrations are required.

**Alternatives rejected.** More remote distractors do not alter the shortcut’s
prediction.  Randomly hoping for a witness was rejected in favor of an ordered
schedule.

**Failure mode/limit.** The ordered schedule is evidence against the declared
rival.  Unlisted rivals remain unknown; arbitrary downstream reassembly must keep
at least one witness among the demonstrations.

## D5 — Cover the finite output alphabet deterministically

**Original state.** After the semantic repair, standard lint still observed only
45 of the 62 lawful output grids and correctly refused the finite-codomain
justification.

**Choice.** Enumerate all marker subsets of sizes 1..5 over the six free local
cells and choose default subset `(seed + sample_index) mod 62`.  Explicit
`n_markers` overrides still use seeded selection and remain exact.

**Alternative rejected.** Suppressing the warning with only
`EXPECTED_OUTPUT_CODOMAIN=62`.  A declaration without observed complete support
would hide a real schedule-coverage defect.

**Evidence.** The regression failed 45/62 before the change and passes 62/62
afterward; standalone lint is green.  This proves coverage only for the tested
default horizon and mathematical declared alphabet.

## D6 — Keep radius-2 color-8 markers as ignored geometric controls

**Choice.** Allow 0..4 color-8 markers only on the radius-2 ring and 0..4
non-8 distractors only beyond radius 2.  This tests clipping to the 3×3 local
window without colliding with the frame or local color-selection witness.

**Alternative rejected.** Arbitrary distant color-8 noise.  It adds little
semantic value and weakens the source-bound domain.

## D7 — Verification and acceptance policy

The truthful schedule-period declaration makes a standard battery emit
`declared_period_not_enumerated`.  I retained that failed standard run rather
than hiding it, then bound fixed-seed period enumeration and required query
rotations into a fresh final battery.  A separate 100-lessons-per-band census is
used for wider random support.  These checks remain finite.
