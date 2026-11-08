# Working notes: 84def340ce03

## Review review-ee2324304e4503f0, 2026-10-03

Original generator 2.0.1 SHA-256: `50354457757c1a2fc9688b02a03e66ded0d8dd2795b895531dde8844585a3b0f`.
Repaired 3.0.0 SHA-256: `8ea98607c8e772a16787bab201e6ce235f339d25bcf5e4f5f6c560db8b0eff61`.
Canonical rule remains `e27cc4c77443`.

The original rationale is unknown: no earlier task-local review or substantive notes were present. Its summary incorrectly claimed outside-in uniform rings, and its validator rejected every canonical input. All three unique canonical inputs have heterogeneous tiles and include zero. The repaired sampler preserves the real four-pixel, center-out transformation.

The distribution deliberately supplies whole-tile repeats, consecutive row-major repeats, uniform tiles among mixed tiles, and more tiles than the longest input side. Each feature refutes an executable rival that fits all canonical pairs. Canonical examples are six stored pairs but only three unique pairs; never report six independent observations.

The exact controls replace nine partly inert declarations. None means unset for a recognized key, consistent with shared GenCtx. “Adjacent repeats” means consecutive row-major tiles, hence adjacent output rings; physical proximity in the input is not required. Unknown old controls now fail instead of silently doing nothing.

The reference formula is defined for every even legal grid with at most 60 cells. Do not reject blank, monochrome, singleton-on-background or repeated-row grids merely to satisfy a generic mutation test. Such inputs may teach little, which is a distinct question handled by strict_canonical_like, semantic witnesses and complete-lesson comparisons. Explicit malformed-domain fixtures cover odd/ragged/oversized grids, booleans and out-of-range colors.

All 156 final tests pass; the same suite has 126 failures on the original source. Final battery has 10 green stages and 2 unresolved generic gate failures (selfcheck and defect_lint). The return preserves these failures, not an artificial PASS. Two active base-authority target_code fields were aligned to exact canonical text; archival raw_code, canonical JSONL and training labels were unchanged.

The lesson probe measured 300 overlapping three-demo/one-query windows in each band, seeds 0..99 and starts 0,1,2. All six declared rivals were eliminated in every tested lesson. Each band has 600 unique generated inputs in 600 slots. Across all bands there are only 789 unique final inputs because canonical/contrast draws share seeds; do not sum per-band uniqueness. Use disjoint band seed ranges or export deduplication.

Reusable tools: workspace/lesson_probe.py and workspace/domain_probe.py. Full source-bound reports, genuine failed iterations, audits and solver work logs are in the reviewer return. Neither solver's two masked queries were scored. Parent reviewer exposure is explicitly recorded for the post-repair solve.
## Current reviewer considerations

Source SHA-256: `8ea98607c8e772a16787bab201e6ce235f339d25bcf5e4f5f6c560db8b0eff61`.

# Decisions — 84def340ce03 / review-ee2324304e4503f0

## Intended result and authority

Repair the assigned generator's distribution, retain the canonical transformation, and return replayable evidence. The initial baseline had seven failing battery stages. No earlier substantive task-local notes or pending return were found, so original author rationale is unknown. The canonical file, all audit targets, safety labels and immutable assignment are preserved.

The rule maps every row-major 2×2 tile to one center-out ring. Its four source pixels have independent output roles. Uniformizing every tile destroys those roles; the original sampler did exactly that. All three unique canonical inputs contain zero and heterogeneous tiles. See checks/semantic-review/counterexamples_verified.json and checks/lesson-probe-final/report.json.

## Distribution choices

| Choice | Reason and alternative considered | Evidence / limit |
|---|---|---|
| Heterogeneous four-pixel tiles; zero permitted | Restore the actual task. Recoloring existing uniform tiles would preserve the defect. | Canonical mutation changes 3/3 unique inputs and outputs; old sampled inputs change 0/600 per band. |
| Center-out documentation; canonical source unchanged | Canonical Racket already matches the examples. Rewriting it to the old prose would change the task. | Literal 4×4 reference witnesses in the tests; 120/120 final Racket smoke applications. |
| Exact canonical shape/palette branch | Supply canonical scale without replaying example grids. A wholly broad sampler can dilute these profiles. | Final floor: easy 10/20, medium 9/20, hard 11/20. |
| Three-profile deterministic curriculum | Ensure a complete three-demo lesson contains a canonical example and a counterexample to four canonical-fit shortcuts. IID rare witnesses can leave whole lessons ambiguous. | All 300 cyclic windows per band tested; starts 0,1,2, seeds 0..99. |
| Contrast shapes have both dimensions >4 | Refute even the conservative rival that truncates at max(h,w). A 2×N shape does not refute that capped variant. | Earlier candidate used min(h,w)!=4; final source strengthens it to >4. Earlier battery and source retained. |
| Consecutive repeated heterogeneous tiles plus separate uniform tile | Refute global dedup, run compression and uniform-tile omission in the same example. | Consecutive is row-major order, not physical input adjacency. Seed-0 boundary witness retained. |
| Broad shapes and uniform-block examples remain | Avoid replacing one restriction with a uniformly elaborate, always-mixed task. Lawful edge cases are useful contrasts. | 45/600 sampled final draws per band are uniformly tiled and correctly unchanged by the ablation. |
| Full lawful validator, separate teaching predicate | Validity and information content differ. Rejecting valid pixel edits solely to obtain green generic gates would misstate the task. | self_check accepts all six stored canonical inputs; strict teaching fraction 557/600. Two generic gates remain blockers. |
| Five observable/supported controls | Replace inert legacy switches with explicit dimensions, palette count, zero presence and construction mode. Silent compatibility aliases would perpetuate false controls. | 77,850 override draws: 61,110 accepted, 16,740 structured refusals, zero findings/warnings. |
| Keep known None values as unset | Match the existing GenCtx convention. Rejecting None was an overstrict initial test assumption. | Final tests compare all five controls with omission across all three phases; original failures preserved. |
| Synchronize active authority copies only | Remove exact-text drift while preserving canonical and historical source. | Both target_code fields equal canonical; raw_code and other JSON bytes unchanged. |

