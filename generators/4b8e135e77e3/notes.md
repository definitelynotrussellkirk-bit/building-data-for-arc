# Working notes: 4b8e135e77e3

## Final state

- Generator version: `3.0.0`
- Final SHA-256: `4645fe070721cb36387bbf6907d3d2d9daea97fe99596895cc6c2fbc4f64c1b7`
- Canonical `RULE_HASH`: `a44e14a9fb6c`
- Racket authority: unchanged
- Training approval: unchanged/unverified

## Baseline findings

The selected 2.0.1 source was not a usable exact generator contract. It omitted `RULE_HASH`; advertised a dead singleton density axis and invalid texture modes; accepted unknown override keys; declared domains that the difficulty-specific draws rejected or silently changed; had zero canonical-profile support in the 60-draw profile check; and declared no semantic witnesses or rivals. The baseline override check recorded 15,655 findings across 62,100 draws / 690 cases, including 4,860 dimension mismatches, 9,180 self-check failures, and 1,590 generation errors. See `checks/before-*`.

A simple 60-draw probe also found 18 inputs whose output barely differed from the input. The old texture axis was removed rather than papering over modes that did not construct legal task inputs.

## Construction decisions

### Exact observable controls

The sampler now accepts only:

- `grid_h`: 7–16
- `grid_w`: 7–18
- `k_rot`: 1–4
- `shape_size`: 2–8
- `palette_kind`: `canonical | monochrome | multicolor`
- `tally_layout`: `prefix | scattered`

All controls are jointly constructible. `observe_overrides()` recovers their realized values from the grid, unknown keys fail explicitly, and generated inputs are revalidated before return.

### Geometry

The anchor is placed with radius-two clearance from every boundary and below the tally row. Shapes use offsets in a 5×5 neighborhood. Offset `(1, 0)` is mandatory while its three quarter-turn partners are excluded from the source; therefore every additional requested orientation contributes at least one genuinely new output cell. The remaining offsets are sampled without replacement, preserving shape diversity while preventing the weak no-op behavior measured in the baseline.

### Default distribution

Half of default indices use 7×7 or 9×9 canvases, preserving canonical-profile support; the other half span difficulty-specific ranges. Default `K` cycles through 2, 3, and 4. `K=1` remains available through the exact override but is not a default because it teaches a much weaker, near-copy transformation.

The final four-profile cycle is:

1. `prefix_canonical`
2. `scattered_monochrome`
3. `prefix_multicolor`
4. `scattered_multicolor`

Every cyclic two-draw window contains a scattered non-6 example. This refutes the direct `prefix_tally_only` and `color6_only` shortcuts and the conditional `palette_gated_tally` and `layout_gated_shape` shortcuts.

### Cross-axis regression found during self-review

An intermediate schedule alternated scattered/color-6 with prefix/non-6 examples. It passed the standard semantic gate but admitted a conditional rule: “use prefix tally on non-6 shapes, otherwise count all tally cells.” The test in `checks/tdd-cross-axis-red.log` failed in easy, medium, and hard before the fix. The final schedule breaks this correlation, declares both conditional rivals, and tests all 24 cyclic starts in each difficulty band.

### Labels and authority

The generator creates inputs only. Labels remain sourced from the canonical Racket authority. `workspace/reference_probe.py` contains an independent row-major Python oracle solely for audits/tests; `--racket` requires real authority parity and never falls back.

## Final measurements

All measurements below bind to generator SHA-256 `4645fe070721cb36387bbf6907d3d2d9daea97fe99596895cc6c2fbc4f64c1b7`.

- Full after battery: 12/12 stages green.
- Portable task tests: 49 passed with Racket available.
- Exact override matrix: 54,180/54,180 accepted draws, 602 cases, 0 findings, 0 warnings; unknown key rejected.
- Profile floor: 26/60 exact canonical-profile hits, at least 5 in every band; 0 crashes.
- Semantic gate: 600/600 strict inputs, all four canonical-fitting shortcuts covered by executable witnesses.
- Lesson census: 300/300 lessons materialized, 1,200 unique inputs, zero ambiguity/hook warnings/scoring errors; every rival refuted in 100/100 lessons per band.
- Independent audit: 1,000 deterministic valid inputs, 1,000 transformed outputs, all four rivals disagreed on their scheduled witnesses, and 35/35 Python outputs matched Racket.

