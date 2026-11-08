# Working notes: 0f075657ddbb

2026-09-28 review, assignment `review-28df04f9d685dce9`.

The original associated-notes ledger is empty; undocumented design motives remain unknown. The review reproduced ignored axes, selector clamping, duplicate self-check definitions and rejection of two canonical no-op inputs. The replacement makes scene geometry and overrides explicit, keeps the canonical labels unchanged and introduces falsifiable rival counterexamples.

Failed iterations remain in the returned `checks/`: the first rewrite over-sampled identity scenes and missed compact morphology; a diagonal seed/index call aliased its schedule; strict override validation exposed our transient zero-frame branch error; real after-policy validation exposed an eight-demo lesson incompatible with the serializer's maximum five. The final four-demo, seed-conditioned regime addresses that interface without suppressing the gate.

Read `workspace/README.md` for runnable commands and the next-agent handoff. Detailed decisions and limitations are in the return's root DECISIONS.md. Named rivals cover whole-grid red counting, leading-prefix counting, overwriting protected cells, and clamping an overflow selector. These finite alternatives do not exhaust all possible shortcuts.

Do not widen acceptance to arbitrary executable Racket inputs or silently remove lawful identities. Do not claim a model-level improvement from these generator probes. Default thin-frame sampling and unrestricted offset geometries remain future curriculum work; canonical acceptance and exact Racket fixtures already cover the thin-frame rule branch.
## Current reviewer considerations

Source SHA-256: `147f6094719fde548df05307f7360821f719e6e2be6aaef47ab44d8370fa324e`.

# Decisions — 0f075657ddbb

Assignment: `review-28df04f9d685dce9`. Canonical H72; generator 2.1.1 → 3.0.1.
This review changes the input sampler and checker, not the canonical puzzle.
The inherited notes and associated-notes ledger contain no substantive rationale.
Where reasons below are inferred from code rather than documented, they are marked unknown.

## Authority and labels

**Original:** canonical `program_solution`, selected `target_code`, and archived `raw_code` were not byte-identical; the selected target differed only in comments. The baseline authority check reported executable parity but source divergence. **Decision:** keep the canonical ledger and all example labels byte-for-byte unchanged. Align only the bound selected target's comments with the canonical source. `checks/authority-comment-sync.json` proves the comment-stripped token streams match. Pin `RULE_HASH = 99635e96d174` and retain the canonical program SHA-256 in every reference probe. A Python mirror is a diagnostic, never the training-label authority. **Rejected alternative:** redefining the rule to make missing selectors illegal; two canonical pairs are identity cases.

## Scene grammar and validation

**Original:** a second `self_check` silently replaced the first. It rejected missing markers, existing cyan, and single/no-frame branches, and used yellow component count without perimeter validation. Rationale unknown. **Decision:** one checker validates rectangular integer grids, 0..9 colors, complete color-4 perimeter components, strict nesting, separated borders, and a selector header. A scene must contain background 0 and at least two nonzero colors. This rejects uniform/singleton/line/2×2 impostors without pretending every executable Racket input is an intended training scene. Missing markers, overflow selectors, frame-free distractor scenes, and one frame are accepted when otherwise in grammar. **Limits:** the checker deliberately covers a scene grammar, not the entire Racket program domain. Disjoint rectangles, malformed yellow components, touching frames, and one-color inputs remain outside it. Thin 2-high frames are accepted, including canonical examples, but the default constructor uses a minimum 3×3 inner frame.

## Size and difficulty

**Original:** nominal grid dimensions were advertised but ignored. New defaults mostly left the canonical scale in the first iteration: 0/60 exact-profile and 3/60 envelope hits. **Decision:** use a 65% compact / 35% broad proposal mixture when compatible with requested geometry. Compact layouts mix generic square and rectangular canvases, height 11..14, width 12..16, with 2..3 foreground colors. Broad layouts retain larger canvases up to 30×30 and complexity-dependent ceilings. This uses scalar morphology, not stored canonical input/output arrays. Separate keyed layout streams by difficulty avoid duplicates when the same seed/index is sampled across difficulty bands. **Probes:** a new-seed distribution test (`10000..10239`), the fixed profile gate, 1,200 independent Racket-labeled draws (`20000..20399` across three bands), and exact size overrides. **Limits:** the compact band deliberately overlaps across difficulties; difficulty is not a guarantee of strict per-instance complexity ordering.

## Frame count, gaps and placement

**Original:** frame counts and gaps were implicit random choices; overrides were silently ignored. Frames shared fixed top positioning and uniform insets. Original rationale unknown. **Decision:** enumerate a small feasible structural domain before constructing any grid; never retry, clip, or fall back. Expose exact `n_frames=0..5`, `band_gap=2..3`, `position_bias=concentric|offset`, and `grid_h/grid_w=11..30`. `band_gap` is the minimum per-side inset, not the count of blank cells, and is undefined for fewer than two frames. Explicit use in that case raises a structured incompatibility. Offset introduces an asymmetric inset while preserving the exact minimum gap. Translation includes edge placements. **Rejected alternatives:** silently resizing a pinned canvas or reducing frame count; remapping an impossible request into a different axis value. **Limits:** offsets are currently one extra top inset at one nesting level, not arbitrary offsets on all sides. Default innermost size ≥3 ensures the overflow-vs-clamp contrast can actually change cells.

## Selector and curriculum

