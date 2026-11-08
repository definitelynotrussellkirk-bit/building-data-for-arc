# Current generator notes: 1bfb2ef9ca71

## 2026-10-25 native parametric admission build

- Preserved the exact canonical `borders_only` Racket program and added the nearby episode-fixed `fill_largest_interior` setting.
- Sequential rule: construct every colored frame, then consume that intermediate by selecting the unique largest enclosed interior and filling it. The protected skip-A witness changes the final label.
- Inputs are matched across settings and prefix-stable for 3..6 demonstrations and 1..4 queries. The fourth query is a substantive 30×30 four-frame competition.
- The first lesson separates interior area from both perimeter and bounding-box area. A reusable `workspace/parametric/audit.py` checks six finite rivals on seeds 0, 17, and 97.
- Native qualification: 4 jobs / 40 protected-Racket evaluations passed. Public projection: 16 views; combined first-turn audit across both assigned families passed 32 views and 48 private-field invariance checks.
- Status is reviewer-ready only. Owner acceptance and training admission remain external.

## Authority and intended rule

The selected authority is unchanged and pinned by `RULE_HASH = a0ec8172be31`.
For each nonzero color appearing at exactly two diagonal cells, treat those cells
as opposite corners of an axis-aligned rectangle and paint that rectangle's
hollow border in the same color on a zero background.

Version `3.1.0` is bound to generator SHA-256
`1040eab6c06ff4c472af885bc51eb8c6ec94c8e33be5b04b246e303a238d275f`.
No canonical JSONL or Racket source was changed.

## Repaired decisions

### Exact public controls

**Prior choice:** version 2.1.0 advertised nine controls, including palette,
texture, density, position, and color-count aliases that were ignored or only
partially honored. It also accepted unknown keys.

**Current choice:** advertise only the three exact observable controls the
sampler can construct jointly: `grid_h=8..12`, `grid_w=7..14`, and
`rectangles=2..3`. Every Cartesian combination is legal. Calls reject unknown
axes and non-literal scalar types; explicit `None` remains equivalent to no
override. `observe_overrides` and `self_check(..., meta={"overrides": ...})`
make the contract executable.

**Evidence:** the final override gate accepted all 7,560 probes with zero
findings, and the task-local probe checked all 240 value combinations once
across the three bands (`checks/after-final/` and `checks/final-probe.json`).

### Geometry and endpoint orientation

**Prior choice:** the rejection sampler placed only upper-left/lower-right
endpoint pairs, even though the canonical data uses both diagonal orientations.
Crowded fallbacks also restricted shapes and made exact controls unreliable.

**Current choice:** constructive layouts place two rectangles in separated row
or column bands, or three rectangles in three gutter-separated quadrants.
Rectangles are 3..5 rows by 3..6 columns with at least one empty row or column
between inferred boxes. Every ordinary input includes both `NW-SE` and `NE-SW`
endpoint orientations. This removes rejection/fallback drift and keeps all
advertised combinations feasible.

### Canonical support versus broad support

Every difficulty band samples a canonical `(height, width, color-count)` profile
with probability 3/5, then samples a broader band-specific shape otherwise.
The final profile-floor result observed 37/60 exact canonical-profile hits and
38/60 envelope hits, with exact support in every band: easy 11/20, medium 10/20,
hard 16/20.

### Teaching schedule and canonical shortcut

All three canonical pairs have rectangle height three, so the strongest simple
source-bound rival is `fixed_height_three`: infer the correct columns but always
draw only a three-row border. It matches every canonical output.

The production schedule alternates two declared profiles:

- even `sample_index`: `canonical_height3`;
- odd `sample_index`: `height_variation`, constructively forcing at least one
  rectangle of height four or five.

`EXAMPLES_NEEDED = 3` and `LESSON_SCHEDULE_PERIOD = 2`; therefore every three-demo
window, and every query rotation of a consecutive four-pair bundle, retains at
least one taller-than-three demonstration. The executable rival, witness,
shortcut declaration, and `lesson_identifiable` hook enforce that claim.

The retained counterexample is
`counterexamples/fixed_height_three.json`: seed 731, sample index 1, medium. Its
four-row color-9 rectangle is painted through row 7 by Racket, while the rival
stops at row 6. The Python mirror matches the Racket output exactly.

## Validators and tests

`_analyze` is the common structural parser for `self_check`,
`strict_canonical_like`, witnesses, and override observation. `rule_mirror` is an
independent diagnostic mirror and matches all three canonical pairs; it is not
label authority. Seven portable task tests cover authority binding, exact joint
overrides, scalar rejection, schedule/rival refutation, replay/global-RNG
isolation, constructive support, and the retained counterexample seed.

Reusable authoring tools live in `workspace/`:

- `probe_generator.py` performs a finite replay/diversity census, exhaustive
  exact-axis checks, canonical checks, and all schedule/query rotations;
- `materialize_counterexample.py` regenerates the retained shortcut witness.

## Measured final evidence

