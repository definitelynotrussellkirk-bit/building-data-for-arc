# c6b14e07214c — generator review notes

Version2.0.0; selected Racket pin `d219d22bc8a3`; generator SHA `10ca64b8f0a74c5689230d7edda9709f4b339a8a9996a0b6bc4ea853c10f7a06`. Original review assignment `review-a17bad0aece71558`.

The earlier fixed four-corner sampler rejected all canonical inputs and ignored controls. The current sampler keeps a complete7-frame on zero background,2..6 distinct singleton sources,0..2 preserved interior7 cells, and at least one blank interior cell. Source colors exclude0 and7. All positive labels remain selected canonical Racket output.

Exact controls are `grid_h`, `grid_w`, `frame_h`, `frame_w`, `n_seeds`, `n_interior_sevens`. `observe_overrides` reads the actual grid. Removed legacy controls reject rather than silently do nothing. Exact overrides apply across difficulty bands; difficulty affects default size weights only.

Default profiles cycle canonical → geometry → many_sources, offset by seed. Canonical and geometry profiles use9/10 grid scale; many_sources supplies larger dimensions. Three consecutive demos refute the six declared rivals. The canonical-fitting capped-source rival is checked on every usable canonical pair. `lesson_identifiable` is an offline query-aware check; never expose its query label to the solver. Overrides and nonconsecutive assemblers can break the default guarantee and must be checked as realized lessons.

Final evidence: 12/12 battery stages green,19 task-local tests,174 repository tests,900 windows/1,800 unique inputs with no declared query-changing survivor. These finite counts do not imply universal induction or training approval. The two-demo negative control exposes41/90 windows; details are in the return's checks directory. Corner-biased high sources and constructed geometry remain useful future adversary targets.

Use `workspace/README.md` for reproduction and tool scopes. Historical return evidence belongs with the assignment ZIP, not copied into this task directory. The selected and archival Racket sources were not edited.
## Current reviewer considerations

Source SHA-256: `10ca64b8f0a74c5689230d7edda9709f4b339a8a9996a0b6bc4ea853c10f7a06`.

# Decisions and rejected alternatives

## R1 — Replace fixed corner occupancy, preserve the rule
The original source uses four corner seeds; no separate historical rationale was supplied. Canonical examples use two or three seeds at non-corner positions and include an interior 7. Treating those as invalid would redefine the task instead of repairing the generator. The replacement samples 2..6 distinct singleton source colors and 0..2 preserved interior 7s. Canonical acceptance and selected-Racket parity are mandatory. Rule pin `d219d22bc8a3` is unchanged; modifying Racket to fit the old sampler was rejected.

## R2 — Only advertise controls observable in returned pixels
Six exact axes remain: grid height/width9..22, frame height/width5..9, seed count2..6, interior-seven count0..2. All advertised Cartesian combinations fit: the minimum 3×3 interior has nine cells, enough for six seeds, two 7s, and one blank. There is no silent clipping or undocumented cross-axis incompatibility. Unknown keys and noninteger exact values reject. `None` remains the explicit unspecified value supported by the framework.

Palette categories, textures, corner/placement names, and legacy dummy controls were removed rather than kept as misleading aliases. This is an intentional override-interface change; old recipes using removed keys must migrate or receive a clear error. Color identity and locations remain randomized, but they are not advertised as exact controllable axes. A compatibility shim that silently ignored requests was rejected. Difficulty changes default weighting, never override legality.

## R3 — Guarantee concrete teaching contrasts without generating labels in Python
Three consecutive default profiles are canonical, geometry, and many_sources, with phase `(seed + sample_index) mod 3`. EXAMPLES_NEEDED remains3. The cycle is independent of evaluation seed lists. Canonical draws randomize exact small profiles, palettes and placements; the geometry phase constructs a Manhattan-vs-Euclidean/Chebyshev and tie-break contrast; the many-source phase supplies a source omitted by the canonical-fitting three-smallest-sources rival. Interior 7s refute repainting. Both grid and palette remain variable.

The positive label source remains selected canonical Racket. Python distance calculations inside witness/rival functions are diagnostic only. The independent relocated probe checks them against Racket and records source identity. Per-grid marginal witness frequency is insufficient: the full three-demo window must refute a candidate that would change its query. Answer-equivalent survivors are not failures. Tests confirm that classification is based on supplied rival declarations and that in-place rivals cannot mutate the probe's examples.

Randomly choosing a teaching profile per draw was rejected: a three-demo lesson can omit the decisive case. Increasing global sample count without checking assembly was also rejected. The two-demo diagnostic establishes the missing-window failure: 41/90 windows are ambiguous despite individually valid inputs. It is not evidence that any model actually chose those rivals.

## I1 — Frame helper correction
The first implementation passed height/width to a helper that expects inclusive bottom/right coordinates. This was our implementation error, caught by tests and the intermediate battery. The corrected call passes `(r0, c0, r0+fh-1, c0+fw-1)`. Both erroneous source and failing results are retained. No shared helper was patched outside assignment scope.

## I2 — Increase canonical-scale mixture, not seed tuning
A one-third canonical-size mixture produced only12/60 in-envelope draws in the gate's independent sample; the aggregate warning threshold is25%. The first corrected-frame battery therefore remained red even though every band had some exact support. The geometry phase now also uses9/10 dimensions by default, while its interior frame dimensions and source positions vary. Two-thirds of the cycle is canonical-scale, with the many-source phase providing size extrapolation. Final exact/envelope counts are23/60 and37/60. A failing structural regression test preceded this change. Hardcoded gate seeds, threshold relaxation and CANONICAL_PROFILE_OPT_OUT were rejected.

## Scope, bias and honest limits
The largest extra source is planted at a corner to guarantee a uniquely nearest blank even at the minimum interior size. That leaves a position bias for future adversaries. The geometry phase is also constructed, not a claim of unconstrained natural layouts. The probe tests finite declared rivals, actual direct consecutive-index lessons, and no-override default streams. Exact overrides can intentionally remove a witness; `lesson_identifiable` checks the realized lesson. Other assemblers must be checked on their actual policy before admission. No model was trained or benchmarked, and no claim is made about a Qwen accuracy improvement.

## A1/A2 — Audit findings only
The random two-target audit assignment is immutable. We read and replayed both targets but left their generator bytes unchanged. Counterexamples explicitly distinguish hand-constructed documented-domain inputs from generated samples. A1's clamped-cycle rival is a high-agreement shortcut, not a universal one:8/300 generated draws refute it. A2's column-projection rival fits300/300 sampled draws and source constraints explain why default draws always separate both axes. A2 therefore deserves a separate repair that varies relative position and verifies projected-overlap witnesses.

## Evidence and solve discipline
Every actual failure is retained, including our two intermediate generator defects and deliberately degraded teaching control. Large intermediate directories were losslessly archived with a per-file SHA/size map to meet return budgets. The final fresh solve was prepared only after the generator froze. Earlier rule exposure is disclosed, visible-only diagnostic comparisons are distinguished from submitted revisions, and hidden-query correctness is not claimed. No independent second reviewer or model evaluation was run; final review and verification were performed in this session.

## Solve-data qualification

`evidence/solve-data-qualification.json` identifies the exact supplied-stub execution from review-bc0c45d2cb547c41. It is a diagnostic baseline, not a failed reasoning solution or DPO negative. Original reports remain unchanged; no trajectory is admitted to training.
