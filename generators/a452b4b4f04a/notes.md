# Review handoff — a452b4b4f04a

## Current decision

Keep canonical single-color/three-corner examples while deliberately varying
color count, missing corner, palette, size, aspect, placement, and boundary
contact. Do not recover diversity by returning to canonical-incompatible
always-two-color/two-marker inputs. Do not add overlap semantics without a new
explicit policy and reference tests.

Final generator SHA-256:
`fc5965005f4cf72f3c35f78c9b8a5822d41bb63782a05b87052186b4f2c42093`.
Canonical rule hash: `f54dbee03c8b`. Approval is **unchanged**, not granted by this
review. `VERSION=3.0.0` invalidates the old sample stream deliberately.

## Changes and evidence

R1 restores all five canonical examples, including color 5. R2 replaces ignored
or decorative overrides with four observable exact integer axes and constructive
packing. R3 removes a comment-only active-source discrepancy, without editing
the canonical ledger or executable Racket forms. R4 adds actual lesson-level
checks against three canonical-fitting rivals. The initial arithmetic schedule
aliased under correlated seed/index sampling; a seed-keyed phase offset fixed
that. The failed revision is retained, rather than rewritten as a successful
first attempt.

The review return contains `checks/after/checks/` (12 green stages),
`checks/qualification_final.json` (source-bound Racket census and real lessons),
`checks/focused_tools_final.log` (60 task-local tests), and
`checks/project_suite.log` (178 repository tests). The final tool-only metadata
revision does not change generator bytes. Detailed distribution rationale lives
in return-root `DECISIONS.md`.

## Important boundaries

The validator accepts some lawful grids outside the sampler's exact axes (up to
30x30 and mixed per-color marker counts). `strict_canonical_like` measures the
single-color/three-corner structural profile; the separate shared profile gate
checks canonical scale/palette signatures. Canonical dimensions are strongly
weighted, not hard-coded example grids. Defaults guarantee finite-rival teaching
coverage; explicit overrides can intentionally remove it. Three rivals are not
all possible rules. No Qwen training or held-out accuracy measurement was run.

## Next agent

Rerun the commands in `workspace/README.md` from the original packet plus this
delta. Keep the final generator/rule hash relationship intact. Independently
validate authority parity and the audits before admission. Do not toggle
approval or treat the reviewer-authored solve as a blind human/model trace.

The two audit targets were read-only: `252c3df06496` has a documented-domain
ambiguity, not an in-domain defect; `2e5c98d98eed` has a reproduced canvas-shape
lookup shortcut over all 256 emitted inputs. Prioritize independently varying
frame placement at a fixed canvas size in a **separate** assignment for the
latter; preserve canonical support and verify each new scene with Racket.

Original associated notes remain untouched in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `fc5965005f4cf72f3c35f78c9b8a5822d41bb63782a05b87052186b4f2c42093`.

# Distribution decisions and rejected alternatives

Final selected source: `fc5965005f4cf72f3c35f78c9b8a5822d41bb63782a05b87052186b4f2c42093`.
Rule pin: `f54dbee03c8b`. Evidence is in REVIEW.md and the named check files.

