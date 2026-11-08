# Working notes: 02280b74c8ab

## Review revision 4.1.0 — 2026-10-04

The unchanged canonical authority is bound by RULE_HASH a7b2395a133e. The v3.0.1
sampler ignored code_shape, rejected legal advertised dimensions and size-3
controls outside hard, and had a size-2 fallback for size-3 requests. Its validator
missed crop contamination/output bounds and rejected lawful index colors 6/7.
The repair uses finite connected template libraries, constructive disjoint
placement, pixel-derived axis observations, and explicit incompatible aliases.

### Declared domain

Unique largest 4-connected color-6/7 components have equal square 2x2 or 3x3
bboxes and at least three cells. Each template crop contains only its own color
and zero. Template and code bboxes are pairwise disjoint. The code bbox is formed
from every remaining 1..8 cell and contains no 9. Its mosaic is at most 30x30.
These are clean-mosaic sampling restrictions: the Racket program can execute
some rectangular, unequal, or contaminated crops with clipping/overlap semantics.
They are not a claim that all rejected inputs lack a Racket result.

Symmetry is lawful and represented by crosses/rings. The canonical profile pairs
one symmetric shape with an asymmetric five/six-cell shape. Dense asymmetric
eight-cell templates separately teach that occupancy is not permission to skip
rotation. A color-9 cell is ignored only OUTSIDE the index/template bboxes: the
authority processes all pixels after cropping, including an internal 9.

### Default lesson construction

The five profiles are small_gapped, dense_full, small_full, dense_gapped, and
canonical_sparse. Small profiles use two-cell tiles and code above the templates
with magenta to the right; dense and canonical profiles use three-cell tiles and
vary all four relative layout directions. Profiles 0/3 have a fully empty internal
code column; others use 2x3 or 3x2 full code. Profiles 0/1 or 2/3 carry exterior
9, selected by one seed-only flip, while the canonical profile has none.
Thus size crosses both gaps and decor, and gaps also cross decor in ordinary
sampling. The canonical profile uses the actual sparse/symmetric template family.

Every five consecutive indices contain two size-2 witnesses, two dense rotation
witnesses, two gapped cases and two decorated cases. Removing any one pair leaves
evidence against each declared rival, including decoration-derived and gap-derived
strides. Actual production accepted indices and all cyclic starts must still be
checked: deduplication/rejection could invalidate an index-only argument.
The default contract uses four demonstrations and one query; arbitrary shorter
lessons, multiple-query layouts and arbitrary control-conditioned lessons are
outside this finite teaching guarantee.

Difficulty changes the small_gapped canvas distribution (easy favors smaller
search areas, hard larger ones) while every legal exact control works in every
band. Other profiles retain substantial canonical size/palette support. No grid
is copied from canonical examples. Deterministic library enumeration is cached;
neither generated grids nor labels are cached in the generator.

### Overrides and bounded edges

grid_h=10..20, grid_w=12..22, tpl_size=2..3, all five code_shape values, and
decor_9=0/1 are exact and observed from pixels. Helpful texture values alias
code_shape and reject conflicting simultaneous requests. monotone_code and
single_index are lawful, deliberately under-informative controls; neither is
sampled as the default texture. single_index is incompatible with an explicit
code_shape. Unknown keys and malformed values raise ValueError.

### Retained review evidence and tools

tests/test_review_contract.py contains independent control/domain regressions
and real canonical Racket checks. workspace/probe_mosaic.py labels through the
public Catalog API, checks the live rival mappings, every cyclic schedule start,
query rotations and optional joint-control boundaries, with exact source hashes.
See the returned REVIEW.md, RESULTS.json and checks/ for measured final counts,
failed intermediate iterations and the independent adversarial audit findings.

Remaining limits: equal square 2/3-cell templates, fixed semantic colors 6/7,
clean disjoint crops, and a finite list of rivals. Passing the declared-rival
checks does not establish universal rule identification or training admission.
## Current reviewer considerations

