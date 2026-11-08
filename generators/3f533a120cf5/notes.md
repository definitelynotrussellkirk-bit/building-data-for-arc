# Working notes: 3f533a120cf5

## Current decision

Keep the approved production generator and canonical rule unchanged. The task now has a separate **unapproved task-local prototype** under `workspace/parametric/` with two episode-fixed parameters:

- `key_target`: `gray_cells` (canonical default) or `bbox_holes`;
- `key_order`: `forward` (canonical default) or `reverse`.

The invariant reasoning remains: find the gray bitmap, crop its bounding box, locate the separator bar and adjacent repeated-color key, then paint the crop from the key plus separator color. Only the cells receiving key colors and the key traversal direction vary. Inputs retained for the prototype must be lawful under the selected generator, distinct within an episode, and produce four different predictions across the four declared settings.

The canonical/default program is byte-identical to Racket SHA-256 `f6264cbb3adf5c325cc07efd5c4497420ad999965faecd3f55d883ffdcee8a02` and normalized rule hash `df7e059f3faa`. Production generator SHA-256 remains `c63333b9cd8acc75cd147d76deff12590f9267cb7286d9d18f14cddf2bf8cd5c`; the canonical ledger remains unchanged.

## Retained evidence

`checks/parametric/paint-semantics-v1/report.json` records four source-bound episodes, one per setting, each with 2 demonstrations and 4 distinct queries. Every label was executed by its retained exact Racket program, an independent Python mirror agreed, demonstrations alone eliminated the three declared rival settings, and public files contain only demonstrations plus unlabeled query inputs with visible-byte-derived IDs.

The portable task-test stage initially exposed a fixed-parent-depth path defect in the issued legacy test. `tests/test_generator_3f533a120cf5.py` now uses `reviewer_support.find_root` and `canonical_path`; the staged rerun executed all 17 task tests successfully.

Both bounded supplementary tickets completed. The `5553241d87bf` `scene_profile` boundary accepted `public_1` and rejected undeclared `public_4`. The existing `04a27ff51304` teaching-ambiguity witness reproduced exactly on unchanged source and remains unresolved; this work does not clear it.

## Limits and next useful action

Identifiability is proved only against the finite four-setting family, not against every conceivable alternate rule. The prototype is neither production approval nor training admission. A useful next review is maintainer assessment of whether these two parameters are semantically valuable enough for a separately designed production parametric API; if so, expand the rival set before admission rather than changing the canonical authority.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/3f533a120cf5/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
