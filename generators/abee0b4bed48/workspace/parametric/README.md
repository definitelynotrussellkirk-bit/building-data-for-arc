# Decode tiles, then order their classes by frequency

This separate proposal preserves the production generator and the selected
canonical program. `{"order":"input"}` returns `canonical.rkt` byte for byte.
`{"order":"frequency"}` executes `frequency.rkt`.

## Exact rule

Divide the three-row strip into aligned, adjacent 3x3 zones. Decode each zone
from its gray (5) cells:

| Gray pattern | Decoded label |
|---|---:|
| Exactly one gray cell, anywhere | 4 |
| Exactly eight gray cells, any missing position | 3 |
| Exactly three gray cells filling the top row | 6 |
| Exactly three gray cells filling the bottom row | 1 |
| Any other exactly-three-gray shape | 9 |
| Every other gray count | 0 |

The default fills each zone with its label in input order. The alternative
first computes the complete decoded label vector, counts each label's frequency,
and orders zones by descending frequency. Equal-frequency classes use ascending
numeric label order, including label 0. It fills the resulting zones with their
decoded labels. Original order breaks ties between identical labels; that tie
is unobservable after painting identical output zones.

This adds a global operation while retaining every local classification branch.
Raw gray counts cannot substitute for decoded labels: three-gray top, bottom and
other tiles belong to different classes. The protected causal counterfactual
keeps the correct painted labels but ranks using raw gray-count frequencies.

## Supported domain and API

Inputs are exactly three rows, width 3–30 divisible by 3, with exact integer 0/5
cells in exact Python lists. All 512 binary 3×3 patterns are lawful. This extends
the unchanged production sampler's restricted counts and linked profiles.
It deliberately remains a strip: 30×30 is outside the grammar. The canonical
source reads only the top three rows; adding other rows would create ignored
context rather than meaningful two-dimensional classification. The maximum
generated case is 3×30, with ten populated zones and 51 gray cells.

`generate(seed, settings, demos=3, queries=4)` accepts exact integer seeds in
`0..2**63-1`, 3–6 demonstrations and 1–4 queries. Inputs and their ordering match
across settings. The complete four-query bank is shuffled before prefix
selection, and demo/query counts are independent. Every episode input differs;
every returned row/grid is independently owned.

Three constructive demonstrations teach an isolated action, repeated classes
with unequal frequencies, and a multi-zone all-distinct case. Marker and hole
positions cover center, edge and corner roles. Other triples include middle
rows, diagonals, L shapes and columns; fallback examples include blank and
nonempty tiles. A tie is deliberately presented in an order opposed to the
numeric tie rule. Optional demonstrations retain the ordinary prefix.

Sorting can hide a wrong decoder when two classes have the same counts in every
demonstration. The repaired three-demo design gives all six classes distinct
count vectors across the demonstrations. The singleton identifies label 3; the
large example uses counts 1, 2 and 3 and contains two instances of one outer-row
class; the all-distinct example contains the opposite outer-row class and omits
the repeated one. Both multi-zone scenes share their vertical reflection.
This distinguishes every fixed permutation of the six decoder labels, including
the formerly hidden top/bottom and fallback/other swaps. It is a specific
identifiability property, not uniqueness against arbitrary programs. Every
reviewed query and optional demonstration is unchanged by the repair.
The three label-9 tiles in the repeated-class demonstration form one contiguous
run. This distinguishes counting individual zones from counting runs, while
leaving the class-count signatures unchanged.

`decode` and `first_stage` return the decoded vector. `analyze` also returns
per-zone frequencies, the stable permutation, ordered labels and output.
These Python outputs are claims; native qualification independently executes
Racket. Finite rival checks cannot establish unrestricted uniqueness.

## Native reproduction

Run from the outer packet with its Python 3.12 environment and Racket setup:

```sh
WORK/.venv/bin/python review.py task-tests abee0b4bed48 --phase after --out ../checks/abee0b4bed48/task-tests
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify abee0b4bed48 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/abee0b4bed48/qualification --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/abee0b4bed48/qualification/qualification.json --out ../checks/abee0b4bed48/preview
```

Use fresh output destinations for reruns. The public preview exposes one query
per file; the bundle, listing, settings, programs, answers, future inputs and
presentation permutation remain controller-private. Qualification is separate
from owner exact-source acceptance and training admission.
