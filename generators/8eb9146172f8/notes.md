# Working notes: 8eb9146172f8

## Review result

Version `3.0.0` replaces the transform-based `2.1.0` generator. Final battery: 12/12 green. Focused tests: 9 passing.

## Canonical facts established during review

- Four distinct canonical input/output pairs are present (the profile gate counts repeated source rows separately).
- Colors are fixed: background `0`, red deflectors `2`, cyan emitters/rays `8`.
- Cyan markers share one edge; red markers share one perpendicular edge; corners are not needed.
- The selected rule advances a latent staircase position even when it leaves the grid and clips off-canvas writes.
- Canonical horizontal examples use red markers only on the bottom edge.
- Canonical vertical emitters originate only on the top edge.

The last two omissions permit simple direction shortcuts. Generated red-top horizontal cases and bottom-origin vertical cases are required curriculum evidence.

## Decisions

- Public axes: `grid_h`, `grid_w`, `cyan_edge`, `red_edge`, `n_red`, `n_cyan`.
- Removed no-op/overlapping `palette_size` and `texture` axes and invalid generated degenerates.
- Construct orientations directly rather than applying a late dihedral transform.
- Reject parallel edge pins explicitly; all eight parallel ordered pairs are declared incompatible.
- With no dimension pins, sample one of `(12,12)`, `(12,17)`, `(14,10)`, `(17,12)` in every difficulty band so exact canonical profiles have support.
- With any dimension pin, preserve the full declared dimensions `grid_h=9..20`, `grid_w=9..22`.
- Sample marker positions from every non-corner coordinate; do not reserve an artificial in-bounds staircase margin.
- Keep `raw_code` as provenance, but synchronize both selected base `target_code` fields to canonical `program_solution`.

## Failed hypotheses retained as evidence

1. An initial test asserted that a lawful ray never leaves the canvas. A canonical pair failed it. The test and implementation were corrected to mirror clipping semantics.
2. An initial full-envelope size distribution failed strict profile support in hard mode. Unpinned dimensions were changed to explicit canonical-profile anchors.

TDD receipts are under `checks/tdd-*.log`; the complete before/after batteries are under `checks/before/` and `checks/after/`.

## Shortcut proof

The rival “horizontal rays always step upward” fits every distinct canonical pair. The frozen counterexample at seed 7, sample index 0, with `cyan_edge=left` and `red_edge=top`, differs from the canonical Racket output on 26 cells. See `checks/shortcut-witness-proof.json` and `QUESTION_ANSWER.md`.

## Limitations

- Default dimensions use four canonical shapes, although exact overrides cover the full declared domain.
- The published demonstrations alone do not identify both direction cases; generated witnesses are essential.
- Archival source remains textually divergent by design, while executable parity is verified.
## Current reviewer considerations

Source SHA-256: `84301bd12c17dbb0897847b4ddd15d66ee1e7fa0c74d4cafaa9f9a3480472d95`.

# Design decisions for `8eb9146172f8`

Each item records the inherited rationale when it was knowable, the selected design, alternatives considered, the probe used, and remaining failure modes or limits.

## 1. Background and marker colors

- **Inherited rationale:** The published task uses background `0`, red deflectors `2`, and cyan emitters/rays `8`. The old generator also used these colors, but exposed a fixed `palette_size=2` axis that did not alter them.
- **Decision:** Keep the exact `{0, 2, 8}` palette and remove `palette_size` from the public grammar.
- **Alternatives:** Permute colors, expose palette aliases, or retain a no-op palette axis.
- **Probe:** Canonical inputs pass `self_check`; wrong in-range and out-of-range colors are rejected; the override audit has no palette/provenance finding.
- **Failure mode / limitation:** This generator teaches the canonical color-bound rule, not an abstract color-role permutation.

## 2. Grid height and width

- **Inherited rationale:** Version `2.1.0` used difficulty-specific random ranges and declared `grid_h=9..20`, `grid_w=9..22`. Exact overrides were not honored after random transposition, causing tens of thousands of width/height mismatches.
- **Decision:** Preserve the declared full domains for overrides. When neither dimension is pinned, choose one of the four published dimension profiles `(12,12)`, `(12,17)`, `(14,10)`, `(17,12)` in every band.
- **Alternatives:** Sample the entire envelope by default; narrow each band to one profile; transform a base grid and swap reported dimensions.
- **Probe:** Exact lower/upper and rectangular boundary tests; 65,250-draw override audit; profile-floor audit with 60/60 exact hits and 20/20 per band.
- **Failure mode / limitation:** Default size diversity is four shapes rather than the full rectangle domain. This is deliberate because exact canonical-profile support is a hard curriculum requirement.

