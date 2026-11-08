# Working notes: 9db8deba5903

## 2026-10-24 native parametric reviewer extension

The production generator and selected canonical Racket source remain byte-for-byte unchanged. The task-local native adapter adds two matched-input settings: `canonical`, which returns the exact selected rule, and `largest_tiled_component`, which first builds the canonical four-quadrant rotation mosaic and then selects the unique largest four-connected color-1 component in that intermediate and recolors only it to 9.

The dependency is deliberately sequential. Stage B cannot know its candidates or their sizes from the input alone because rotated copies join across quadrant seams only after Stage A constructs the mosaic. The retained protected-Racket counterfactual replaces only Stage A with four identity copies; the largest component changes from size 8 to size 4 and the final output changes. Evidence: `checks/9db8deba5903/causal-official/witness.json`.

The adapter supports 2–6 demonstrations and 1–4 sequentially visible queries, uses matched inputs across settings, is prefix-stable, omits query outputs from public projections, and includes a 15×15 input whose result is 30×30. Fresh evidence reported 42 staged tests, 120 protected-Racket finite-rival evaluations with no harmful tested survivor, two clean public projections, and native qualification for both settings at seeds 0 and 17 (four jobs, 32 labels).

Current disposition: reviewer-ready prototype only. Owner exact-byte integration, fresh owner qualification/acceptance replay, and any training admission remain pending. The rival bank and seed set are finite and do not prove unique induction.


## 2026-09-28 review — selected design

The v2 generator had eight declared axes but no coherent lesson schedule. Several axes were dead or only partly honored, degenerate textures were declared valid while intentionally violating `self_check`, and a fixed top-right pixel was used to break 4-fold symmetry. That repair was a learnable artifact. The generator also had no task-linked semantic contract and its selected base Racket target differed textually from canonical.

Version 3.0.0 replaces that surface with one exact `scene_profile` axis. Twelve profiles are split into four per difficulty band. A profile is observable from `(side length, sorted color multiplicities)`, so override compliance is exact without leaking hidden metadata. The layout remains seed-variable and uses connected, scattered, edge-spanning, and half-turn families.

Important rule constraint: do **not** require all four rotations to be distinct. Canonical contains a lawful input whose 180° rotation equals the input, so its orbit has size two. Every band therefore schedules one half-turn-symmetric-but-not-90°-symmetric profile and three full-orbit profiles. A four-example lesson always contains both kinds.

`self_check` accepts all six canonical inputs and all generated profiles. It rejects malformed grids, one-color grids, singleton colors, one-dimensional short-line marks, isolated solid 2×2 impostors, and 90°-invariant inputs. It intentionally does not require a specific texture: the transformation is valid for any sufficiently informative square pattern.

Semantic contract:

- `strict_canonical_like`: all generated draws and all canonical inputs pass.
- branch witnesses: canonical 3×3 binary, multicolor, half-turn orbit, full orbit.
- rival claims: `repeat_identity` and `swap_quarter_turns`.
- `lesson_identifiable`: four consecutive demonstrations must refute both rivals.

Verification after the change: all 12 battery stages green; 600/600 strict semantic draws; 6/6 canonical inputs accepted; 6/6 witnesses fire; 2/2 rival claims verified; 12/12 lessons identifiable; 1,170/1,170 override draws accepted with zero findings; 120/120 Racket mirror checks; 97% input/output uniqueness in the diversity probe.

Limitations: profile identity is recovered from shape and color-count signature, not morphology, so an arbitrary external grid with the same signature can be labeled as that profile. This is sufficient for generated override auditing but should not be interpreted as a universal scene classifier. Changing profile counts requires a version bump and signature-table update.
## Current reviewer considerations

Source SHA-256: `59b8d0b23d4ffbcf741af0db076dd2ac9777d1c03c426eaab71ef38184f908f5`.

# Decisions: 9db8deba5903

## D1. Keep the canonical transformation unchanged

**Choice.** Preserve the canonical quadrant order: identity, 90° CCW, 180°, 90° CW.

**Original rationale.** The written solution, all six canonical pairs, the selected legacy Racket, and the Python mirror agreed behaviorally.

**Alternatives considered.** Rewrite the rule; retain the text-divergent selected source; change canonical to the shorter legacy form.

**Probe.** Baseline rule smoke passed, and authority sync showed behavioral parity despite source-text divergence.

**Failure mode avoided.** A gratuitous rule rewrite could alter semantics or invalidate the canonical hash.

**Limitation.** The canonical source contains unused `h` and `w` bindings, but exact synchronization is more valuable than stylistic cleanup.