## Remaining limitations

The rival set is finite, so the results do not prove universal identifiability. Default motifs are radius-two and all quarter-turns stay in bounds; clipping is supported by the authority but intentionally absent from the generated teaching domain. Default `K` omits 1, though the exact override covers it. Collision ownership between differently colored rotated cells is authority-defined and parity-tested, but the sampler's protected witness avoids relying on a collision to demonstrate the rule.

Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `4645fe070721cb36387bbf6907d3d2d9daea97fe99596895cc6c2fbc4f64c1b7`.

# Decisions for `4b8e135e77e3`

Final generator SHA-256: `4645fe070721cb36387bbf6907d3d2d9daea97fe99596895cc6c2fbc4f64c1b7`.

## D1 — Keep the Racket authority unchanged

**Decision.** Pin `RULE_HASH = "a44e14a9fb6c"` and repair only the input sampler.

**Rationale.** The canonical examples and the selected Racket authority agree: count all color-1 cells in row 0, rotate every color-2..8 motif cell around the unique color-9 anchor for the first `K` clockwise quarter-turns, and clear unrelated input marks. Rule smoke, grammar, Racket lint, authority sync, 35 independent parity cases, and canonical-pair checks all passed.

**Rejected alternative.** Editing the authority to fit baseline generator artifacts. The defects were in generated inputs and metadata, not label semantics.

**Failure mode.** A future authority change would invalidate the pin. The battery's rule smoke and authority sync are retained to catch that.

## D2 — Replace the advertised axis contract rather than preserve invalid texture modes

**Decision.** Expose only six exact, observable, jointly constructible controls: `grid_h`, `grid_w`, `k_rot`, `shape_size`, `palette_kind`, and `tally_layout`.

**Rationale.** Baseline texture values produced empty/invalid grids or had no observable effect, while declared dimension and difficulty domains disagreed. Keeping them would make exact overrides fictional. `observe_overrides()` gives a direct postcondition for every surviving axis.

**Alternatives considered.** Repair each old texture token; mark dead controls diagnostic; keep difficulty-specific incompatibilities. These added complexity without teaching the rule and would leave large regions of the declared cross-product unusable.

**Probe.** Final override matrix: 602 cases, 54,180 draws, every draw accepted and observed exactly; unknown key rejected.

**Limitation.** The new contract intentionally has no incompatibility declarations. Future axes must remain jointly constructible or declare precise incompatibilities.

## D3 — Use canonical anchors plus banded size diversity

**Decision.** Default index residues 0 and 1 use 7×7 and 9×9; the other half draw from difficulty-specific 7–16 × 7–18 ranges.

**Rationale.** The baseline had zero canonical-profile support. Deterministic canonical anchors guarantee support while leaving half the schedule available for broader dimensions.

**Rejected alternatives.** All-canonical dimensions would overfit size. Pure random dimensions could again miss profile-floor samples. A post-hoc retry loop would obscure exact sampling.

**Probe.** Final profile floor: 26/60 exact hits, with 11 easy, 10 medium, and 5 hard; zero crashes.

**Limitation.** Canonical-size frequency is intentionally high. It is a teaching distribution, not a claim about a natural task prior.

## D4 — Default `K` uses 2, 3, and 4; exact override retains 1

**Decision.** Cycle default `K = 2 + sample_index % 3`; allow exact `k_rot=1..4`.

**Rationale.** `K=1` mostly copies the motif while erasing the cue row and is a weak demonstration of rotation. Values 2–4 make the rule's iterative structure visible. Exact override coverage preserves the full lawful domain.

**Rejected alternative.** Uniform 1–4 defaults. It spends 25% of examples on a weak transformation and makes two-example lessons less informative.

**Failure mode.** A learner may see few natural `K=1` cases. This is documented; override-based evaluation covers it.

## D5 — Radius-two geometry with a protected asymmetric witness

**Decision.** Place the anchor with radius-two clearance and sample 2–8 unique motif offsets inside a 5×5 neighborhood. Always include `(1,0)` and exclude its other three quarter-turn locations from the source motif.

**Rationale.** This makes all rotations lawful and guarantees each additional quarter-turn contributes a fresh cell. It directly fixes weak/no-op examples without deriving labels in Python.

