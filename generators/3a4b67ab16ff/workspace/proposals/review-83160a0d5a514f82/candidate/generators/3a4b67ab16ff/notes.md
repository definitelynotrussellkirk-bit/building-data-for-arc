# Working notes: 3a4b67ab16ff

## Current decision

Generator `3.1.0` keeps canonical rule hash `32c694357bd0` and adds a `split_extrema` curriculum profile. Four non-corner markers jointly provide the top, bottom, left, and right extrema, so a first/last-row-major-occurrence shortcut computes the wrong box. The machine-readable rival is `endpoint_only_bbox`; its bound witness is `split_extrema_refutes_endpoint_only_bbox`.

Adding the profile initially diluted the fixed default schedule enough to miss canonical public profiles in one band. The final schedule retains the new lesson and weights the four existing public profiles by 7, yielding final strict support in every band and 19 exact canonical-profile hits across 60 pinned draws. `generate` now strictly rejects bool/non-integer seeds or sample indices and negative sample indices.

## Parametric proposal

The task-local `workspace/parametric/prototype.py` proposes one hidden episode setting, `layer_order=ascending|descending`. Ascending is the exact canonical program; descending reverses only the color traversal. Paired settings share input sampling, each retained episode has 3 demonstrations and 4 distinct queries, and all seven inputs distinguish the rival setting under exact Racket. Public exports omit settings, seeds, programs, and answers. This remains a proposal, not a production API, variant approval, or training admission.

## Authority and verification

Canonical `puzzles.jsonl` and archival `raw_code` are unchanged. The selected base solution's active `target_code` was synchronized byte-for-byte to canonical formatting, with execution parity preserved. Focused authored tests pass 17/17, and the twelve final source-bound stages pass. Aggregate task tests remain blocked at preflight by the issued frozen fixture's fixed parent-depth root lookup; that fixture remains byte-identical to baseline.

## Next useful action

Maintainers should replay the return, migrate the frozen fixture to `reviewer_support.find_root`/`canonical_pairs` in packet-generation source, and evaluate the `layer_order` proposal separately from the production repair.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/3a4b67ab16ff/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