Source SHA-256: `c6c1fe92d20bffc6f109fc202d6861003e8594f73ff3495359b094328a1b66e8`.

# Decisions — 02280b74c8ab, version 4.1.0

Final generator SHA-256: `c6c1fe92d20bffc6f109fc202d6861003e8594f73ff3495359b094328a1b66e8`.
Selected canonical rule: `a7b2395a133e`, unchanged. The assignment and both audit targets remain as drawn.

## D1 — Make advertised controls an exact contract

The baseline ignored `code_shape`, accepted unknown controls, rejected advertised dimensions within some difficulty bands, and could return a size-2 template when size 3 was requested. The new generator honors `grid_h=10..20`, `grid_w=12..22`, `tpl_size=2..3`, all five code shapes, and `decor_9=0/1` in every difficulty band. Boolean decor values are accepted; malformed values, unknown keys and conflicting shape/texture requests raise explicit `ValueError`. The five code shapes include canonical `3x2`.

`observe_overrides` measures the resulting pixels. It does not simply echo requested parameters. Helpful texture values alias the corresponding code shape, so requesting two conflicting aliases is a declared incompatibility. `single_index` conflicts with an explicit code shape. Retaining explicit incompatibilities makes valid requests exact without inventing a hidden precedence rule. The final battery measured 54,090 requests across 601 cases, 30 seeds per case and three bands: 51,840 accepted, 2,250 declared rejections, zero findings or warnings. A separate joint boundary probe generated and validated 2,060 of 2,560 requests and classified the other 500 as declared incompatible. These are request counts, not distinct-grid counts; exact details are in `checks/final-summary.json` and the underlying reports.

The seed-only episode context is created before the per-grid context. This preserves the shared observer's actual last-draw provenance. The first attempted ordering failed the added provenance regression; that failure and its exact intermediate source are retained.

## D2 — Preserve the executable authority; specify the clean mosaic domain

The true rule selects the unique largest monochrome 4-connected components of colors 6 and 7. Codes 1–4 select clockwise rotations of the first template and 5–8 select rotations of the second; blank code slots preserve empty tiles. Symmetry is lawful. All five canonical pairs include one fully rotation-symmetric template, which the baseline's all-asymmetric templates failed to represent.

The Racket implementation crops full rectangles. Color 9 is excluded when forming the code bounding box, but an internal 9 is subsequently processed as template B at four quarter turns. A 9 inside a template crop is also copied. The repair therefore places decor outside all three crops and validates crop purity, rather than claiming the authority ignores 9 everywhere. Ten independent hand-built fixtures, including these edge cases, were executed through supported Racket application before implementation; their source binding is explicitly baseline-era in `checks/semantic-analysis/`.

Equal square 2×2 or 3×3 template boxes, at least three cells in each unique largest component, disjoint clean crops, integer colors 0–9, input dimensions at most 30 and output dimensions at most 30 define the generator's clean tiling domain. Unequal or rectangular templates can sometimes execute under Racket's stride, overlap and clipping semantics, but are not advertised as ordinary samples. Expanding that domain would be a separate task. Rejecting it here is an explicit sampling restriction, not evidence that the authority has no output.

## D3 — Construct layouts and template families instead of falling back

Connected template masks are enumerated into finite cached libraries. Size-3 requests cannot fall back to a size-2 pattern. The libraries contain symmetric crosses/rings, sparse asymmetric five/six-cell shapes and dense asymmetric eight-cell shapes. Canonical sparse/symmetric pairs therefore occur in ordinary generation; dense asymmetry provides a separate witness against skipping rotation for dense templates.

Constructive disjoint placement supports all advertised input boundaries. Code can occur above, below, left or right of templates. Small-template profiles place code above both templates and put the color-6 template to the right of color 7, refuting the specific topmost-component and left-to-right template shortcuts. Every generated label continues to come from Racket. The Python decoder exists only for deliberately altered rivals and witness predicates.

## D4 — Cross nuisance features in a five-profile default schedule

