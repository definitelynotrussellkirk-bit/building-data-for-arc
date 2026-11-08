# Working notes: b39674306606

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-25 native parametric review `review-905638ee737372d6`

The production generator and canonical Racket authority remain unchanged at SHA-256 `ff480f1799acf6aa5c1c83c3c566ba3868a05bbcd947c07737262e348947649a` and `c78264ef8c54240970643145f93fc924be2e21f7bdeab3368e426bb56ec46c21`.

A native episode-fixed family now exposes `frequency_target=singleton` (the exact canonical default) and `frequency_target=most_frequent`. Both settings first extract translation-normalized exact object shapes and their frequencies, then select either the unique singleton class or the unique maximum-frequency class and paint all selected cells cyan. Inputs contain one singleton, one pair, and one triple of equal-area shapes; the singleton is a D4 transform of the pair while the triple is not D4-equivalent, so size-only and rotation/reflection grouping shortcuts do not identify the rule.

The family supports independent 2–6 demonstration and 1–4 query counts with stable prefixes, matched setting-neutral inputs, four distinct private queries, and one-query public projections. The 30×30 query contains 108 foreground cells, touches every boundary, and differs by 72 cells across settings. The two-demo prefix eliminates the alternate setting and retained position, frequency, D4, color, area, and all-object shortcuts.

Protected evidence: 17 staged tests; a 96-evaluation self-audit; 40 native qualification labels; and a source-bound causal replay where replacing maximum-frequency selection with singleton selection changes 20 cells. The owner still needs to qualify and accept the exact integrated source; `training_admitted` remains false. Finite rivals/seeds are strong bounded evidence, not universal identifiability proof.
