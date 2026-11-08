# Migration and provenance

ARCpuzzles now contains the copied puzzle/generator library, shared helpers,
reference runtime, inherited linters and review tools, data authorities, and
associated notes. The public Python API, CLI, HTTP service, and review assignment
workflow are implemented locally. ARC2train now has the selected LoRA/RL
implementation; ARC2model has candidate import and independent inference. The
ARCagi2 source checkout is preserved. See [the shared migration map](repository-split.md).

Version0.5 adds ARC-native JSON/private tensor export, explicit unapproved archival
rule selection and native bare-expression support. The complete v0.3 one-seed
census and its subsequent compatibility fixes are documented in
[census classification](migration/census-classification.md). All53 v0.5 interface
tests pass locally and in a fresh isolated wheel. The older Kaggle generator
service remains in ARCagi2 until its import is requested. The earlier archive
copy was moved out of this repository; see [deferred imports](deferred-imports.md).

## Inventory

- 3,892 per-puzzle generators and 49 generic generators, each with its own home.
- 4,350 canonical puzzle rows, grouped by stable generator/task identity.
- Original generator files and tests, plus 12 battery stages and their common
  dependencies. Legacy review helper implementations are retained as shared tools.
- Canonical and base-rule authorities, public source puzzles, approval/review
  ledgers, and per-generator associated-note projections.
- The executable Racket bridge/prelude and GUIDE documentation.

The per-file source paths, hashes, source commit, and dirty/untracked source
status are in [import-manifest.json](migration/import-manifest.json).
The import used the working bytes, including existing uncommitted work.
`catalog/runtime_files.json` maps authored files to their execution paths;
`catalog/authority_files.json` identifies task-local base-rule authorities.
The import script records the initial extraction. Additional test/review-helper
dependencies and original-ID aliases were added during verification; the final
manifest and mappings include them. The historical script is neither a runtime
dependency nor a supported refresh command.

Copied originals retain their bytes. New summaries, workspace guidance, note
projections, catalog records, and public-interface code are identified separately
from those originals. No generator was relabeled or semantically rewritten by
extraction. Query approval checks current code/rule hashes against imported
review metadata; a copied review is not a new quality measurement.

## Independent execution

The authoring layout separates `generators/` from `shared/`. Each tool run copies
local shared code/data and the selected generator into a fresh ordinary runtime
layout. It includes the full canonical ledger and selected base-rule authorities.
The complete source-to-runtime mapping and hashes are recorded in that runtime.
This keeps existing gate behavior and original source paths working without a
mass rewrite of generators, symlinks, or imports into another checkout.

All-generator import checks prepare the complete library. Installed wheels carry
the same library under `arcpuzzles/library/`. A source checkout is not required by
a wheel installation. The only external execution dependencies are the declared
Python packages and a Racket executable; no source server or training job is used.

## Preserved boundaries

Caches, live databases, training/model artifacts, historical bulk review ZIPs,
and the LLM generator-authoring client were excluded. Selected review evidence
and associated notes were retained. Historical notes and scripts may mention
old source paths or old counts; they are provenance, not instructions to operate
the predecessor's resources.

`shared/tools/` is a storage location for inherited tools. Use the public `check`
interface or a prepared review workspace. Launching an arbitrary legacy helper
from the storage directory is not a supported invocation.

The API's default approval boundary is stricter than the raw review label:
449 entries currently qualify, versus 453 raw `reviewed_safe` labels. Of the four
excluded entries, `0e4861d08306` has a changed canonical rule hash;
`7c7796f15a18`, `generic_band_dock_gen1`, and `generic_dense_motion_gen1` lack a
canonical rule entry. These conditions remain visible; no label was upgraded.

See [verification](verification.md) for measured behavior and its limits.

Version 0.3 adds bounded mixed exports, public/private artifacts, grid/code chat
renders, full raw-instance rows, DSL token projections, executed mutations and
synthetic prefix traces through the copied serializers. A compatibility census
compares the current and retained historical generation routes. Tensor packing
and other legacy producer workflows still need full-route verification.