## 3. Cyan edge

- **Inherited rationale:** The old generator built only top-edge cyan markers and applied random dihedral transforms. This produced orientation variety but made a requested edge or dimension difficult to preserve exactly.
- **Decision:** Draw `cyan_edge` directly from `top|bottom|left|right`, or honor an exact pin before constructing the scene.
- **Alternatives:** Keep post-hoc transforms; expose a dihedral index; support only canonical orientations.
- **Probe:** All four cyan-edge pins are observed exactly; every ordinary generated scene has one unambiguous cyan edge; bottom-origin semantic witnesses fire.
- **Failure mode / limitation:** Corners are excluded so one marker cannot ambiguously identify two edges.

## 4. Red edge

- **Inherited rationale:** Red markers must lie on an edge perpendicular to the cyan edge. The old transform-based implementation varied the edge but had no exact joint-axis contract.
- **Decision:** Draw the red edge from the two perpendicular choices, while respecting either a cyan-only pin, a red-only pin, or both pins.
- **Alternatives:** Draw both independently and retry; silently coerce parallel pins; expose only a relative left/right deflection sign.
- **Probe:** Single-edge pin tests verify that the unpinned edge remains perpendicular. All eight perpendicular ordered pairs are reachable. The eight parallel pairs are explicitly declared incompatible and rejected.
- **Failure mode / limitation:** Parallel red/cyan edges are outside the task grammar rather than a degenerate training mode.

## 5. Number of red markers

- **Inherited rationale:** Version `2.1.0` varied red count by difficulty and declared `1..4`, but its validator treated counts as band-specific and rejected otherwise lawful canonical inputs when called with a different band.
- **Decision:** Keep public domain `1..4`; difficulty biases the ordinary draw through `draw_int_diff`, while structural validation accepts every lawful count in the public domain.
- **Alternatives:** Fixed count two; strict band-specific validation; larger counts limited only by edge length.
- **Probe:** Exact `n_red=1` and `n_red=4` boundary cases, canonical acceptance, and override recovery.
- **Failure mode / limitation:** The public domain is capped at four even on long edges to remain near canonical complexity.

## 6. Number of cyan markers

- **Inherited rationale:** The old generator varied cyan count by difficulty and declared `1..4` but coupled valid placement to an in-bounds-tail calculation.
- **Decision:** Keep domain `1..4`, difficulty-biased for ordinary draws, with independent exact overrides.
- **Alternatives:** Couple cyan count to red count; fixed count two; permit enough markers to fill an edge.
- **Probe:** Exact count boundaries, observable override equality, canonical acceptance, and 100% unique generated inputs/outputs in the diversity sample.
- **Failure mode / limitation:** At most four rays are generated, prioritizing interpretable examples over dense superposition.

## 7. Marker positions

- **Inherited rationale:** Red positions were sampled from interior edge coordinates. Cyan positions were artificially restricted so every transformed staircase stayed in bounds.
- **Decision:** Sample both colors without replacement from every non-corner coordinate on their selected edges. Do not reserve a margin for future ray shifts.
- **Alternatives:** Keep all tails in bounds; hand-place markers around canonical coordinates; allow duplicate markers.
- **Probe:** Canonical pair parity exposed the old in-bounds assumption as false. Rule smoke then applied the selected rule to 120 generated inputs with no crash or out-of-bounds output.
- **Failure mode / limitation:** A ray may become fully clipped after enough shifts. It still fires before clipping; `rule_smoke` found no identity case in 120 draws.

## 8. Off-canvas staircase behavior

- **Inherited rationale:** The old notes claimed “no truncation,” but at least one published example has a staircase tail that leaves the canvas. The selected Racket rule advances the latent position and simply skips writes outside the grid.
- **Decision:** Treat clipping as part of the canonical rule. Input markers remain; only in-grid ray cells are painted.
- **Alternatives:** Reject such inputs; clamp a ray to the border; stop advancing after the first out-of-bounds step.
- **Probe:** All distinct canonical outputs equal both the selected Racket output and the independent Python mirror. A test written with the stronger invariant failed on canonical data before this decision was corrected.
- **Failure mode / limitation:** Clipped cells are unobservable, so examples with excessive clipping may carry less visual evidence than fully in-bounds rays.

## 9. Direct construction versus dihedral transforms

