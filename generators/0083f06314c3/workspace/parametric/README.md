# Selector-directed template orientations

This separate native prototype offers one episode-fixed parameter:

| Setting | Matching rule |
| --- | --- |
| `orientation=fixed` | Use the selected cropped template in its original orientation. The returned program is byte-identical to the current canonical authority. |
| `orientation=rotations` | Search all four quarter-turn orientations of the selected template. Reflections remain excluded. |

Both rules read the selector panel first: color 2 selects template A; another
nonzero non-divider color selects B. Template zeros are wildcards, nonzero cells
must match exactly in color, and the answer marks the union of every matched
nonzero template cell in color 8. The board-sized answer has zero background.
Overlapping matches remain valid. This selection-to-matching dependency is
input-dependent: the chosen shape, colors and wildcard positions constrain B.
The protected audit substitutes A for a B-selected intermediate and checks that
the final output changes.

## Sampling and teaching scope

`generate(seed, settings, demos=3, queries=4)` supports independent counts of
2–6 demonstrations and 1–4 queries. Seed is a literal integer in 0..2**63-1.
Unknown settings, booleans, non-integer controls and out-of-range values fail.
Input randomness does not depend on the setting or requested counts. The same
seed gives matched inputs across settings and stable train/query prefixes.

The first two demonstrations select A and B respectively. Each contains an
overlapping true pair, a rotated occurrence, a reflection-only decoy, a copy in
the wrong color, an unselected-template occurrence and another true occurrence.
Chiral L/P shapes, their orientations, colors, translations and placements vary.
The second demonstration uses a 30×30 input with the maximum supported number
of positive groups, while the first uses only two (fixed) or three (rotations).
This repairs an observed cap-at-demonstrated-count shortcut that fitted the
initial small lessons and failed larger queries. The first demonstration also
contains a dense unselected-color distractor, so the selected template's color
is the minority there and the majority in demonstration two. Selection cannot
be replaced by choosing the more prevalent template color.
Additional scenes increase variation and board content. A constructive overlap
filter keeps witnesses that distinguish union from both greedy-disjoint and XOR
aggregation under both parameter values. This filter does not inspect queries.

An episode uses selector 2 and one B code from `{1,3,4,5,6,7,8}`, chosen by seed
modulo seven. Every query code is shown in the first two demonstrations. Across
episodes all B codes occur; seed 0 includes the historically missed code 1.
This is an explicit sampling restriction, not an additional private rule
parameter. The evaluator still implements the canonical selector law for all
nonzero non-divider selector colors. No claim is made that two demonstrations
uniquely establish arbitrary behavior on unseen selector codes.

The sampler uses monochrome templates in two width-3 panels, one selector
column, and three full-height color-9 dividers. No interior 9 is admitted.
Template and selector positions vary. Queries use these input sizes:

| Query | Input | Search board / output |
| --- | --- | --- |
| 1 | 12×28 | 12×18 |
| 2 | 19–27×29 | 19–27×19 |
| 3 | 16×30 | 16×20 |
| 4 | 30×30 | 30×20 |

The minimum and maximum query sizes carry real matches and decoys. Larger boards
contain additional groups across the canvas; the maximum reaches all four board
edges. Template and separator overhead precludes a 30×30 output inside a 30×30
input. This larger geometry is separate from the unchanged production sampler's
6–8-row domain. `rule_mirror` also preserves cell colors when rotating multicolor
templates, although the sampler itself uses monochrome ones.

`teaching_check` reads demonstration labels only and rejects thirteen named,
parameter-aware rivals: the other orientation setting; always A; always B;
literal zeros; color-blind matching; rotations plus reflections; first match;
greedy disjoint matches; XOR matches; all board foreground; bounding-box fill;
a small cap on positive output groups; and the most frequent template color.
`rival_programs` supplies executable Racket counterparts. This is a finite
shortcut audit, not a universal uniqueness guarantee or a training-gain claim.

## Native integration and reusable audit

`adapter.py` imports only its exact adjacent implementation. `promotion.json`
declares the two settings, canonical default, resources and count limits.
`canonical.rkt` retains exact authority bytes; the alternate changes only the
unique final matching mode. Shared runtime and production source are unchanged.

From this packet's outer directory, use the selected Python environment and the
existing `review.py run` wrapper (payload paths below are relative to `WORK/repo`):

```bash
WORK/.venv/bin/python review.py run python3 -m pytest generators/0083f06314c3/tests/test_parametric.py -q
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify 0083f06314c3 --out ../checks/0083f06314c3/qualification --summary
WORK/.venv/bin/python review.py run python3 generators/0083f06314c3/workspace/parametric/audit.py --qualification ../checks/0083f06314c3/qualification/qualification.json --out ../checks/0083f06314c3/audit --export ../checks/0083f06314c3/examples
```

Create a fresh native source inventory before qualification, and use new output
directories when repeating checks. The audit refuses stale source closures and
changed native execution receipts. It reuses qualified labels, executes boundary
requests and finite teaching rivals through the same checkout's protected Racket
bridge, validates its causal witness with the native validator, and checks the
public/private export using the existing packet helper. Its report records the
evaluation budget and actual count. It does not grant owner acceptance.

## Public projection

`public_challenge(episode, query_index)` returns all visible demonstrations and
exactly one query input. It includes no query answer, private setting, program,
seed, future input, query index or total-count hint. Query 0 is byte-identical to
single-query use. The existing consumer can call it again for successive turns;
no new controller or training loop is added.

`export_batch` writes `public/<visible-sha256>.json` and a separate
`private/<visible-sha256>.json` full bank. It hashes only the established public
projection bytes. It validates the entire batch, rejects duplicate visible
lessons (including contradictory hidden banks), and serializes exact private
bytes before creating the destination. Existing destinations are refused. Only
the public directory is model-visible; the private bank carries answers,
programs, settings and the remaining queries. The audit's small retained export
comes from hash-verified native Racket execution records. Training admission and
exact-source owner acceptance remain pending after this reviewer handoff.