- Final after battery: 12/12 stages green.
- Semantic gate: 600/600 strict draws; `non_three_height` witnessed in 408/600.
- Declared-period schedule census: all period residues and query positions pass.
- Larger lesson census: 300/300 lessons materialized, 1,200 labelled pairs,
  1,199 unique inputs, zero production ambiguities, and zero ambiguities in
  1,200 query rotations against the declared rival.
- Source-bound probe: 1,536 draws, 952 unique inputs, zero failures, 240 exact
  axis checks, and 24 schedule-rotation checks.

## Known limits

The lawful generated domain intentionally excludes collinear endpoints,
overlapping/touching rectangle boxes, single-rectangle scenes, heights outside
3..5, and widths outside 3..6. The semantic evidence refutes one explicit
canonical-fitting rival; it does not prove unique induction against every
possible rule. Finite seed probes do not exhaust the generator's random support.
## Current reviewer considerations

Source SHA-256: `1040eab6c06ff4c472af885bc51eb8c6ec94c8e33be5b04b246e303a238d275f`.

# Decisions for `1bfb2ef9ca71`

Final generator version: `3.1.0`
Final generator SHA-256: `1040eab6c06ff4c472af885bc51eb8c6ec94c8e33be5b04b246e303a238d275f`
Pinned rule hash: `a0ec8172be31`

## D1 — Keep the canonical authority unchanged

**Prior choice and rationale:** the selected Racket rule already reproduced all
three canonical pairs. The prior generator did not pin its hash, so its authority
binding was implicit.

**Current choice:** keep the canonical JSONL and Racket source byte-for-byte
unchanged and add `RULE_HASH = "a0ec8172be31"` to the generator.

**Alternatives rejected:** changing the rule to match generator-specific
restrictions would invert authority and would not address the generator defects.

**Probe/evidence:** final `authority_sync`, `rule_smoke`, and `racket_lint` stages
are green in `checks/after-final/`; the retained shortcut witness was labelled by
that same Racket hash in `checks/fixed-height-counterexample/racket.json`.

**Failure mode/limit:** the Python `rule_mirror` is diagnostic only. Racket remains
label authority.

## D2 — Advertise only exact observable controls

**Prior choice:** version 2.1.0 advertised many controls (`grid_h`, `grid_w`,
rectangle/color-count aliases, palette, texture, position, density) even though
several were ignored, dead, invalid, or incompatible with the rejection sampler.
The original rationale for this broad surface is unknown.

**Current choice:** expose only:

- `grid_h`: every literal integer 8 through 12;
- `grid_w`: every literal integer 7 through 14;
- `rectangles`: literal integer 2 or 3.

All three controls are jointly constructive. Unknown keys, booleans, floats,
strings, negative sample indices, and invalid difficulty values fail closed.
Explicit `None` means “use the scheduled default.” `observe_overrides` provides
an executable observation contract.

**Alternatives rejected:**

1. Keep the old axes and label them diagnostic. Rejected because callers would
   still see a misleading public contract.
2. Preserve palette/color aliases. Rejected because the number of distinct
   colors is exactly the rectangle count; duplicate aliases add ambiguity.
3. Declare many incompatibilities. Rejected because the small exact Cartesian
   domain is simpler and stronger.

**Probe/evidence:** the override gate accepted 7,560/7,560 probes with zero
findings or warnings, and rejected the unknown-key probe. The task-local probe
checks all 240 axis value/band combinations. Evidence:
`checks/after-final/checks/1bfb2ef9ca71_after_override_results.json` and
`checks/final-probe.json`.

**Failure mode/limit:** controls outside the declared ranges are intentionally
unsupported rather than silently approximated.

## D3 — Replace rejection/fallback placement with constructive geometry

**Prior choice:** random rectangle proposals were retried and then fell back to
restricted patterns. This made exact controls unreliable and coupled successful
output distribution to retry luck.

**Current choice:** construct layouts directly:

- two rectangles use vertically or horizontally separated bands;
- three rectangles occupy three of four gutter-separated quadrants;
- every pair of inferred boxes has at least one empty row or column between it;
- rectangle heights are 3–5 and widths are 3–6.

**Alternatives rejected:**

1. Increase retry count. This would reduce but not remove fallback drift.
2. Allow touching or overlapping rectangles and define paint precedence. That
   would add a second composition problem absent from the intended lesson.
3. Generate one rectangle. The canonical task uses multiple simultaneous color
   bindings, and one rectangle would support a simpler shortcut.

**Probe/evidence:** 1,536 source-bound draws over 64 seeds, 8 indices, and three
bands had zero generation, self-check, replay, or global-RNG failures. The final
strict semantic census accepted 600/600 draws.

**Failure mode/limit:** the generated domain excludes touching/overlapping boxes,
collinear endpoint pairs, and one-rectangle scenes. That is a deliberate domain
choice, not a claim about the full mathematical authority.

## D4 — Make diagonal endpoint orientation visibly non-semantic

**Prior choice:** every generated rectangle used only the upper-left and
lower-right corners, although canonical pairs contain both diagonal orientations.
The rationale is unknown.

**Current choice:** every ordinary input with two or three rectangles includes
both `NW-SE` and `NE-SW` endpoint orientations; a third rectangle chooses either.
The output is invariant to which diagonal marks the same bounding box.