## D2. Make canonical Racket the selected authority and preserve legacy text as archival

**Choice.** Copy canonical `program_solution` exactly into `target_code`; retain the previous executable in `raw_code` with explicit role/status metadata.

**Original rationale.** Unknown; the base row had preserved the older executable form.

**Alternatives considered.** Delete the legacy source; leave both active sources divergent; replace canonical with legacy.

**Probe.** Authority sync now reports `selected_synchronized_archival_divergent`, with execution parity passing over both source texts.

**Failure mode avoided.** Different training and execution paths silently selecting different active programs.

**Limitation.** Textual duplication remains by design so provenance is not destroyed.

## D3. Collapse eight axes into one `scene_profile` axis

**Choice.** Replace `grid_n`, palette, texture, density, noise, asymmetry, corner, and dead foreground-density controls with a single exact categorical profile.

**Original rationale.** The old axes attempted broad visual diversity through independently sampled texture knobs.

**Alternatives considered.** Repair all eight axes and define compatibility rules; retain degenerate textures as a separate negative-fixture mode; expose every internal layout choice as another axis.

**Probe.** Baseline override audit found 4,619 findings and 9,480 explicit multi-axis rejections. The new contract passes 1,170/1,170 draws with zero findings.

**Failure mode avoided.** A nominal Cartesian product whose combinations are invalid, dead, or unobservable.

**Limitation.** Callers lose fine-grained low-level texture controls. For training quality, exact semantic profiles are preferred over a large but misleading control surface.

## D4. Use four deterministic profiles per difficulty band

**Choice.** Schedule by `sample_index % 4` within each band; overrides can still request any of the 12 profiles in any band.

**Original rationale.** The old generator sampled sizes/textures independently and had no lesson-level schedule.

**Alternatives considered.** Fully random scheduling; one global schedule independent of difficulty; one profile per band.

**Probe.** The semantic census visits all 12 declared profiles, and every sliding four-demo lesson refutes both named competitors.

**Failure mode avoided.** Random lesson windows containing only examples on which a plausible rival rule agrees.

**Limitation.** The cycle is intentionally predictable. Spatial layouts and palettes still vary by seed and sample index.

## D5. Put a canonical 3×3 binary profile in every band

**Choice.** Reserve one of four slots in easy, medium, and hard for side 3 with two colors, using different color-count signatures.

**Original rationale.** Canonical consists entirely of 3×3 two-color inputs, but the old hard band generated only 6×6 or 7×7 grids.

**Alternatives considered.** Treat hard as size-only and accept zero canonical overlap; make every draw canonical-sized; add a separate canonical-only dataset.

**Probe.** Canonical-profile support improved from 13/60 with hard 0/20 to 15/60 with easy 4/20, medium 6/20, hard 5/20.

**Failure mode avoided.** A model trained on hard examples never seeing the literal canonical scale/manifold.

**Limitation.** Difficulty is semantic/layout breadth, not monotone size; one hard slot is deliberately small.

## D6. Preserve lawful half-turn symmetry

**Choice.** Include one 180°-symmetric but not 90°-symmetric profile per band. Do not require four distinct rotations.

**Original rationale.** The old summary claimed rotations should visibly differ and repaired full 4-fold symmetry, but it did not distinguish orbit size two from orbit size one.

**Alternatives considered.** Require all four rotations to be pairwise distinct; allow 90°-invariant inputs; exclude all symmetric inputs.

**Probe.** A canonical training input has an orbit of size two. The focused test explicitly accepts a diagonal 3×3 orbit-two grid.

**Failure mode avoided.** Rejecting a legal canonical geometry and teaching an incorrect stronger rule.

**Limitation.** A half-turn example alone cannot distinguish CW from CCW; the scheduled full-orbit examples do that within the same lesson.

## D7. Generate asymmetry structurally, never by editing a fixed cell

**Choice.** Construct/retry layouts until the intended orbit and structural checks hold.

**Original rationale.** The old code changed the top-right cell whenever a generated texture was 4-fold symmetric.

**Alternatives considered.** Randomize the repair cell; keep the fixed repair; permit symmetric ordinary draws.

**Probe.** 3,000 stress draws completed in under one second of generation time, all passing `self_check`; diversity remained 97% unique.

**Failure mode avoided.** A stable top-right anomaly that a model can use as a generator fingerprint.

**Limitation.** Rejection sampling has a bounded retry loop. Current profiles have large feasible spaces and did not exhaust it in stress or battery runs.

## D8. Make profile realization observable from the grid

