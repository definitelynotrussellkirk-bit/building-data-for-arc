# Real final receipt audit

Both commands recorded in real-receipt-commands.json ran from WORK/repo against complete real shared receipts. The tool source was unchanged (SHA256 f160bf6a3e96202332fb00b6ad741d5e36e0444a2fec500fe74623e5c8603105).

## Retained original distribution, rescored with current rivals

`python generators/747486860e56/workspace/audit_rival_coverage.py ../checks/lesson-rescore-v1.json --canonical-census ../checks/lesson-census-final.json --out ../checks/tooling/rival-coverage-v1-rescored.json`

Exit1: finite_coverage_gap. The source-bound canonical join succeeds. Both SEMANTIC_RIVALS:monochrome_corner_else_first and LESSON_COMPETITORS:monochrome_corner_else_first fit2/10 canonical pair occurrences yet survive all300 original generated lessons and all2,100 pair holdouts. The shared rescore is ambiguity-green, demonstrating why query-ambiguity checks alone can miss a sampled distribution shortcut.

The tool intentionally retains two namespace-qualified rows. The receipts do not establish callable declaration identity, so the summary does not collapse or count them as independently discovered semantic behaviors.

## Final repaired distribution

`python generators/747486860e56/workspace/audit_rival_coverage.py ../checks/lesson-census-final.json --out ../checks/tooling/rival-coverage-final.json`

Exit0: no_finite_coverage_gap_found among the16 declared namespace rows. The conditional rival is refuted in all300 final lessons and all2,100 holdouts. The smallest-color rival (canonical fits8/10) is also refuted throughout. Canonical-fitting corner-exclusion rivals survive138 neutral-context lessons and monochrome-main rivals survive146 monochrome-context lessons; they agree with those sampled labels, so these survivors do not constitute a canonical-failing distribution gap or imply query ambiguity.

## Interpretation and limits

Both reports cover300 lessons,2,100 generated pair occurrences and2,100 holdouts. A refuted lesson/holdout means some demonstration label refutes the rival. It does not imply that every query prediction or every pair prediction differs. Holdouts reuse the same labels and do not add independent generated examples. The canonical10 pairs are pair occurrences from training and augmented variants, including duplicate examples; they are not10 independent semantic witnesses.

This is a finite coverage check of declared rivals only. It cannot prove universal identifiability, discover undeclared rivals, verify callable identity across namespaces, establish purity/determinism of rivals, or independently re-execute reference labels. Hash and completeness checks protect the receipt join and internal consistency; the scoring/runtime claims remain those of the shared source-bound receipts. No approval or training-admission state changes. No WORK/solve or blind-solve files were read.
