# Current rule and authoring decisions

Split the even square into four equal quadrants. Count all nonzero cells in the upper-left for output height and in the upper-right for output width, irrespective of color or connectedness. The lower-left is a palette grid and the lower-right a stencil. Expand each palette cell into a constant quadrant-sized block, repeat the stencil across this backing, and use its nonzero cells as foreground. Zero stencil cells expose the backing. Crop to the two counts.

The original empty-stencil demonstration establishes an identity fallback: when the lower-right is entirely zero, repeat the lower-left tile directly instead of expanding each palette pixel to a quadrant-sized block. Black in the palette is a real fill value, not another transparent layer. All five original demonstrations and both supplied test-gold outputs match the general Racket rule. There is no supplied-grid lookup.

## Parametric family and dependency

`background_sampling=block` is the byte-exact reference default. `periodic` repeats the palette at cell scale even when the stencil is nonempty. It is a documented generative alternative, not a claim about the original task's intended answer. The input grammar is even square grids 2..30 with equal quadrants, 1..30 nonzero cells in each counter, and arbitrary palette/stencil colors. Quadrant capacity also bounds the coarse palette indices. Rectangular or zero-count inputs are rejected rather than silently approximated.

A derives the output counts and the input-dependent backing color grid. B overlays the periodic nonzero stencil onto that backing. The causal counterfactual keeps counts, dimensions and the stencil unchanged, but substitutes an all-zero backing; final hole colors change.

## Sampler and self-review repair

The independent seed streams vary counter colors, pixel positions, counts, palette texture, stencil density and private query order. Counts vary for the same quadrant size, so canvas dimensions do not identify the output shape. The full query bank is shuffled before slicing; 2–6 demos and 1–4 queries are independently prefix stable and matched across settings. There are small 4×4 input cases, partial tiles, blank and fully opaque stencil branches, and a 30×30 input/output stress with substantive content.

Initially both demonstrations contained a nonempty stencil. The `empty_large_hole` rival ignored the identity fallback, fit those demos, and failed a legal empty-stencil query at seed 0. `tests/empty_stencil_counterexample.json` retains the inputs, both programs and six protected-Racket executions with match pattern [true,true,false]. The first demo now always teaches the empty identity; the second teaches a nonempty multi-tile composition and distinguishes the settings. A regression and 32-seed audit check the repair.

Thirteen executable rivals cover opposite sampling, swapped counts, occupied row/column counts, first-color-only counting, constant/transposed palette, ignored/opaque/transposed stencil, first-tile-only output, the wrong empty fallback, and rounding to complete tiles. Some rivals coincide with the intended periodic setting on the admitted domain; only a demonstration survivor that disagrees on a query is a dangerous survivor. Finite audits do not establish universal uniqueness.

## Reproduction and privacy

`authoring_tools.py audit --seeds 32 --out ...` checks all supported request-count prefixes, matched inputs, private-metadata/future-query invariance and bounded protected-Racket agreement for both selected rules and all rivals. `export --preflight ... --out ...` and `verify-export --preflight ... --bundle ...` use the shared current-source preflight validator. Public files hash only their own one-query visible bytes; the bundle/listing/private manifest remains controller-only. Duplicate views and existing destinations fail before writing.

Native owner registration, source review, exact-source qualification/acceptance and training admission remain pending. The final code examination is author self-review, not independent review.

Final export-verifier review: negative tests showed that changing private manifest task ID, schema, admission flag, public-file list or limits was not rejected. The verifier now reconstructs and compares the entire canonical manifest byte-for-byte, in addition to public payloads, file sets and source binding. All five tamper regressions pass.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.

## Current repeated-return reconciliation

Excluded incompatible count-sized stencil/resize interpretation: 16/20 incoming defaults disagree with preserved quadrant-block compositor. stretch/repeat semantic differences remain unmerged. Partial: primitive_snake is an explicit distinct alternate using the exact incoming snake program. Its primitive-raster canonical differs from incumbent block semantics on 16/20 inputs; incoming constructor rows are admitted only where preserved default agrees and all settings execute. Primitive-raster setting and rectangular/period-conflicting sampler rows remain excluded. Not fully incorporated. Exact incumbent programs, empty-stencil fallback and entire original query sampler retained. Ordinary difficulty=None owner repair preserved byte-for-byte.

All original accepted programs and defaults remain exact. Two to six demonstrations and four shuffled, sequential private queries are supported. Finite rival checks and sampled protected labels are bounded evidence. Fresh private native qualification and acceptance re-execution passed. Live publication and training admission remain separate. Source-bound decisions and witnesses: `evidence/reconcile-18/`.