**Choice.** Assign each profile a unique `(n, sorted color multiplicities)` signature and implement `observe_overrides` from returned pixels.

**Original rationale.** The old generator had no observer and several exact axes could not be recovered.

**Alternatives considered.** Return hidden metadata; infer morphology/family with a complex classifier; trust keyed-draw provenance only.

**Probe.** Every profile override is round-tripped in every difficulty band, and the override gate reports zero findings.

**Failure mode avoided.** Declared controls that are consumed internally but not reflected in the training example.

**Limitation.** Signature identity does not prove the named morphology on arbitrary external grids; family generation is separately tested through construction and semantic checks.

## D9. Strengthen `self_check` without overfitting to textures

**Choice.** Validate literal ARC shape/type/range, side 3..7, 2..4 colors, at least two cells per color, no tiny one-dimensional minority mark, no isolated solid 2×2 minority block, and no 90° invariance.

**Original rationale.** The old check only required square, at least two colors, and not 4-fold symmetric.

**Alternatives considered.** Require connected objects; require all colors to have a specific topology; accept every non-monochrome square.

**Probe.** All six canonical inputs and all generated draws pass; generic singleton, short-line, solid-2×2, monochrome, malformed, and 90°-symmetric fixtures fail. Defect lint is clean.

**Failure mode avoided.** Minimal marks that technically rotate but do not teach a meaningful 2-D transformation.

**Limitation.** Cell shuffles and color swaps remain lawful because the rule is texture- and color-label-independent. Rejecting them would encode unsupported semantics.

## D10. Add named rivals and a four-demo identifiability contract

**Choice.** Test `repeat_identity` and `swap_quarter_turns`; bind them to witnesses and require every four-demo lesson to refute both.

**Original rationale.** The baseline had no semantic contract, so diversity/profile gates could not measure whether lessons distinguish the rule.

**Alternatives considered.** Rely on marginal diversity; use witnesses with no rival claim; train a model as the gate.

**Probe.** Semantic gate: 600/600 strict, six witnesses firing, 60/60 verified checks for each rival claim, and 12/12 identifiable lessons.

**Failure mode avoided.** High-diversity examples on which a simpler wrong transformation gives the same answer.

**Limitation.** Two rivals are not an exhaustive hypothesis space. They cover the most direct quadrant-order shortcuts exposed by this task.

## D11. Add focused tests before implementation

**Choice.** Encode expected behavior in a task-local pytest file and observe the baseline failures before replacing production code.

**Original rationale.** No task-local tests existed.

**Alternatives considered.** Depend only on the battery; add tests after implementation; manually inspect samples.

**Probe.** The initial run failed 10 of 11 tests for the expected missing contracts, then a separate authority test failed before synchronization. Final focused suite is 12/12 green.

**Failure mode avoided.** A battery-only repair that passes generic checks but regresses canonical pairs, determinism, or lesson structure.

**Limitation.** Tests pin the current profile schedule and signatures; intentional curriculum changes require explicit test/version updates.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-026dd51a546f5f5a:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `59b8d0b23d4ffbcf741af0db076dd2ac9777d1c03c426eaab71ef38184f908f5`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported bounded no issue on unchanged59b8d0b23d4ffbcf741af0db076dd2ac9777d1c03c426eaab71ef38184f908f5,rule847ceb038813. Source/notes/scene_profile observer/orbit schedule/rivals inspected;12/12 portable tests reported. Exact observer applies to generated shape/color signatures,not universal morphology classification. Existing independent approval is provenance,not a new approval from this audit. Source-bound receipt retained at generators/9db8deba5903/evidence/bounded-audit-026dd51a546f5f5a/manifest.json.

### Assessment or prior finding

## 9db8deba5903

No issue found.

I reviewed the exact selected source `59b8d0b23d4ffbcf741af0db076dd2ac9777d1c03c426eaab71ef38184f908f5`, its current notes/review index, canonical transformation, observable `scene_profile` contract, half-turn/full-orbit schedule, semantic rivals, and focused tests. The retained current index contains no unresolved audit, and the exact source already has an independently checked decision bound to rule hash `847ceb038813`. The optional portable task-test snapshot passed 12/12 (`checks/audit/9db8deba5903-task-tests/result.json`).

Residual limitation, not an actionable defect: `observe_overrides` identifies profiles from shape and color-count signatures rather than reconstructing morphology, so it is an exact generated-grid observer rather than a universal external-grid classifier. The task notes already state that limit.

No files under `repo/generators/9db8deba5903/` were edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