**Alternatives rejected:** random independent orientation without a per-input
coverage guarantee. It would eventually sample both orientations but could still
produce lessons in which orientation appears spuriously semantic.

**Probe/evidence:** the source-bound probe and portable schedule test assert both
orientations across ordinary generated examples. The retained shortcut witness
itself contains one rectangle of each orientation.

**Failure mode/limit:** orientation is balanced structurally, not statistically
forced to exactly 50/50 across long runs.

## D5 — Weight canonical profiles without collapsing the broader domain

**Prior choice:** band-specific shapes made canonical exact profiles sparse and
left the hard band at 0/20 exact hits in the baseline profile-floor sample.

**Current choice:** every band draws one of the three canonical
`(height, width, color-count)` profiles with probability 3/5. The remaining 2/5
uses broader band-specific shapes. Canonical draws use two rectangles; broad draws
use two or three with difficulty-dependent weighting.

**Alternatives rejected:**

1. Canonical profiles only. This would overfit shape and color count.
2. Uniform sampling over every grid shape. It would make exact canonical support
   unnecessarily weak and less reproducible.
3. Separate override domains by band. Exact controls should mean the same thing
   at every difficulty.

**Probe/evidence:** final profile floor: exact 37/60 and envelope 38/60; exact
support easy 11/20, medium 10/20, hard 16/20.

**Failure mode/limit:** the 3/5 probability is a curriculum choice, not a fitted
estimate of a natural ARC distribution.

## D6 — Explicitly refute the canonical-fitting fixed-height shortcut

**Observed shortcut:** all three canonical demonstrations use rectangles exactly
three rows tall. `fixed_height_three` therefore fits every canonical pair while
failing on a taller rectangle.

**Current choice:** declare that rival in `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS`, and `SEMANTIC_RIVALS`; declare `non_three_height` as its
witness; and use a period-2 schedule:

- even `sample_index`: `canonical_height3`;
- odd `sample_index`: `height_variation`, with at least one height-four or
  height-five rectangle.

Set `EXAMPLES_NEEDED = 3`. Every three consecutive demonstrations therefore
contain a refuting odd sample. Every held-out query rotation of a four-pair bundle
still leaves at least one refuting demonstration.

**Alternatives rejected:**

1. Depend on random taller rectangles. A complete lesson could still miss them.
2. Use two demonstrations. Two examples can work for this rival but provide less
   redundancy and diverge from the requested/default three-example policy.
3. Force every rectangle tall. That would replace the original height-three
   shortcut with an “always tall” shortcut and weaken canonical support.
4. Resample lessons until a witness appears. A deterministic small schedule is
   easier to audit and replay.

**Probe/evidence:** the retained seed-731/sample-index-1 counterexample is labelled
by Racket and differs from the rival. The strict gate observed the witness 408/600
times; the period census checked both residues. The 300-lesson census found zero
production ambiguity and zero ambiguity across 1,200 query rotations. The custom
probe checks all 24 band/residue/query combinations.

**Failure mode/limit:** this establishes coverage against the named rival and the
bounded searched rivals only. It is not a proof of unique induction.

## D7 — Centralize structural analysis and keep the mirror non-authoritative

**Prior choice:** generator validation was weaker and did not expose a common
structural representation or semantic declarations.

**Current choice:** `_analyze` is the single parser for grid shape, color endpoints,
boxes, orientations, and structural errors. `self_check`,
`strict_canonical_like`, `observe_overrides`, witnesses, and rivals reuse that
analysis. `rule_mirror` independently constructs intended output for diagnostics
and lesson-hook checks.

**Alternatives rejected:** duplicate parsing in each hook, which would allow the
validator, rival, and observer to disagree silently.

**Probe/evidence:** seven portable task tests bind canonical authority, exact
controls, invalid scalar rejection, schedule semantics, deterministic replay,
constructive support, and the retained counterexample seed. The mirror matches
all canonical pairs and the Racket-labelled counterexample.

**Failure mode/limit:** sharing `_analyze` reduces inconsistent parsing but creates
a common parser dependency. Racket comparison on the retained witness and the
canonical pairs guards the most important consequence.

## D8 — Build reusable authoring tools rather than one-off prose

Added:

- `workspace/probe_generator.py`: deterministic replay/diversity, exact axes,
  canonical mirror/rival checks, and every declared schedule rotation;
- `workspace/materialize_counterexample.py`: regenerates the exact fixed-height
  witness and writes Racket-input evidence;
- seven portable task tests under the selected task.

The probe reads declarations from the selected module rather than maintaining a
second rival-name list.

**Limit:** these are finite source-bound diagnostics, not exhaustive formal proofs.

## D9 — Preserve solve and audit separation

The pre-repair blind solve was completed before opening the assigned source. The
post-repair solve was prepared from final generator bytes and used only visible
examples during solving; prior rule exposure was declared honestly. Audit targets
`3d0427aad724` and `109a03554ed3` were not edited. Exact Racket-labelled audit
witnesses are retained under `checks/audit/`.