**Original:** only positive, in-range selectors were generated, and `k_select` was clamped. **First iteration:** four profiles alternated first/last/missing/overflow equally; `(seed+index)%4` aliased to half the profiles for callers using `(i,i)`. A later eight-profile version reduced identity mass but failed the real after-policy contract because `EXAMPLES_NEEDED=8` exceeds the serializer's maximum five.

**Final decision:** mix seed through a deterministic BLAKE2s phase, then cycle four sample indices: first rank, last rank, random valid rank, and one no-op. Each seed fixes its no-op regime to missing **or** overflow; different seeds cover both. `EXAMPLES_NEEDED=4` fits the serialization contract. A same-seed overflow query has a prior overflow demonstration because the regime repeats every four indices. A first-rank example always uses a non-prefix selector and includes a protected off-row red contrast; every four consecutive demos thus refute the other three named rivals. This is checked across 160 seed/phase lesson combinations and by the Racket-backed semantic gate.

Nominal identity rate is 25%; independent sampled rate is measured, not assumed. Exact `k_select=0..6` is never clamped. **Probes:** diagonal seed/index coverage, explicit endpoints, serializable lesson tests, and actual Racket execution. **Limits:** the finite-rival lesson check is not proof of universal identifiability. Both no-op types occur in the dataset but not necessarily in each lesson. The program still permits incidental identities, for example selecting a thin frame with no interior.

## Palette and distractors

**Original:** texture/palette/position controls were mostly decorative metadata; no off-row red or selected-band nonzero clutter distinguished plausible shortcuts. **Decision:** `palette_size=2..6` is the exact number of distinct *nonzero input* colors. Semantic colors 0/2/4/8 never get remapped. Texture affects preference ordering for additional colors. Distractor clusters, off-row red, preexisting cyan, and protected in-band cells force reference-preserving decisions. The marker count reads row 0 only. **Rejected alternative:** uniform recoloring, which changes this color-specific task. **Limits:** generated clutter is deliberately sparse, not arbitrary foreground occupancy. Palette-texture preference is stochastic, not an exact observable semantic value.

## Overrides and impossibility

Every named numeric axis rejects booleans, fractional values, out-of-range values and strings; unknown keys fail loudly. Grid-observed metadata checks size, frame count, selector count, foreground palette, offset and gap. Multi-axis failures use specific static constraints or `IncompatibleOverrides.incompatible_axes`; a generic `ValueError` is not treated as proof of intended infeasibility. This strict policy caught our own transient zero-frame regression: evaluating an inactive random active-selector branch called `randint(1,0)`. Eight failing regression cases were added and fixed before the final battery. Earlier failed receipts and source snapshots are retained, not relabeled.

## Reference testing and reusable tooling

`workspace/review_probe.py` stages a source-bound independent runtime, invokes the canonical Racket program, checks mutation and repeat determinism, and stores exact inputs, reference outputs, parameters, source hashes and first rival counterexamples. It supports another task ID, a baseline generator copy, held-out seeds, and explicit edge fixtures. Pair normalization supports both a singleton `test` object and digit-string grids encountered in this library. Its first staged-worker path bug and the inadequate original portability test are retained in evidence; the corrected test creates a genuinely shallow `/tmp` directory.

The public `arcpuzzles check` wrapper hardcodes `phase=before`, even for an output directory named `after`. `checks/run-strict-after.py` runs the unchanged underlying battery with real `after --fresh --keep-going`. No shared gate thresholds, admission labels, manifests, or safety evidence were edited.

## Unresolved scope

This is a generator correctness/distribution review, not evidence that a trained ARC solver improves. Arbitrary programs may still fit the demonstrations; only four explicit rivals were tested. Default generation does not yet systematically teach thin-frame/empty-interior examples (canonical acceptance plus a Racket fixture cover them), unrestricted asymmetric stacks, or dense protected clutter. Those are bounded future curriculum extensions, not reasons to silently widen this patch. The two other assigned audits are findings-only, with their sources unchanged.

## Current native extension (2026-10-25)
Design: `relay_policy=fill_only|key_relay`. Preserve the exact canonical fill.
The alternate uses the magenta key adjacent to newly filled cells to derive an
area, then recolors the unique blue object of that area green. The source key
and remote receiver may have different shapes. This is contextual gating from
a computed intermediate, not a claim of iterative physics.
Approaches considered: reversing frame rank is too shallow; filling another band
adds no new object reasoning. The area relay retains count/rank/band reasoning
and adds cross-object measurement. Production source stays unchanged.
Execution plan: (1) pin hand-derived relay and request/privacy tests; (2) implement
constructive matched-input scenes and exact Racket composition; (3) execute
nearby rivals, repair teaching holes, then source-bind qualification and a causal
counterfactual. Work takes place in this isolated extracted packet; no live
checkout or remote branch is modified.

Native self-review: the first sampler draft could put a six-cell key in a
five-cell inner width; the existing count sweep exposed it. The declared family
now constructs widths 26–30, satisfying the geometric inequality without retry
or key truncation. A separate test exposed that generated receivers were all
rectangular for the selected areas; irregular four-/six-cell receivers now force
cell count rather than bbox area. Hand-derived fixture and real Racket agree.
The completed bounded audit at workspace/parametric/evidence/current-run2 covers
20 seeds, 800 requests, 5,200 repeated-prefix pair instances, 200 unique inputs,
400 matched-input comparisons, and 2,000 public turns. 182 protected evaluations
checked exact settings and authored rivals. No tested wrong rule fits all demos
and differs on a query. One earlier audit command was externally interrupted;
its empty directory is not claimed as evidence. Production source is unchanged.
Current-source owner acceptance is still required; training_admitted=false.