**Alternatives considered.** Arbitrary-radius shapes with clipping; rejecting weak examples after label execution; forcing every source offset to have no rotational partner. Clipping complicates induction, label-dependent rejection couples the sampler to authority execution, and globally forbidding rotational relations needlessly reduces shape diversity.

**Probe.** Independent audit: 1,000/1,000 outputs transformed; zero self-check failures; 35/35 Racket matches.

**Limitations.** Generated lessons do not teach clipping or large-radius motifs. Other source cells may be rotationally related; only the protected witness is guaranteed fresh.

## D6 — Preserve three palette modes

**Decision.** Support `canonical` (all 6), `monochrome` (one non-6 color), and `multicolor` (at least two colors, with a non-6 protected witness).

**Rationale.** The canonical examples alone admit a color-6-only shortcut. Monochrome and multicolor non-6 shapes refute it while testing color preservation independently of geometry.

**Rejected alternatives.** Always use color 6; random unrestricted colors without a guaranteed non-6 witness. Both can leave the shortcut unrefuted by chance.

**Probe.** Final semantic gate observed 454/600 noncanonical-color witnesses; `color6_only` was refuted in every lesson in the 300-lesson census.

## D7 — Treat tally placement as a count, not a prefix

**Decision.** Support both `prefix` and guaranteed-nonprefix `scattered` layouts.

**Rationale.** Canonical examples admit a leading-prefix interpretation. Scattered tallies demonstrate that all row-0 ones count.

**Rejected alternatives.** Prefix-only tallies; arbitrary random columns without rejecting the prefix set. The former teaches the shortcut; the latter can accidentally fail to supply the witness.

**Probe.** Final semantic gate observed 307/600 scattered witnesses; `prefix_tally_only` was refuted in every census lesson.

## D8 — Require a joint cross-axis witness in every two-example window

**Decision.** Use the four-profile cycle:

1. `prefix_canonical`
2. `scattered_monochrome`
3. `prefix_multicolor`
4. `scattered_multicolor`

Every odd residue is both scattered and non-6. Therefore every cyclic pair of consecutive examples contains a joint witness.

**Original intermediate decision and failure.** The first repaired schedule used `prefix_monochrome`, `scattered_canonical`, `prefix_multicolor`, `scattered_canonical`. It covered each direct witness but correlated palette and tally layout. The conditional rival “use prefix tally only for non-6 shapes” fit every generated default. `checks/tdd-cross-axis-red.log` reproduces the failure in all bands.

**Alternatives considered.** Randomly mix both axes; rely on pooled witness counts; use separate direct witnesses in every pair. Random mixing gives probabilistic gaps. Pooled counts do not establish lesson identifiability. Separate witnesses can remain correlated.

**Probe.** Task tests cover 24 cyclic starts × 3 bands. The 300-lesson census refutes `prefix_tally_only`, `color6_only`, `palette_gated_tally`, and `layout_gated_shape` in 100/100 lessons per band.

**Limitation.** These four rivals are plausible and reproducible, not exhaustive. A future shared gate should synthesize simple conditional compositions automatically; see F1.

## D9 — Fail loudly on invalid construction and malformed overrides

**Decision.** Validate override keys/types/ranges before drawing; run `self_check()` on every constructed grid; return diagnostics rather than exceptions for malformed candidate grids where possible.

**Rationale.** Invalid examples must never silently enter a training corpus. Exact controls need explicit failure rather than implicit clamping or ignored keys.

**Probe.** Mutation tests cover erased tally, extra anchor, shape/tally row violations, clipping, invalid colors, malformed rectangularity, and type errors.

## D10 — Build an independent reusable probe

**Decision.** Add `workspace/reference_probe.py` with a row-major oracle, declaration-driven rival census, deterministic sampling, and optional mandatory Racket parity.

**Rationale.** Generator-local helper functions can share the same bug as construction. The probe independently implements the transformation and reports source hashes. `--racket` has no Python fallback.

**Probe.** Final report: 1,000 samples, 1,000 distinct inputs, zero self-check errors/nondeterminism, all four rivals refuted, and 35/35 Racket parity.

## D11 — Preserve genuine solve provenance

The blind solve remains separate and declares no earlier exposure. The final exposed solve was regenerated after the last generator edit, is bound to final hash `4645fe…`, declares earlier exposure, and records no reference consultation. The superseded exposed solve is retained under `checks/prior-solve-177e509a/` rather than relabeled as final.
