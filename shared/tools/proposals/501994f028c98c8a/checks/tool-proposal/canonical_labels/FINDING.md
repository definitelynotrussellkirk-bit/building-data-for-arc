# Optional canonical-label gate — proposed

The reusable authoring checker executed all available canonical labels for both controls: **623cca1dd5a8: 3/3 match** and **a92bb76c10ef: 5/5 match**. The counting-label suspicion was not reproduced. No canonical file, rule, generator, or shared source was changed.

Twenty focused tests passed. The explicit corrupted-label control changes one copied expected cell, reuses the retained actual Racket outputs, and returns the required mismatch exit **1**, with four matches and one exact mismatch witness. It is an intentional demonstration, not a natural model failure or a source-data defect. The saved source, ledger, program, generator, runtime, and negative-control bindings were rechecked successfully.

The future shared-tool proposal is a low-copy private label-consistency gate before other data-admission checks. It hashes every source binding, checks all variants without trusting a stored training anchor, rejects conflicting labels for an identical input, retains shape-safe discrepancies, and distinguishes mismatch (exit 1) from execution/data errors (exit 2). The implementation uses the existing raw Racket application path inside ArcExecutor; the internal coupling is explicitly documented. A consistency pass alone does not establish generator quality, teachability, or training admission.

Retain this full folder as `checks/tool-proposal/canonical_labels/`. Exact replay commands, observed exits, source hashes, and evidence paths are in `commands.json`; source and usage are in `canonical_labels.py` and `README.md`. Reports are private authoring evidence containing labels and reference programs.
