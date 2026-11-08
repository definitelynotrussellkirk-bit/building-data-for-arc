# Bounded raw-sampler lesson census

The repaired generator's raw sampler still creates lessons that do not identify
the rule against its declared finite rivals. The completed public census returned
exit **1** with status **ambiguous**, preserving that finding. All 300 requested
lessons materialized successfully; the exit is not a runtime or labeling error.

## Scope and results

The public `arcpuzzles lesson-census` command sampled 100 lessons in each of easy,
medium, and hard, with three demonstrations and one query. It labeled all 1,200
pairs using the selected canonical Racket rule, then held out each of the four
pairs in turn while preserving the order of the other three. The resulting
1,200 query rotations reuse those recorded Racket outputs. All 1,200 sampled
inputs have distinct hashes.

| Band | Lessons | Ambiguous original lessons | Single-query rotations | Ambiguous rotations |
| --- | ---: | ---: | ---: | ---: |
| easy | 100 | 11 | 400 | 43 |
| medium | 100 | 0 | 400 | 1 |
| hard | 100 | 0 | 400 | 0 |
| Total | 300 | 11 | 1,200 | 44 |

There were zero materialization errors, scoring errors, hook warnings, or
rotation scoring errors. Exactly 44 distinct materialized four-pair bundles have
an ambiguous rotation. The 11 original production ambiguities are included in
those 44, not additional cases.

Every ambiguity is explained by the already declared
`SEMANTIC_RIVALS:globally_unique_seeds`: it fits all three demonstrations but
disagrees with the held-out canonical answer. This rival requires a seed color
to occur only once across the whole grid, whereas the canonical rule assigns
color roles separately inside each connected group. The other declared rival,
`SEMANTIC_RIVALS:translate_copies`, was refuted in every original lesson and every
rotation. The global-singleton rival was refuted in 262 original lessons,
survived all labels in 27, and was ambiguous in 11; the corresponding rotation
counts were 1,048, 108, and 44.

These are finite measured results. The input-level semantic witnesses establish
that accepted counterexamples exist, not that every randomly sampled lesson
contains them. Passing this finite rival set is also not a proof of unique
identifiability against every possible rule. A separate optional curator may
replace demonstrations under an explicit stricter export policy; it must not
erase this raw-sampler finding or imply production approval.

## Exact witnesses

Each `.lesson.json` is a plain labeled lesson with top-level `train` (three
input/output pairs) and `test` (one input/output pair). Its adjacent
`.evidence.json` retains original pair order, sampling identity, all four
canonical outputs, fresh predictions from both declared Python rivals, differing
cell coordinates, and source identities. Canonical labels are reused from the
actual Racket census; the extraction separately verifies current rival behavior.

| File stem | Band / index / seed | Held-out original pair | Canonical/rival differences | Original production lesson |
| --- | --- | ---: | ---: | --- |
| `production-ambiguity` | easy / 25 / 1776932124 | 3 | 38 cells | ambiguous |
| `rotation-ambiguity` | easy / 92 / 632428106 | 0 | 38 cells | not ambiguous |
| `medium-rotation-ambiguity` | medium / 85 / 2201692212 | 1 | 18 cells | not ambiguous |

Pair 3 is the original production query. The first row is the strongest measured
original production ambiguity by differing cells. The second is a strongest
alternate-query ambiguity. The third preserves the only medium-band failure.
`ambiguous-cases.json` retains all 44 original source-bound bundles and their
ambiguous query indices for bounded follow-up curation.

The stricter optional export policy requires actual refutation of both named
rivals in every holdout. Another 27 bundles are answer-equivalent: the global
singleton rival agrees with all four labels, so no query ambiguity is observed,
but no demonstration refutes that rival either. These are retained separately in
`answer-equivalent-cases.json`. The representative `answer-equivalent.lesson.json`
is easy index 0, seed 1923198031; its adjacent evidence freshly verifies the
rival's agreement on all four pairs. `strict-policy-cases.json` therefore lists
71 candidates for optional curation, retaining the distinction between the 44
actual ambiguities and these 27 answer-equivalent cases. The other 229 bundles
already refute both declared rivals in all four holdouts. Any follow-up result
must be separately measured and must preserve this original census unchanged.

## Source and report identities

| Bytes identified | SHA-256 |
| --- | --- |
| Selected `generator.py` | `f200365928e54477a847a8494a60c081a4428a6057d99491b1b26de34b94cda4` |
| Raw canonical row `program_solution`, UTF-8 | `bf88e8ff998e82775552a9164adcc733433cf5fc60a9df43afa1467a4106b49f` |
| Public runner's executed wrapped callable, UTF-8 | `4f9e1757d2fb7d1360948dfa342feebdee6f8626f40cef3d88dfaeb989ddfe26` |
| Full decompressed census, 30,554,735 bytes | `857229364e0e0c23c3c9cbe0f7137f9d5133847f60669fb45bfa85931a7ba3b9` |
| Compressed census, 660,574 bytes | `87edf1b8c64cb823efc5b365cbc0a9950a96c21a8e1459b98b84fff1c596c74d` |

The declared `RULE_HASH` remains `f9fbf72b057d`. Raw rule text and wrapped
executable text are deliberately named separately. The full report additionally
retains controller and staged-runtime manifest identities. Its compression
manifest provides the exact restoration recipe, sizes, and both byte hashes;
the extraction independently checked those values.

## Reproduction

Run from the packet root, using the prepared review virtual environment:

```bash
python3 review.py run ../.venv-review/bin/python -m arcpuzzles lesson-census dc2c4869445c --per-band 100 --train 3 --test 1 --rotate-query --rotation-policy require --timeout 1800 --gzip --out ../checks/lesson-census/census.json
python3 review.py run ../.venv-review/bin/python -B ../checks/lesson-census/extract_witnesses.py
```

The first command returned 1; the second returned 0. Exact command rows and
evidence paths are retained in `commands.json`. The census used its documented
default deterministic seed recipe: the first eight hex digits of
SHA-256(`lesson-census:v1:TASK:BAND:INDEX`), with consecutive requested starts
0 through 99. Accepted indices may advance during materialization and are
recorded in each instance. The report's modulus 6 is a reporting convention;
this run did not enumerate a declared schedule period.