| Choice | Original rationale / evidence | Decision and rejected alternative | Probe / limitation |
|---|---|---|---|
| Color count and markers (R1) | Original summary explicitly required 2–3 colors and exactly two opposite corners; reason for excluding the canonical one-color/three-corner case is unknown. | Include 1–3 colors and 2/3/4 corners. Preserve the canonical case as a default phase, rather than merely making the validator accept it. Reject an always-canonical sampler because it cannot teach color separation or two-corner completion. | 5 canonical pairs; Racket census; three lesson competitors. No one-corner or adjacent-two-corner cases because they cannot locate the intended nondegenerate box. |
| Palette (R1) | Baseline excludes 5, despite a canonical color-5 example; rationale unknown. | Use every nonzero ARC color symmetrically; distinct colors identify separate objects. Reject decorative palette-kind controls with no stable semantics. | All nine colors observed in each 600-case band census; color-5 and color-renaming tests. Same-color multiple objects are outside the teaching grammar. |
| Dimensions and profiles (R1/R2) | Baseline emitted a narrow band but advertised a wider exact range; no evidence that these mismatches were intentional. | Honest 6–20 exact dimensions in every band, strong default canonical-size weighting, and broader noncanonical components. Reject pure size expansion that erases canonical support and reject hard-coded canonical grids. | 20-draw per-band profile gate and larger census. Structural strictness is intentionally distinct from exact shape/palette similarity. |
| Packing and overlap (R2) | Baseline required nonoverlap but bounded attempts could fail to realize requested structure. | Recursive capacity-checked guillotine partition; choose boxes within disjoint regions. Minimum 6x6 supports all advertised 1–3 objects of minimum 3x3. Reject arbitrary retries/silent underplacement. | 2,160 exact combinations plus 243 Racket controls. The layout distribution is not uniform over all packings; nested, overlapping, and disconnected same-color scenes remain excluded. |
| Corner orientation / boundaries (R4) | Baseline favors one diagonal; rationale unknown. | Either diagonal, any missing corner, or all corners; include boundary-touching examples. Reject always-interior boxes because a canonical-fitting boundary-ignoring rival survives. | Orientation, reflection, rotation, boundary witnesses; actual-Racket parity. Four corners are still nonidentity because minimum side length is three. |
| Exact controls (R2) | Several old axes were ignored, shallow, or degeneracy-inducing. | Advertise only grid_h, grid_w, n_colors, corner_count; enforce actual integers and domain bounds. Unknown/retired keys fail loudly. Reject keeping deprecated no-op knobs for apparent compatibility. | Cartesian tests and shared override gate. External callers using old palette/texture/density knobs must remove them; this is an intentional versioned contract change. |
| Three-phase teaching schedule (R4) | Individual valid examples do not ensure an assembled lesson distinguishes plausible rules. | Canonical, multicolor, two-corner/boundary in every consecutive three-example window. Caller exact overrides take priority; do not quietly change requested scenes to improve a lesson score. | 100 real lessons per band plus all three cyclic starts for seeds 0–19. Measured guarantee is only for defaults and the declared finite rivals. |
| Seed-keyed phase offset (R4) | First revised arithmetic phase aliased when seed=4200+i and index=11*i; retained failed tests expose it. | Hash-keyed stable random offset per seed, then cycle on sample index. Reject a phase depending on a simple seed/index sum, which can collapse under common sampler strides. | Failed intermediate source and red/green logs; large pinned census and cyclic coverage. Stable hashing does not promise balance under every adversarially chosen seed set. |
| Canonical authority (R3) | Selected active source differed only by an explanatory comment; execution parity already passed. | Remove the selected comment to match unchanged canonical source exactly. Reject disabling authority sync or rewriting canonical to justify sampler restrictions. | Field-only diff evidence, authority regression and all final battery gates. Active source bytes did change, even though semantics did not. |
| Validator scope | Validator should characterize lawful structure, not memorize a short generated-profile list. | Accept valid structure up to ARC's 30x30 bound, with 1–3 colors and potentially mixed per-color corner counts; actual emitted axes remain narrower and uniform per example. | Mutation tests and canonical acceptance. Validator acceptance alone does not imply positive emission probability; A2 demonstrates why that distinction matters. |

## Rejected inference

The finite-rival certificates are not proof that a model will learn the intended
rule or that Qwen3.5-9B accuracy improves. No model was trained or benchmarked.
Repeated cyclic windows are useful stress cases but not independent test cases.
The reviewed task remains unapproved until maintainer verification.

## Audit decisions

A1's body distractor violates the target's explicit sparse-left-edge grammar;
report it as a scope choice, not a blocking defect. A2's translated frame is
accepted by both the validator and strict hook, yet cannot be sampled by any
advertised profile. Exhaustive support and canonical parity establish a real
shortcut opportunity, not a measured model failure. Both targets remain
unchanged; repair belongs in separate scoped assignments.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a452b4b4f04a/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Parametric prototype review-1235967f8e2a064a (2026-10-24)

Decision: leave the approved production generator and canonical rule authority unchanged. Add an opt-in task-local family whose episode-fixed `render` setting is `outline` (the byte-identical canonical default) or `filled`; both settings receive identical color-specific corner-marker inputs and differ only in rendering each inferred bounding box.

The adapter exposes independent 2–6 demonstration and 1–4 query counts. Retained episodes use four distinct queries, including a 30×30 multi-object query. `episode_io.py` is a reusable strict sequential exporter: one opaque hash-named public file per query, no settings/seed/program/answer/index/total-count hint, atomic publication, duplicate-visible refusal, and saved-bundle verification.

Evidence: `workspace/parametric/evidence/current/report.json` records 12 protected-worker jobs and 136 protected-Racket evaluations; `WORK/checks/a452b4b4f04a-qualification-final/qualification.json` records native finite-setting qualification; `WORK/checks/final/independent-check.json` adds seeds 0–31, count-boundary, prefix-stability, shared-input, pairwise-distinction, and retained-bundle checks. The source binding remains generator SHA-256 `fc5965005f4cf72f3c35f78c9b8a5822d41bb63782a05b87052186b4f2c42093`, rule hash `f54dbee03c8b`.

Limit: this is bounded prototype/qualification evidence, not variant acceptance, universal identifiability, measured learning gain, or training admission. Next useful owner action is semantic review of the parameter grammar followed, only if desired, by a separate exact-source acceptance decision.
