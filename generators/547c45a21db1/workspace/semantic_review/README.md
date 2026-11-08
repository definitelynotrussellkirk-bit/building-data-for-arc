# Independent semantic review: 547c45a21db1

This authoring probe reads only the selected canonical task and task-local source.
It does not read either Python solve episode. Its candidate rivals are diagnostic
hypotheses; the public `arcpuzzles apply` receipt is the retained Racket authority.
The baseline observations below use generator SHA-256
`a9ad5c0c5a3c1b4eb1dc2db8fdc120f16342fcdc3cb261bbce1aedc4bb4a8efb`.

## Canonical support and actual rule

The rule uses four-neighbor shortest-path distance through colors 1, 2, and 3,
recoloring only color 1 by the nearer seed and using 4 for a tie. It preserves
seeds 2 and 3 and emits 0 elsewhere. On the stated simple induced path domain,
following the path and splitting its ordered cells into equal halves is
equivalent; that implementation is not a false rival.

| Canonical pair | Grid | Total path cells | Color-1 cells | Tie cells |
| --- | --- | ---: | ---: | ---: |
| Train 0 | 5 by 7 | 7 | 5 | 1 |
| Train 1 | 7 by 7 | 12 | 10 | 0 |
| Test 0 | 8 by 9 | 19 | 17 | 1 |

The baseline `path_len` axis ends at 14 and means total occupied cells in actual
construction despite its color-1 wording. Thus it cannot generate the canonical
query's total path length of 19. All canonical seeds 2 are earlier than seed 3
in row-major order; color assignment therefore requires an orientation witness.

## Candidate rivals, measured on all canonical pairs

`checks/semantic-review/analysis.json` retains every input, prediction, and exact
mismatch coordinate. Each count below has denominator three canonical pairs.

| Rival | Fitting canonical pairs | Observation |
| --- | ---: | --- |
| Eight-neighbor unit-step BFS | 3/3 | Diagonal shortcuts happen not to move the canonical boundary. |
| Eight-neighbor distance with diagonal cost square root of 2 | 3/3 | Discounting corners still leaves these particular outputs unchanged. |
| Assign 2 to the half nearer the row-major first endpoint | 3/3 | All canonical seed orientations agree with this rule. |
| Add 0.5 per intervening path turn | 3/3 | Canonical ties balance turns; other cells have enough distance margin. |
| Subtract 0.5 per intervening path turn | 3/3 | Same canonical limitation. |
| Direct Manhattan distance | 2/3 | Fits both training pairs, differs on seven canonical query cells. |
| Direct squared Euclidean distance | 2/3 | Fits both training pairs, differs on seven canonical query cells. |
| Direct Chebyshev distance | 1/3 | Differs on train 1 and test 0. |
| Add 1 per intervening path turn | 2/3 | Introduces an incorrect tie in train 1. |

An L path is coordinate-monotone, so Manhattan distance equals path distance
everywhere on it. The baseline comment claiming L shapes refute Manhattan is
incorrect. Bent paths need genuine backtracking to teach that distinction.

## Exact separating witness

Use a 5 by 7 background grid and this ordered support:
`[(2,1),(3,1),(3,2),(3,3),(2,3),(1,3),(0,3)]`.
Place color 2 at the first point, color 3 at the last, and color 1 between them.
Racket produces colors `[2,2,2,4,3,3,3]` along that support. This one input refutes
all nine candidate rivals above. Its input SHA-256 in the public apply receipt is
`4ebfc634c3679d7bf151a473cafc6078b22adfc918900872b7e302dc78433d02`.
The complete input, Racket output, and all differing predictions are retained.

The supported command `arcpuzzles apply` evaluated four crafted witnesses;
`authority_verification.json` confirms the independent Python BFS diagnostic
matches all four Racket outputs and all three canonical outputs. This is not a
new rule authority. The canonical program SHA-256 is
`44ec512ed7bb40370dd13ed35408a4c0ece07c3de292f157b51d6a4450ade2ea`, and its rule
identifier is `44ec512ed7bb`. The apply receipt's separately named
`rule_text_sha256` hashes executable callable text and is
`68b35003cc1eda3ab51e7f204be370b800090a78e4f78edf929090032ae22355`.

## Witness coverage and curriculum implications

`spaced_snakes.py` enumerates contiguous subpaths of the complete spaced
serpentine layouts on the smallest 5 by 6 grid, with reflections, translations
where available, and both endpoint label orders. The selected odd lengths
7, 9, 11, and 13 have 24, 40, 24, and 4 distinct inputs respectively refuting all
nine candidates, out of 144, 120, 96, and 72 unique inputs in those restricted
families. These are finite family counts, not frequencies of the production
sampler. No even-length subpath in that family refutes all five canonical-fitting
rivals, although general induced paths can do so.

`even_length/enumerate_paths.py` separately enumerates every induced path support
on the 5 by 6 board, counting it once modulo endpoint reversal but retaining
translation and board symmetry. The accompanying census is exhaustive through
20 cells and gives both witness counts and example grids. All five canonical-
fitting rivals can be refuted simultaneously at each length from 7 through 20.
All nine candidates can be refuted at each of those lengths except 8. This is a
domain census independent of the selected generator's sampling distribution.

For four demonstrations plus one query, placing two all-rival witnesses among
the five labelled pairs guarantees that every query rotation retains a witness
against these rivals. Alternating contrast and free draws provides two such
witnesses in every five consecutive requested indices. Rejected or duplicate
draws can change the accepted sequence, so production claims must inspect actual
accepted indices and full materialized lessons, not only requested residues.
Specific exact overrides may intentionally suppress the contrast schedule and
therefore need a separate stated teaching limitation.

## Domain limits

The smallest 5 by 6 grid contains a 20-cell induced spaced snake; any prefix
therefore proves geometric feasibility for each exact total path length 4 through
20 across every larger permitted canvas. This does not prove a particular random
generator always honors those controls; joint overrides require separate tests.
Branches, cycles, interior seeds, disconnected components, recolored backgrounds,
and arbitrary palettes are unnecessary domain expansions. In particular,
disconnected 1-cells make a distance lookup undefined, and extra colors do not
remain unchanged under the current Racket rule. No reference-rule change is
recommended by these probes.

## Retained commands and a diagnostic correction

The exact commands, working directories, statuses, and evidence paths are in
`checks/semantic-review/commands.json`; the exhaustive induced census has its own
command record. A first provenance verification incorrectly compared the raw
canonical program hash with the callable-wrapper hash and exited 1. Its source
and explanation remain in `verification_failed.json` and
`verify_authority_failed_source.py`. The corrected verification checks the proper
rule identifier and all four outputs, exits 0, and keeps both hash identities.
This bookkeeping failure did not find any label disagreement.