The first repaired design coupled small templates, gaps and 9-decor. Independent review found that a solver could infer tile stride from decoration rather than template size. It also found that the first design omitted the canonical sparse asymmetric texture. Both findings led to failing regressions before the final repair; the first candidate's passing known-rival measurements are retained as intermediate evidence, not final proof.

| Profile | Template side | Code | Shape family | Purpose |
| --- | ---: | --- | --- | --- |
| `small_gapped` | 2 | Full interior blank column | Asymmetric small templates | Size, blank-slot and placement witnesses |
| `dense_full` | 3 | Full `2x3` or `3x2` | Dense asymmetric + symmetric | Dense rotation and decor/size crossing |
| `small_full` | 2 | Full `2x3` or `3x2` | Asymmetric small templates | Size witness without gaps |
| `dense_gapped` | 3 | Full interior blank column | Dense asymmetric + symmetric | Gap witness at size 3 |
| `canonical_sparse` | 3 | Full `2x3` or `3x2` | Sparse asymmetric + symmetric | Canonical texture support |

A seed-only flip decorates either profiles 0/1 or profiles 2/3; profile 4 has no decor. Every five consecutive indices cross template size with both gaps and decoration, and also cross gaps with decoration. Each declared rival has at least two witness profiles, so holding out any single example leaves a refuter among four demonstrations. The exact phase argument is in `checks/repair-review/final-review.md`.

The production sampler could invalidate an index-only argument by rejecting or deduplicating draws. We therefore measured actual accepted indices: 300 production lessons accepted all 1,500 consecutive requested indices with zero rejections. Separately, the reusable probe tested every cyclic start of the period-five schedule over seeds 0–19, four difficulty settings and all five single-query holdouts: 400 windows and 2,000 rotations. Every one of the ten live declared rivals was refuted by the demonstrations in every rotation. The 720 overlapping lesson draws contain 257 globally unique inputs; this is kept distinct from the 1,500 unique inputs in the production census.

Pure random witness frequencies were rejected as the main teaching contract because they would not ensure witnesses in each lesson. Rejection-based filtering was unnecessary once the constructive schedule passed actual sampler checks. The first period-two design was rejected because it allowed decoration-derived stride and excluded canonical sparse shapes.

## D5 — Keep difficulty active without narrowing controls

Difficulty changes the `small_gapped` canvas distribution: easy favors smaller search areas and hard larger ones. Every exact dimension remains available in each band. Other profiles retain substantial canonical size and palette support. The final profile floor accepted 5/5 canonical inputs and measured exact profile support of 9/20 easy, 14/20 medium and 9/20 hard. All 600 semantic-gate draws passed the declared strict predicate, whose `MIN_STRICT_FRAC` is 1.0.

The lawful `monotone_code` and `single_index` controls remain available as explicitly under-informative cases and are absent from default texture selection. The four-demonstration/one-query default guarantee is not extended to arbitrary controlled lessons, shorter lessons, or multiple queries. The required post-repair solve used two queries and is reported separately as visible-example solve evidence.

## D6 — Keep the patch small and the evidence replayable

The source delta touches six files under the assigned task: the generator, focused tests, the reusable probe and its README, task summary and notes. Audit targets `6347dcb736b5` and `d2f386d0e071` have findings and exact Racket counterexamples, with no source changes. Shared tooling proposals are prioritized in `FEEDBACK_TO_CODEX.md`; none was silently added to the allowed task patch.

All genuine failed iterations, dependency errors and solver revisions are retained. The 13,262,777-byte production census is stored losslessly as `checks/lesson-census.json.gz`; `checks/COMPRESSED_EVIDENCE.json` records original and compressed sizes and SHA-256 hashes. A small explicit JSON pointer occupies the original path. `python3 checks/manage_evidence.py verify` checks the bytes, and `python3 checks/manage_evidence.py restore` recreates the original report, replacing only its known pointer or an identical report. `checks/summarize_final.py` reads the compressed or full report and derives the compact summary without rerunning the checks. See `REVIEW.md` and `checks/handoff/` for the final exact-patch relocation results.
