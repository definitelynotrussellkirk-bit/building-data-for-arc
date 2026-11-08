# Native stamping policies — reviewer ready, owner acceptance pending

`adapter.py` promotes and reuses the exact-path `stamp_orientation.py` prototype.
The production generator and the selected canonical Racket rule are unchanged.
The legacy module and its tests remain independently usable.

## One episode-fixed parameter

`policy=identity` returns the exact canonical bytes. `horizontal_mirror` reuses
exactly the existing mirrored-template program. `visible_majority` first performs
canonical row-major, clipped, overwriting stamps, then retains only the color
with the largest **visible painted-cell count**, breaking ties by smallest color.
This is not marker-frequency selection: clipping and overwriting alter the
intermediate histogram. The retained wrong-intermediate program counts original
singleton markers before painting and changes the final output.

A: extract the connected template and paint every marker, with canonical overlap
and edge semantics. Intermediate: the completed painted grid and its per-color
visible counts. B: select the dominant visible color and mask all others.
The winner cannot be selected from raw marker counts independently of A.

## Requests and teaching

`generate(seed, settings, demos, queries)` supports exact integer seeds in
0..2**63-1, 2–6 demos, and 1–4 queries; normal qualification uses three demos and
four queries. Settings must contain only `policy`; booleans, coercive counts,
unknown values and extra keys fail closed. Labels are Python claims, independently
re-executed by the native protected-Racket worker; generation never nests an audit.

Inputs are identical across settings, with independent per-split/per-index RNG
streams and stable demonstration/query prefixes. Two constructive demos expose
orientation, occupied-vs-box origin, clipped stamps, overlap precedence, and the
difference between raw-marker and visible-area selection. The repaired first
shape has empty top-row ends and an asymmetric lower tail. The second demo has
three clipped markers versus one full visible winner and a surviving higher-color
decoy. This fixes both a column-order teaching hole and a numeric-maximum shortcut
without increasing the two-demo minimum. Finite rivals are executable in
`rival_predictions`; `teaching_failures` tests demos before consulting queries.

Queries have sizes 7x9, 16x20, 23x27 and 30x30. The final query has a connected
large comb and 66 spatially spread singleton markers touching all four corners;
its content and stamps, not blank padding, exercise the boundary. Other scenes
vary connected shapes, colors, positions, marker counts, overlaps and clipping.
Grammar: background 0; sides 7..30; exactly one multicell monochromatic
4-component plus singleton markers. No extra multicell distractor is generated.
The program handles ties with the explicit numeric rule. Finite coverage does
not establish universal uniqueness or learning benefit; two structured teaching
profiles remain a distributional limitation.

## Public/private boundary

`public_turn(episode, i)` returns only demonstrations and the single current query
input. Programs, settings, answers, future query inputs and total-query hints are
not exposed. `audit.py` writes public files using the repository's canonical
serializer, named by SHA-256 of their exact public bytes. All four queries stay
private/controller-side until individually projected. No turn controller or
training loop was added.

## Reproduce from the packet's outer directory

```sh
python3 review.py run python3 -m pytest -q generators/144c5d002191/tests
python3 review.py run python3 generators/144c5d002191/workspace/parametric/audit.py --seeds 32 --out ../checks/144c5d002191/audit-fresh
python3 WORK/check_public_exports.py WORK/checks/144c5d002191/audit-fresh/public --queries 1 --demos 3 --summary
python3 review.py run python3 -m arcpuzzles parametric qualify 144c5d002191 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/144c5d002191/qualification-fresh --summary
```

The existing `arcpuzzles parametric manifest` and `arcpuzzles.review_witness`
commands maintain exact-source inventory and causal binding. Use fresh output
paths after edits; rebuild the manifest and qualification rather than relabeling
old evidence. `checks/144c5d002191/causal-final/witness.json` is the source-bound handoff.
Owner qualification/acceptance is separate; training admission remains false.
