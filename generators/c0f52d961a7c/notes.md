# Working notes: c0f52d961a7c

## 2026-09-28 review

The imported `2.0.0` generator had a sound core scene but an inaccurate public
contract. It omitted `RULE_HASH`, declared inert/singleton/dead axes, exposed
negative fixtures as ordinary textures, ignored or clamped exact overrides,
accepted unknown keys, had no realized-axis observer, generated no
canonical-profile rows in a 60-draw probe, and declared no semantic contract.
The baseline battery ended at 7 green, 2 advisory, and 3 failed stages.

The canonical Racket authority was not the problem. Its canonical, selected,
and archival copies were byte-equivalent after normalization, shared rule hash
`0f51670bbbc2`, and solved all three canonical pairs. No rule source was edited.

The generator was rewritten as `3.0.0` around four live exact axes only. A
four-slot teaching schedule covers all marker colors and places the marker on a
spatial side inconsistent with the requested move. Explicit connected
polyomino catalogs cover sizes 3 through 8. A full border around the payload
keeps the entire override Cartesian product constructible. Canonical-size
anchors occupy half of each eight-index block; the other half samples the full
canvas range.

Semantic safeguards now name and test five rivals: follow marker position,
move away from marker, do not shift, always move left, and rotate the color
key. Eight witnesses and `lesson_identifiable` require four-demo lessons to
eliminate those rivals. The strongest canonical shortcut, follow marker
position, has a generated exact counterexample and is checked against the real
Racket program.

Regression tests cover rule pinning, canonical parity, the complete four-color
teaching block, exact and composable overrides, unknown-key rejection,
semantic rival refutation, deterministic/fresh/global-RNG-neutral replay, and
canonical-anchor plus broad-range support.

After repair, the full 12-stage generator battery is green. Known scope limit:
the curriculum intentionally teaches one connected 3..8-cell payload and one
marker. The authority can mechanically process malformed or broader inputs,
but those are not claimed as part of the teaching distribution.
## Current reviewer considerations

Source SHA-256: `3fd0e0e9b95eb3ce66e47ebb31d2892815b1af95fcaa31d11b564f6a634942c4`.

# Decisions: c0f52d961a7c

## D1 — Preserve the Racket authority

**Input choice.** Leave the canonical and selected Racket sources unchanged and
pin the generator to `RULE_HASH = "0f51670bbbc2"`.

**Original rationale.** Unknown, but the retained source directly implements
the written rule.

**Alternatives considered.** Rewrite or simplify the Racket; add guards for
missing/multiple markers; clip differently at borders.

**Probe.** Authority sync found canonical, selected, and archival sources in one
exact/normalized group; execution solved all three canonical pairs. Rule smoke
also found 120/120 Python-mirror parity.

**Failure modes / limits.** The authority assumes at least one marker and uses
the first if malformed inputs contain several. The generator prevents those
inputs, so broadening authority semantics was unnecessary.

## D2 — Remove fake axes instead of preserving compatibility theater

**Input choice.** Retain only `grid_h`, `grid_w`, `payload_size`, and
`marker_color` as override axes. Remove palette, position-bias, density, and
texture axes that had no lawful behavioral alternatives.

**Original rationale.** The imported generator appears to have inherited a
broad generic axis template. Several axes were singleton, ignored, or aliases.

**Alternatives considered.** Mark inert fields diagnostic; invent cosmetic
palette/texture changes; keep negative fixtures in the normal domain.

**Probe.** Baseline lint and defect lint identified singleton, unprobed, dead,
and domain-overlap axes. The repaired linter reports 0 errors and 0 warnings.

**Failure modes / limits.** Callers using undocumented removed keys now receive
a loud unknown-override error. That is preferred to silently returning a grid
that does not honor the request.

## D3 — Make the remaining override product exact

**Input choice.** Every declared override is independently exact and the full
Cartesian product is constructible. Add keyed provenance and
`observe_overrides`.

**Original rationale.** Unknown; the baseline accepted values it later ignored
or clamped.

**Alternatives considered.** Declare incompatibility pairs; silently clamp
large payloads; allow best-effort overrides.

**Probe.** The strict override matrix accepted 55,620 draws across 618 cases
with zero findings or warnings, including boundaries and mixed combinations.
Unknown keys are rejected.

**Failure modes / limits.** Axis values are intentionally integers only;
booleans are rejected despite Python’s `bool` subclassing `int`.

## D4 — Use a four-slot complete color-key schedule

**Input choice.** Set `EXAMPLES_NEEDED = 4` and assign one marker color to each
slot in left/up/right/down order.

