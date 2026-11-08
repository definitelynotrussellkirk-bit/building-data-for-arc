# Working notes: 5b18a320e97b

## Current decision

Retain the approved canonical generator unchanged and add a separate task-local `read_direction` prototype under `workspace/parametric/`.

- Allowed settings: `forward` and `reverse`.
- Original/default: `forward`, materialized as the exact pinned canonical Racket bytes (`c88b81c9786841551051d1c26625321375d4849229760bd0e40b7329fda63231`).
- Alternative: `reverse`, implemented by one guarded change around the unique `sorted-colors` expression.
- Invariants: ignore `0` and gray `5`; detect horizontal/vertical line orientation; preserve objects, occlusion semantics, and square stripe construction.
- Episode contract: choose once from the deterministic episode seed and hold fixed; demo/query counts are separate; retained evidence uses 3 demonstrations and 4 distinct queries.
- Labels: exact materialized Racket only. The Python generator is used for lawful input sampling, not label authority.
- Public boundary: demonstrations include outputs; queries omit outputs; parameter, seed, programs, counterfactuals, and query labels remain private; filenames derive only from visible challenge bytes.

## Retained checks

`tests/test_parametric_read_direction.py` covers exact default restoration, guarded reverse materialization, every labeled canonical record, invalid inputs, fixed-setting episodes, uniqueness/grammar coverage, declared-rival refutation, public projection, content-derived names, duplicate-visible-payload rejection, public-ID batch ordering, fail-closed evidence creation, source hashes, and independent bundle replay.

The exact evidence command and limitations are in `workspace/parametric/README.md`. This work is proposed/unapproved and does not modify `generator.py`, canonical authority, production axes, or catalog status.

## Resolved packet-level follow-ups

The inherited root test used a removed fixed module path and a fixed-depth canonical path. This review converted it to the packet's portable `reviewer_support.find_root`, `load_selected_generator`, and `canonical_pairs` loaders; the complete task suite now passes 125/125.

The inherited public writer sorted its report only after emission and therefore carried `public_identifier_status=external_correction_pending`. The replacement audit preflights every visible-byte ID and collision before writing, emits in sorted ID order, preserves the original pending manifest for review, and passes the independent 16-file public-export checker. This resolves the reviewer-side hold only; owner acceptance and variant approval remain separate.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/5b18a320e97b/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## Review `review-be46772efd20bd43` — native read-direction family

Built a native, source-bound `read_direction={forward,reverse}` adapter. The `forward` program is byte-for-byte the canonical authority; `reverse` changes only the ordered-color binding after the same input-dependent orientation and spatial-order analysis. The production generator remained unchanged.

The adapter supports 2–6 demonstrations and 1–4 independent, prefix-stable queries. Its four controller-side queries are distinct and reach 30×30. A finite self-review tests twelve intended/shortcut candidates; the first two demonstrations leave only the selected setting. The protected audit passed 8 jobs and 128 Racket evaluations, and the native qualification passed both settings on seeds 0 and 17 with 32 protected evaluations.

The inherited prototype had `public_identifier_status=external_correction_pending` because its old writer sorted only after emitting files. The replacement audit preflights all visible-byte IDs and collisions, then writes in sorted ID order. The original pending manifest is retained under `workspace/parametric/evidence/reviewer-original-manifest.json`; the current source inventory no longer carries the stale hold. `checks/5b18a320e97b/public-export-check.json` independently reports 16/16 public exports valid.

Sequential dependency: first infer horizontal versus vertical orientation and the spatial color order from the input; that intermediate chooses the sort axis and stripe layout before forward/reverse order is applied. Forcing the wrong horizontal intermediate on a qualified vertical case changes 12 final cells. The official witness checker returned `reviewer_replayed`.

Limits: finite seeds and authored rivals only. Qualification is reviewer evidence, not owner acceptance, measured learning, or training admission. Exact-source owner acceptance remains pending.