- **Inherited rationale:** Dihedral transforms were an economical way to add orientations to a top/left base case.
- **Decision:** Remove post-generation transforms and construct each orientation directly.
- **Alternatives:** Transform both scene and metadata; keep transforms only when no overrides are supplied.
- **Probe:** Exact dimension and edge recovery on boundary cases; no override mismatch or axis-provenance finding across the complete override audit.
- **Failure mode / limitation:** The code has four explicit traversal branches, which is longer than a transform-based implementation but substantially easier to audit.

## 10. Difficulty

- **Inherited rationale:** Difficulty changed dimensions and counts in version `2.1.0`.
- **Decision:** Accept only `None|easy|medium|hard`. Use `draw_int_diff` for marker counts; keep all bands on the same canonical-compatible scene grammar and profile support.
- **Alternatives:** Make hard examples larger only; change orientation availability by band; ignore invalid difficulty strings.
- **Probe:** Deterministic generation and validation across all three bands; 200 semantic draws per band; 20 profile-floor draws per band.
- **Failure mode / limitation:** Difficulty mainly changes count tendencies, not the logical rule or palette.

## 11. Removed texture and degenerate modes

- **Inherited rationale:** The old public `texture` axis aliased cyan edge values and also exposed `no_cyan`, `no_red`, and `full_grid`. These modes were outside the selected rule grammar, overlapped another axis, and produced validator failures.
- **Decision:** Remove `texture`, `palette_size`, helpful texture aliases, and generator-produced degenerates from public generation. Set `HELPFUL_TEXTURES` and `DEGENERATE_TEXTURES` empty.
- **Alternatives:** Keep them as private negative-test fixtures; make degenerates return expected rejections; retain the alias for compatibility.
- **Probe:** Lint and strict defect lint are green. The override audit has zero findings/warnings, versus roughly 94,000 categorized findings before the rewrite.
- **Failure mode / limitation:** Callers using the obsolete axes now receive an explicit unknown-key error rather than a compatibility shim.

## 12. Override error policy

- **Inherited rationale:** The old implementation silently accepted unknown keys and often returned values different from requested dimensions or edge axes.
- **Decision:** Validate keys, scalar types, string domains, difficulty, ranges, and joint edge compatibility before any draw. Reject malformed calls with `ValueError`.
- **Alternatives:** Ignore unknown keys; coerce values; retry until an accidental match; return metadata instead of observable exactness.
- **Probe:** Unknown-key unit test and battery probe; lower/upper boundaries; parallel pair tests; full override matrix with zero findings.
- **Failure mode / limitation:** Strict failure may break permissive legacy callers, but prevents silent training-data corruption.

## 13. Structural checks

- **Inherited rationale:** The old `self_check` required both colors and band-specific counts, and rejected canonical inputs containing four cyan markers under default difficulty.
- **Decision:** Separate task grammar from generation policy. `self_check` validates shape, dimensions, palette, count domain, non-corner single-edge placement, and perpendicularity. `strict_canonical_like` currently equals that grammar.
- **Alternatives:** Validate only generated scenes; include band-specific count policy; treat wrong palettes as a permitted degenerate.
- **Probe:** Every distinct canonical input passes; malformed palette, parallel edge, and off-edge examples fail; self-check and defect-lint stages are green.
- **Failure mode / limitation:** Structural validity does not by itself prove that an example set identifies the intended direction rule; semantic witnesses handle that separately.

## 14. Python rule mirror

- **Inherited rationale:** No independent mirror was present. The selected Racket program is authoritative, but without a mirror it was harder to test rivals and generated outputs cheaply.
- **Decision:** Implement `_paint_rays` and `rule_mirror` independently in Python, with the same clipping semantics.
- **Alternatives:** Invoke Racket for every unit test; copy expected grids by hand; treat generator validity as sufficient.
- **Probe:** 120/120 Racket comparisons match the mirror; all canonical outputs match; the exact shortcut episode emitted through the canonical Racket reference equals the mirror.
- **Failure mode / limitation:** A shared conceptual misunderstanding could affect both implementations; canonical examples and executable authority parity are the independent anchors.

## 15. Shortcut witnesses and curriculum

- **Inherited rationale:** Unknown. The old generator had no semantic contract. The canonical demonstrations omit bottom-origin rays and place every horizontal case's red markers on the bottom edge.
- **Decision:** Declare two canonical-fitting rivals, two exact witness predicates, their mappings, and lesson competitors. Generate both missing orientation families normally.
- **Alternatives:** Rely on random orientation diversity without naming rivals; add only hand-authored tests; change canonical examples.
- **Probe:** Each rival fits every distinct canonical pair. In the semantic gate, each witness fired 60 times and refuted its rival 60/60. The frozen exact witness in `checks/shortcut-witness-proof.json` differs on 26 cells.
- **Failure mode / limitation:** Other more contrived lookup-table shortcuts always exist. The selected rivals are simple, plausible, and directly induced by missing canonical cases.

