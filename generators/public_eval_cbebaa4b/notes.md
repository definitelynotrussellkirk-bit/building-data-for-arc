# cbebaa4b — current authoring decisions

## Design and implementation plan
Reconstruct the unique translation-only assembly of input pieces, anchored at the
piece containing yellow (4). Overlap is allowed only between two red connector
cells. Every red cell must be paired, all bodies remain intact and inside the
canvas. Contacts need not have opposite normals: official test 1 includes a
perpendicular corner contact. Do not forbid body adjacency after assembly.

Two settings: `assembly_policy=assemble|deepest_piece`. The alternative builds
the red-contact graph of the solved placement, computes shortest-path depth from
the yellow anchor, and recolors the unique deepest piece's non-red cells cyan.
This graph is input-dependent and is unavailable before matching connector
constellations. Preserve exact canonical reference bytes for the default.

Plan: (1) tests and general Racket/Python reference against all four official
labels; (2) constructive varied assemblies, shuffled input placements and
prefix-stable four-query bank, minimum two teaching examples; (3) executed rival
self-review, count/privacy stress, protected preflight and source-bound causal
replay; (4) clean-source patch and inventory verification. Work in this isolated
ZIP extraction; no owner repository or shared source is edited. No native
acceptance or training admission is claimed.

## Verified result and limits
General reference: 4/4 supplied original labels; 21/21 task tests. Twenty-seed count sweep: 800 requests, 5,200 repeated-prefix pair instances, 200 distinct inputs, 400 matched-input comparisons, 2,000 masked public turns, 108 protected authoring evaluations. Four public preflight jobs pass. Original smallest-piece shortcut was executed against both demos and a legal counterexample; interior occupancy now varies independently of graph depth, and the shortcut is rejected. Bound eight-piece causal case replaces graph distance with Euclidean distance. Source only supports unique assemblies; Python refuses ambiguity/search exhaustion, Racket chooses its first assembly outside that admitted uniqueness grammar. Synthetic bodies use connected frames/stripes and distinct connector signatures; not a claim of full parent distribution coverage. Author self-review, not independent review. Owner registration, native qualification, exact-source acceptance and training admission are not performed.

Final privacy regression: extra metadata in demonstration/query dictionaries
is now excluded by the direct single-query helper, not merely by the saved-file
serializer. A failing test was retained, then both complete suites passed after
the whitelist repair. All cited preflight/witness bindings were refreshed.

Owner worker API correction: use the existing worker input/findings contract. Earlier author checks used the incompatible return convention. Reference programs are unchanged; owner preflight and native acceptance determine current readiness. See evidence/owner-base-api-repair.json.

## Current repeated-return reconciliation

- review-94ea28a8be9d115d: Preserve exact assembly/depth programs and original tree sampler as an episode branch.
- review-263639f01f39da2f: Retain cycle and dispersed 30x30 constructors and shortest-path versus longest-path lesson, alongside the accepted tree sampler. Programs unchanged; existing ordinary wrapper now consumes the same combined native family.
- review-970cdd2838340900: No new semantic source. Preserve focused audit/tests and rerun current protected labels and finite rivals in the private candidate.

Accepted default and prior program bytes remain unchanged. Evidence and unresolved input/phase witnesses: `evidence/reconcile-16/`. Private native qualification, fresh private native acceptance and accepted generation passed. Live owner publication and training admission remain separate.