**Original rationale.** The canonical training set exposes only colors 2 and 1,
leaving colors 3 and 4 underdetermined without a broader curriculum.

**Alternatives considered.** IID marker colors; two-example lessons mirroring
the canonical train count; random coverage with rejection until all colors
appear.

**Probe.** Every consecutive four-slot aligned block covers all four colors;
12/12 generated lessons were identifiable in the semantic gate.

**Failure modes / limits.** A lesson builder that ignores `EXAMPLES_NEEDED` and
uses fewer examples may not see the complete key.

## D5 — Anti-correlate marker location with commanded direction

**Input choice.** Place the marker right/below/above/left for the
left/up/right/down commands respectively.

**Original rationale.** The canonical examples accidentally permit the
spatial rival “move toward the marker.”

**Alternatives considered.** Uniform marker position; marker always adjacent;
marker placed on the same side as motion.

**Probe.** The `marker_position_shortcut_refuted` witness fires throughout the
600-draw semantic census. An exact generated example is checked against the
canonical Racket authority in `checks/tests/shortcut_counterexample.json`.

**Failure modes / limits.** The schedule is deliberately adversarial rather
than an unbiased model of marker location. That is appropriate for teaching
the color code but should remain documented.

## D6 — Use explicit connected polyominoes and a one-cell margin

**Input choice.** Build a finite shape catalog for sizes 3..8 from hand-checked
seeds and all D4 transforms; place it with one blank border cell on every side.

**Original rationale.** The baseline’s fixed shape family did not honor
`payload_size` and could not support the declared product honestly.

**Alternatives considered.** Random-walk polyomino generation; arbitrary filled
rectangles; generate then reject/clamp on difficult combinations.

**Probe.** Import-time assertions check cell counts; `self_check` checks one
4-connected payload; boundary override tests exercise all sizes and all four
directions.

**Failure modes / limits.** The finite catalog is diverse but not the complete
set of free polyominoes of each size. Completeness is unnecessary for the rule.

## D7 — Mix canonical anchors with full-range exploration

**Input choice.** Indexes with `sample_index % 8 < 4` use scheduled canonical
canvas sizes; the other four indexes sample the full declared ranges.

**Original rationale.** The baseline had 0/60 canonical-profile support, but
forcing all outputs to canonical sizes would make the broad axes dishonest.

**Alternatives considered.** Always canonical; fully random dimensions;
probabilistic anchors driven by RNG.

**Probe.** Profile floor records 26/60 exact hits and nonzero support in every
band; the axis-span regression reaches at least height 15 and width 17.

**Failure modes / limits.** Very narrow sampling of only the first four indexes
will not observe the larger sizes.

## D8 — Encode semantics as executable rivals and witnesses

**Input choice.** Add a pure mirror, five rivals, eight witnesses,
`CANONICAL_SHORTCUTS`, and a lesson-identifiability hook.

**Original rationale.** Unknown; the imported module had no semantic contract.

**Alternatives considered.** Rely only on structural checks; document shortcuts
in prose; compare only to the canonical outputs.

**Probe.** Semantic gate: 600/600 strict draws, all witnesses present, and
12/12 lessons identifiable. Regression tests independently require each witness
to expose its named rival.

**Failure modes / limits.** Rival sets can never enumerate every possible bad
hypothesis. These cover the strongest rule-local alternatives observed here.

## D9 — Keep generation deterministic and side-effect free

**Input choice.** Route all variability through `gen_ctx` and keyed draw RNGs;
return newly allocated grids.

**Original rationale.** Reproducibility is required by the packet contract.

**Alternatives considered.** Module-global `random`; mutable shape caches; one
shared returned grid.

**Probe.** Regression tests verify replay equality, distinct object identity,
row freshness, re-entrancy, and no change to Python’s global RNG state. Rule
smoke found no input mutations or stateful replay differences.

**Failure modes / limits.** Results intentionally change when `VERSION`
changes, because version is part of the deterministic draw namespace.

## D10 — Add targeted regression tests and retain raw evidence

**Input choice.** Add one task-local test module and preserve before/after
battery receipts, focused logs, exact Racket counterexamples, and adversarial
audit census data.

**Original rationale.** The baseline had no task-local regression suite.

**Alternatives considered.** Depend only on the generic battery; add broad
shared tests; provide prose-only review notes.

**Probe.** The focused suite is 6/6 green and the 12-stage after battery is
all green.

**Failure modes / limits.** The tests protect the current declared interface;
future intentional interface changes must update both code and tests.