## 16. Rule authority and provenance

- **Inherited rationale:** Canonical `program_solution`, base `target_code`, and archival `raw_code` contained multiple textual authorities. Before review, selected target authorities were not synchronized even though executable behavior happened to agree on canonical examples.
- **Decision:** Set both base `target_code` fields to the exact canonical selected program. Preserve `raw_code` untouched as archival provenance. Pin `RULE_HASH="5592536df499"`.
- **Alternatives:** Replace raw archival code; keep divergent selected text; alter the canonical program.
- **Probe:** Authority synchronization is green; selected exact/normalized group counts are one; execution parity is `PASS` for both textual implementations.
- **Failure mode / limitation:** The final authority status remains `selected_synchronized_archival_divergent`, intentionally documenting rather than erasing archival divergence.

## 17. Determinism and observability

- **Inherited rationale:** Generation used seeded context but mixed many choices through one layout RNG, making individual axes hard to audit.
- **Decision:** Use named draws for dimensions, counts, edges, and positions; verify the final scene by calling `observe_overrides` before return.
- **Alternatives:** Trust the draw context without inspecting output; attach hidden metadata; use global randomness.
- **Probe:** Repeat generation returns byte-identical grids; `observe_overrides(grid)` equals all requested facts; rule smoke reports input purity and reentrant execution.
- **Failure mode / limitation:** Changing `VERSION` intentionally changes the deterministic sequence.

## 18. Proposed episode-level deflection distance (2026-10-23)

- **Status:** Proposed research prototype only. The approved production
  generator, canonical rule authority, and `RULE_HASH="5592536df499"` remain
  unchanged. Production `generator.py` still has SHA-256
  `84301bd12c17dbb0897847b4ddd15d66ee1e7fa0c74d4cafaa9f9a3480472d95`.
- **Parameter:** One hidden `deflection_distance` is fixed per episode, with
  declared values `{1,2}` and canonical default `1`. At each red trigger, all
  active cyan rays shift away from the red edge by that distance before
  continuing inward. Distance `2` changes only the four signed shift constants;
  origin, travel direction, trigger order, clipping, palette, and input grammar
  are preserved.
- **Authority:** Distance `1` materializes the exact canonical Racket source.
  Both settings are executed through the bundled real Racket runtime; Python
  does not produce labels. The distance-one rule reproduces all eight labeled
  canonical rows, and the same-input witness differs on 12 cells between the
  two settings.
- **Episode support:** Retained evidence contains two episodes, one per setting,
  with three demonstrations and four independently counted, distinct queries
  each. Every demonstration refutes the rival setting, so the consistent
  setting set is a singleton; every query also differs under the rival.
- **Public-evaluation transfer:** Evaluation task `20a9e565` contributes only
  the idea of identifying and extrapolating a repeated spatial stride. This is
  an inspired extension, not a verified lineage, equivalence, admission, or
  measured-difficulty claim.
- **Evidence:** See
  `workspace/parametric/{prototype.py,README.md}`,
  `tests/test_parametric_deflection_distance.py`, and
  `WORK/checks/parametric/deflection-distance-s20261023-v1/manifest.json` in the
  return package. Public challenge IDs are derived only from visible bytes;
  hidden settings, rule text, rival predictions, seeds, and query answers stay
  private.
- **Limits:** The declared set is intentionally finite, `{1,2}`. Retained
  evidence covers selected seeds and role templates and rejects ambiguous draws;
  it is not a census over all seeds or all coherent variants.

<!-- arcpuzzles-current-conflict-reconciliation:start -->
## Current proposal reconciliation

The step_size={1,2} proposal is the selected deflection_distance={1,2} law. Ported its independent Python loop into the current Racket-backed prototype instead of replacing the stronger selected writer; production source unchanged.

Current source-bound disposition and focused checks: [evidence/conflict-reconciliation.json](evidence/conflict-reconciliation.json). All proposed variants remain unapproved and training_admitted=false. Existing audits/failures are preserved; this reconciliation does not resolve an audit or refresh an exact-source safety approval.
<!-- arcpuzzles-current-conflict-reconciliation:end -->