Texture feasibility is constructive: repeated/constant tiles reduce independent color groups, and exact palette capacity is checked before sampling. No count clipping or success-biased rejection loop is used.

## Evidence discipline and limits

The final probe scores declarations dynamically. Four rivals fit 6/6 stored canonical pairs (3 unique); two additional wrong rules fit none. Every authoritative reference label in the final probes comes from public Racket execution; rival and mirror predictions are explicitly identified as Python outputs. Generated samples use no overrides, no retries, no favorable-input filtering, and no replacement. Three overlapping lesson windows per seed share inputs; 900 total windows are not 3,600 independent grids.

Cross-band diversity is a real limitation: 1,800 final slots contain 789 globally unique grids, versus 993 baseline. Within each band, uniqueness rises from 445/427/331 to 600/600. Canonical/contrast values intentionally share a seed across bands. Use disjoint band seeds or export deduplication; no cross-band diversity improvement is claimed.

The strictness target of 0.60 is a teaching floor, not proof of total semantic coverage; observed 557/600 exceeds it. Finite elimination of six rivals is not universal induction, and no Qwen training run or model gain was measured.

## Failed iterations retained

The test-design directory retains the original harness import failure, baseline red suites and the two None-domain assumption failures. The final accepted test suite has 156 passes versus 126 baseline failures. The lesson probe's first provenance guard correctly stopped, but compared a stored-source SHA with a callable SHA; both the failed code and receipts remain. The corrected probe binds the two meanings separately. An optional additive shared receipt patch addresses that recurring tooling ambiguity.

## Stopping decision

The repair, focused tests, audits, both solves and exact source-patch replay are complete. The fresh copy passed all 156 tests and the domain probe, with every changed-file hash matching the reviewed source. The strict battery is still blocked by selfcheck and defect_lint because all their color-only mutations stay within this rule's domain. A task-aware gate decision remains with the maintainer. No shared gate was disabled, and no approval or training label was upgraded.

## Review `review-11f3130ee717b04a`

The generator and canonical rule remain unchanged. The task-local regression suite now locates the checkout with `reviewer_support.find_root` and opens canonical data through `canonical_path`, rather than assuming a fixed `__file__.parents[3]` depth. This preserves the same test population in both the full packet and the staged portable task-test snapshot.

## Review `review-7ecaba6883d313df` — native feedback-routed family

Production `generator.py`, canonical rule hash `e27cc4c77443`, and canonical
program bytes remain unchanged.  The new opt-in native family keeps
`routing=direct` byte-for-byte canonical and adds `routing=feedback_min`: after
painting each ring center-out, the first minimum-color rendered quadrant selects
the clockwise rotation of the next row-major 2x2 tile.  This is recurrent; the
prior rendered orientation changes the next intermediate rather than applying a
fixed postprocessing remap.

The deterministic setting-neutral grammar supports 2–6 demonstrations and
exactly four distinct queries.  Query inputs use shapes 6x10, 10x6, 2x30 and
30x2, each producing a 30x30 answer.  Repeated heterogeneous and uniform tiles
are retained as distractors.  The standard public projection was regression
checked to omit settings, programs and query answers and to reveal query inputs
one turn at a time.

The task-local audit checked both settings at seeds 0 and 17 with 2, 3 and 6
demonstrations.  Across 12 jobs and 40 protected-Racket evaluations, the selected
setting was the sole survivor among the declared family plus source-min,
global-first, one-step and current-tile shortcut rules.  This is a finite rival
audit, not universal program uniqueness or measured training gain.

Native qualification covered both settings at seeds 0 and 17 with three demos
and four queries.  It retained exact canonical default hash
`62c5fc046981a1b0ec964b0e241a4ba0f69f93d6c927a132e5478821259fb94c`
and feedback hash
`bf4245def179170046c5ff3c949b15a8ec07395b174dc07abfea68cadba86b4b`.
The source-bound skip-A witness uses a 6x10 query, records fourteen prior-ring
minimum-quadrant indices, and replays different 30x30 outputs for the qualified
feedback program and canonical direct counterfactual.  Owner admission and fresh
acceptance remain pending after integration; no training data is admitted by this
reviewer return.
