# Current design and implementation plan

Parent: bf45cf4b; public-parent.json is immutable provenance. No prior implementation exists.

Canonical: infer the modal background; find two 8-connected foreground groups, a monochrome stencil and a multicolor tile. Replace each occupied stencil cell with the tile; empty stencil cells become background blocks. Preserve the original tight stencil and tile bounding boxes.
Alternative: segment the stencil under four-neighbor adjacency, select the largest region (reading-order tie break), and use only its cells in the same expansion. This retains rather than simplifies the parent reasoning. The intermediate is the selected stencil-cell set in original stencil coordinates; tile expansion consumes it.

Plan: (1) regression tests, Python geometry and general Racket rule; (2) matched-input deterministic sampler, smallest two-example teaching prefix, native adapter and private presentation; (3) bounded adversarial audit, original-label protected Racket replay, source-bound preflight and wrong-component witness. No owner acceptance or training admission.

Scope: stdlib Python; resources confined to workspace/parametric. No gold/example lookup in executable rules. Review-only prototype, not registered. Workspace is a fresh extracted copy, with no .git repository; source baseline is the packet manifest.

## Current evidence and limits

The general rule matches all three original demonstrations plus provided test gold in protected Racket. The current source-bound receipt is checks/public_eval_bf45cf4b/preflight-final/preflight.json, authoring-only, not native owner qualification. The 32-seed × two-setting audit covers 64 episodes, 640 visible pairs, nine executable rivals, 40 protected generated labels, and 54 protected rival evaluations. All nine rivals are refuted by the first two demonstrations. Every source query bank contains a genuine 30×30 input/product case. Input supports necessarily remain small because stencil-size × tile-size must not exceed 30; moving both roles to opposite input corners spans the canvas, and the output mosaic has substantive repeated content.

Fixed before final preflight: an unsupported Racket make-grid call in the flat-tile rival (now empty-grid); every declared rival now has a live protected-runtime regression. Also reject tied background modes instead of relying on divergent Python/Racket tie-breaking. The first hand-authored test fixture was corrected because its claimed diagonal bridge was actually disconnected; literal expected cells were updated independently.

Sequential witness selects the smallest instead of largest four-connected mask component on the exact preflight stress query; protected execution and independent replay change 480 output cells. Python labels are claims until Racket-replayed. Finite tested rivals do not prove uniqueness against arbitrary rules. Native owner registration, canonical source review, qualification, acceptance, and training admission are not performed.
