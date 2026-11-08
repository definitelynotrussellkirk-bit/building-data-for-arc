# Working notes: 7f181d3b0012

## Current generator contract

The authoritative transform is `vconcat(g, flip-ud(g))`. A lawful input is a
rectangular colored grid within the declared size and palette envelope.
`single_row` and `ud_symmetric` are intentional opt-in generalizations;
three-one-cell binary patterns are also lawful, even though the four official
examples have one-counts exactly in `{2, 4, 5}`. Default draws remain
UD-asymmetric. The strict canonical mixture also requires LR asymmetry.

## Selected repair and evidence

Version 3.1.1 rejects every unknown override key, including keys whose value is
`None`, before drawing. At original source SHA-256
`70eb2d7ac8dadba5519d165b4f9d81ecb42ca586a47c264b6dfa284a1f9e5073`,
seed 23/sample 9 accepted the audit's unknown key and returned the default grid.
The regression fails on those bytes and passes after repair.

The canonical branch previously sampled 2..5 one-cells. Sampling 3 diluted the
promised demonstrated family: seeds/sample indices 0..599 produced strict
counts 130 easy, 144 medium, 133 hard, below 25% in every band. It now samples
`(2, 4, 5)` and retains both asymmetry filters and its valid bounded fallback.
The same census on 3.1.1 gives 190/600 easy, 187/600 medium and 167/600 hard.
The mixture probability remains 30%; finite draws do not guarantee a floor for
every seed set. The version bump intentionally changes keyed realizations.

`LESSON_COMPETITORS` now names pure vertical-duplication and rotate180-bottom
rivals. The existing worker rejects an automatic lesson if a declared rival
fits all demos but disagrees with a query; explicit-count mode retains a
`diagnostic_unsupported` verdict. A symmetric-demo/asymmetric-query regression
reproduces the previous `not_declared` verdict and the corrected behavior.
An asymmetric demo refutes both rivals. Symmetric queries remain lawful when
rivals agree, and a UD-asymmetric/LR-symmetric demo isolates the rotation rival.
This is a bounded declared-rivals contract, not universal rule identification.

Tests use `reviewer_support.find_root`, `load_selected_generator`, and
`canonical_pairs`, fixing the inherited obsolete runtime paths. The final
portable task-tests stage passes 8 tests and 85 subtests without import-path
warnings. Focused authoritative Racket execution matches 33 labels: four
official examples, 24 default draws spanning all bands, and five boundary or
degenerate inputs. Executed canonical rule hash is `738584ea6289`, with rule
text SHA-256 `c4cc5905ef94295b760ec9492106bb171994376320f57dc44e952d00017c9cd5`.
Evidence lives under `checks/7f181d3b0012/` in the return.

## Bounded adversarial findings and limits

After repair: 20 typo/null-key probes reject, all five known axes accept `None`
as no override, 900 additional default draws remain valid and UD-asymmetric,
300 additional direct canonical-family draws are strict, and a forced 200-retry
fallback is strict. The lesson probes above cover both rival surfaces. No new
failure was found in this bounded pass.

Before changing helpers, 400 focused palette/symmetry cases and 22,500
asymmetric texture cases found no realized issue. The palette and symmetry
helpers were therefore left unchanged. This does not prove their complete
correctness. The review's unknown-key, strict-mixture and missing-rival concerns
are addressed by this proposal; its broader self-check and authority-text
observations were not separately repaired or resolved. The canonical and base
rules were not edited, and no broad battery, full semantic gate, approval,
audit-status change, or training admission is claimed.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/7f181d3b0012/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
