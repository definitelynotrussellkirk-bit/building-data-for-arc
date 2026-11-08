# Independent finite-batch curator verification

The optional lesson curator passed the complete targeted follow-up. It repaired
all 44 bundles with an observed ambiguous holdout and separately strengthened
all 27 answer-equivalent bundles without refuting evidence. The resulting finite
export contains 300 lessons, with both declared rivals refuted in every one of
the 1,200 single-query holdouts. All 300 original queries are preserved.

This result does not repair or relabel the raw sampler. Its original 11 ambiguous
production lessons and 44 ambiguous rotations remain recorded in the independent
`checks/lesson-census/` report. The 27 extra bundles were never labeled erroneous
or ambiguous: their rival agreed with every recorded answer, but the strict
export policy required demonstrations that actually refute it.

## Before and after

| Measured quantity | Original raw census | Checked finite export |
| --- | ---: | ---: |
| Lessons | 300 | 300 |
| Demonstrations / queries per lesson | 3 / 1 | 3 / 1 |
| Original production ambiguities | 11 | 0 |
| Ambiguous single-query holdouts | 44 of 1,200 | 0 of 1,200 |
| Bundles with both rivals refuted at every holdout | 229 | 300 |
| Bundles answer-equivalent to the global-singleton rival | 27 | 0 |
| Distinct input hashes | 1,200 | 1,200 |

The targeted set comprised 70 easy lessons and one medium lesson. Each of the
44 ambiguous bundles needed one demonstration replacement; each of the 27
answer-equivalent bundles needed two. There were **98 replacements** in total.
The other **229 raw bundles were retained unchanged**, and every original query
input and output remained equal to its census pair. Curation did not mutate the
caller's lesson objects. Public results were checked to contain exactly the
three labeled demonstrations and the query input, with no query output or
private metadata.

## Independent checks and actual Racket calls

The batch used one reusable curator executor with the original deterministic
case seed, difficulty band, and recorded `next_sample_index`, with a maximum of
128 candidate attempts per lesson. It attempted **413 candidates** in total;
the observed per-lesson range was **1 to 25 attempts**. The curator made **697
actual Racket label calls**, measured from the executor counter and checked
against each returned report. This comprises 284 original-pair checks plus
413 candidate evaluations.

A separate public `Catalog.apply` execution then freshly labeled all **284 final
pairs** from the 71 curated lessons. It uses the same public controller as
`arcpuzzles apply`, which accepts at most 64 inputs per call, so the verification
used chunks of 64, 64, 64, 64, and 28. Each chunk created its own isolated public
runtime. All five original receipts are retained together in
`racket-verification.json.gz`. Every output exactly matched the curated label.

The follow-up therefore made **981 actual Racket label calls**: 697 during
curation plus 284 during independent verification. The 916 labels of the 229
unchanged lessons are reused from the already executed, source-bound original
Racket census.

Finally, a fresh source-bound load of `SEMANTIC_RIVALS` independently scored all
300 final lessons. Both `globally_unique_seeds` and `translate_copies` were
refuted by the demonstrations in all 300 production arrangements and in every
one of the 1,200 rotations. No ambiguous or `survived_all` verdict remained in
this finite union. The check covers exactly these two declared rivals and these
materialized lessons; it is not a proof of identifiability against unrestricted
alternative rules or an approval for production training.

## Source and evidence identities

| Bytes identified | SHA-256 |
| --- | --- |
| Frozen canonical generator | `f200365928e54477a847a8494a60c081a4428a6057d99491b1b26de34b94cda4` |
| Final optional curator | `8a1deb4b86b374378b3a975306c18333d05957020cc8ec6c50be75c91125b0de` |
| Independent batch harness | `c80c71a0d03c0c75f17b807b3a6f852b381201350e22d89a69ee425a1087b4be` |
| Raw canonical `program_solution`, UTF-8 | `bf88e8ff998e82775552a9164adcc733433cf5fc60a9df43afa1467a4106b49f` |
| Native stripped callable used by curator, UTF-8 | `381909599f8b4f2b7c55879c9ac9c22d04df3394cce59d5b45dc54daef7380c3` |
| Public apply's wrapped callable, UTF-8 | `4f9e1757d2fb7d1360948dfa342feebdee6f8626f40cef3d88dfaeb989ddfe26` |
| Decompressed grouped fresh Racket receipts | `ed6509031cf0ecb94f877006880d0d1ec8c0a9abc6affa462cf941b0637ace1b` |
| Decompressed final 300-lesson union | `19ad022e216ec97d3f15bfe84dd7378135ddbd15c3a23cd6ef44100a94afdb2a` |

The canonical `RULE_HASH` remains `f9fbf72b057d`. The different program hashes
identify different, explicitly named byte representations of that same rule.
The grouped curator reports additionally retain native bridge-definition bytes,
protected Racket runtime identity, request bounds, selected/rejected candidate
indices, original and final lesson hashes, and individual query-preservation
evidence. Source hashes were checked before and after each batch phase.

## Files and reproduction

`verification-summary.json` gives the final aggregate result.
`curation-records.json.gz` retains all 71 before/after lessons, source identities,
curator reports, and independently computed rival verdicts.
`racket-verification.json.gz` retains the five independent public apply receipts.
`strict-export-union.json.gz` retains the checked union of 71 curated and 229
unchanged lessons, including original census identities and all holdout verdicts.
Each gzip artifact has a companion `.compression.json` file with exact raw and
compressed sizes and SHA-256 values. Decompress a copy and verify those values
before use.

Run the three phases from the packet root with the prepared review environment:

```bash
python3 review.py run ../.venv-review/bin/python -B ../checks/lesson-curator/verify_batch.py curate
python3 review.py run ../.venv-review/bin/python -B ../checks/lesson-curator/verify_batch.py label
python3 review.py run ../.venv-review/bin/python -B ../checks/lesson-curator/verify_batch.py verify
```

All three commands returned **0**. Exact command rows and packaged evidence paths
are retained in `batch-commands.json`; the corresponding process logs are
`batch-curate.log`, `batch-label.log`, and `batch-verify.log`.
