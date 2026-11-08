# Framed-cell propagation: proposed parametric prototype

This task-local prototype is separate from the selected canonical generator and
its approval. It supplies no production parametric API and changes no canonical
rule, shared runtime, catalog, or assignment. The original/default setting is
`direction="both", min_anchors=2`; its emitted Racket text is the exact canonical
program obtained through `Catalog.get`, and every retained canonical pair is
checked by execution.

## Rule and parameters

All settings retain zero-separated 4×4 framed cells, a common interior color,
color identity, independent local interior offsets, and filling only the span
between matching anchors. Anchors are counted in the **original input**; newly
painted locations never trigger another pass.

| Parameter | Values | Effect |
|---|---|---|
| `direction` | `both`, `horizontal`, `vertical` | Enable row spans, column spans, or both. |
| `min_anchors` | integer `2`, `3` | Require at least this many original matching anchors on a line. |

The six rules are materialized by checked edits to the two anchor-count tests
in the canonical program. Direction disables the relevant painting branch.
Unexpected reference structure raises an error. The default returns unedited
reference text. Output labels and rival comparisons execute with the included
`RacketBridge` using the shared `strip_rule_wrapper` helper on this family's
self-contained lambda (no shorthand conversion is needed). A Python mirror is checked
against these executions; it is not the label authority.

Every sampled scene has four distinct local-offset channels: a horizontal line
with two anchors and a gap; a horizontal line with three anchors and a gap; and
the corresponding two vertical channels. Color/offset grouping remains
independent. Thus active directions and the threshold have observable effects,
including under threshold three. Every demonstration individually separates all
six settings, so the full demonstration set identifies the rule without query
answers. The actual check exhausts all six Racket settings using only the public
demonstrations; queries and private metadata are not arguments to that check.

Inputs vary palette, 4–5 cell rows/columns, channel-offset permutation, line,
span endpoints, and third-anchor location. Four rows/columns are necessary for
three anchors plus a genuine gap. Unique modal common interiors and uniform
frames remain intact. Collision-free offset channels prevent ambiguous paint
ownership; this sampler is a nearby bounded subfamily rather than a claim to
cover all canonical presentations. Queries must be pairwise distinct and absent
from demonstrations; bounded duplicate rejection raises instead of returning
fewer examples.

## Exact commands

Run from the outer extraction directory containing `review.py` (payload paths
resolve from `WORK/repo`):

```bash
python3 review.py run python3 generators/b3d7f3a15b3d/workspace/parametric/prototype.py --all-settings --seed 7321 --n-train 3 --n-test 4 --out ../checks/parametric
python3 review.py run python3 -m pytest -q generators/b3d7f3a15b3d/tests/test_parametric.py
```

The tests also support a dependency-free direct runner:

```bash
python3 review.py run python3 generators/b3d7f3a15b3d/tests/test_parametric.py
```

Single episode with explicit settings:

```bash
python3 review.py run python3 generators/b3d7f3a15b3d/workspace/parametric/prototype.py --seed 90 --direction vertical --min-anchors 3 --n-train 3 --n-test 4 --out ../checks/parametric-single
```

Without explicit settings, a deterministic seeded draw selects one of the six
rules once per episode, before input draws. Explicit parameters override only
their corresponding sampled fields. Changing demo/query counts does not change
the episode's selected rule. `n_train` and `n_test` are independent arguments;
this prototype requires integer `3..128` demonstrations and `1..128` queries,
and rejects booleans, unknown settings, noninteger seeds, invalid counts, and
conflicting CLI modes. These bounds limit cost and prevent silent truncation.

## Evidence and visibility

`WORK/checks/parametric-public-id-final/report.json` records the command, base seed,
each setting, exact source/reference hashes, canonical parity counts, distinct
input hashes, demo-only survivors, and hashes of every retained file. The writer
uses `reviewer_support.public_challenge_bytes` and `public_challenge_id`, validates
the complete batch before creating the output tree, rejects duplicate visible
payloads, and sorts all outputs by the 64-hex public ID.

Each episode is split across two trees:

- `public/<PUBLIC_ID>.json`: the exact canonical visible bytes—only labeled
  demonstrations and unlabeled query inputs. `PUBLIC_ID` is the SHA-256 of those
  exact bytes, so changing a seed, parameter, rule, or query answer cannot rename
  a public challenge.
- `private/<PUBLIC_ID>/private.json`: seed, parameters, query outputs, counts,
  hashes, and demo-only survivor evidence. It records the public path but is not
  model-visible.
- `private/<PUBLIC_ID>/rule.rkt`: the exact Racket program executed for that
  episode.

Give solvers only the `public/` tree. `private/`, `report.json`,
`contrast-private.json`, and this authoring README are controller evidence. Public
names contain no setting-associated ordinal or private field. The report retains
the private mapping from public IDs to settings. `contrast-private.json` contains
one additional lawful input and all six executed outputs; their hashes must be
pairwise distinct.

The tests include hand-derived direction/threshold outputs, original-anchor/no-
cascade and independent-offset cases, canonical default parity, invalid
counts/settings, all six episodes, public/private separation, seed
reproducibility, separate demo/query counts, exact visible-byte hashing,
private-metadata independence, order-independent batch naming, duplicate
rejection before writes, and full private serialization preflight before any
output path is created.

These are bounded execution results and proposed variants. Identifiability is
only against the declared six-setting family; no unrestricted ARC uniqueness,
training admission, or production approval is asserted.
