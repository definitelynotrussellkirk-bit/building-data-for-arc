# Proposed front/back crossing-band rule

`layer_selection.py` is a runnable **parametric prototype** for the original
training family `1a2e2828`, selected task `7b0cb3b9a618`. It adds one episode-fixed
parameter, `target_layer`, with the two literal values `front` and `back`.
The default is `front`. This is separate from the selected production generator,
its canonical authority, approval state, and training admission.

## Meaning and domain

Every nonzero color identifies a contiguous full horizontal or vertical band on
background color 0. The visible color at a crossing tells which of its two bands
was painted later. `front` selects the unique band above all other bands in that
partial order; `back` selects the unique band below them. Both produce a 1x1
color grid. Recovering bands and their occlusion relationships is shared by both
settings. The setting changes which endpoint of that relation is the answer.

`front.rkt` is byte-for-byte the selected canonical `program_solution` (including
its original formatting). Its vertical branch requires a width-1 front band
outside column 0 and a horizontal row with exactly one anomaly. `back.rkt`
independently examines the visible crossings and selects the unique color that
never wins a crossing. Both are executed through the protected `RacketBridge`.
The Python `visible_endpoints` observer checks geometry, crossing legality,
acyclicity, and uniqueness of both endpoints; it does not provide exported labels.
The small Racket rules assume that validated domain and are not general-purpose
validators for arbitrary grids.

All six original canonical pairs have unique endpoints. Their original front
answers are `[1,8,6,3,6,7]`; the independently inferred and Racket-checked back
answers are `[2,3,1,1,3,1]`. Incomparable middle layers are allowed. A complete
unique paint order is unnecessary.

The prototype sampler uses the six canonical shape/palette profiles and a
12-slot schedule alternating front orientation. It paints bands in alternating
horizontal/vertical order to guarantee a visible chain connecting the endpoints.
Colors, spans, positions and band thickness vary. This is a deliberately bounded
subset of crossing-band scenes, not a claim to exhaust their full morphology.
The sampler is independent of `target_layer`; the same sampled input can be
labeled under either rule. It retains the canonical vertical-front restrictions.

## Reproduce the four-query examples

From the outer review-packet directory, with the packet's normal dependencies:

```sh
python3 review.py setup
python3 review.py run python3 generators/7b0cb3b9a618/workspace/parametric/layer_selection.py --seed 190807 --target-layer both --demo-count 3 --query-count 4 --out ../checks/parametric/new-examples
```

Choose a fresh output directory; existing directories are never overwritten.
The command produces two complete episodes, one per setting, with three labeled
demonstrations and four distinct queries each. `--target-layer front` and
`--target-layer back` select one setting. The Python API defaults to `front`;
the CLI defaults to `both` to demonstrate the proposed extension.

Demonstration and query counts are separate: `demo_count` accepts 2..12 and
`query_count` accepts 1..32. Counts must be literal integers. Every query differs
from every other query and from every demonstration. Authoring tries at most
64 deterministic candidate lessons and raises an explicit error on exhaustion;
it never clones examples or silently reduces a requested count.

Before labeling queries, the authoring loop evaluates both lawful settings on
the demonstrations and requires just the selected setting to survive. It also
requires those demonstrations to reject eight concrete shortcuts:
`uniform_row_only`, `uniform_column_only`, most/least frequent foreground color,
smallest/largest foreground color, and first/last foreground pixel. This finite
rival set does not establish unique induction against all possible hypotheses.
Every query receives an explicit demonstration-only identifiability receipt.
No query label is used to eliminate a hypothesis.

## Export and reuse

The output tree is:

- `public/<id>.json`: only demonstration inputs/outputs and query inputs.
- `private/<id>.json`: setting, seed, all labels, exact rule, runtime/source hashes,
  and the per-query identifiability receipt.
- `private/programs/<program-sha256>.rkt`: exact executed rule bytes.
- `private/manifest.json`: sorted public IDs and their private program bindings.

`write_batch` calls `reviewer_support.public_challenge_bytes` and
`public_challenge_id`; each public ID is the SHA-256 of exactly the bytes written.
Hidden settings, seed, program, query outputs and private metadata do not enter
that identity. It sorts outputs by public ID and rejects repeated visible
payloads before writing anything. It serializes supplied private records without
certifying manual edits to their labels; use `build_episode` for Racket-authored
records. There is no public file containing the private setting map.

The reusable entry points are `sample_input`, `visible_endpoints`, `program_for`,
`RacketLabeler`, `build_episode`, and `write_batch`. All authored source and
materialized programs live in this task workspace, with no predecessor imports.

## Focused verification

```sh
python3 review.py run python3 -m pytest -p no:cacheprovider -q generators/7b0cb3b9a618/tests/test_parametric_layers.py
```

The tests execute both Racket settings, all six canonical examples, hand-painted
crossing witnesses (including incomparable middle layers), all 12 input slots,
four-query episodes, independent counts (including retry-schedule aliasing at
2 demos/10 or 22 queries and the 12-demo/32-query boundary), malformed/cyclic/ambiguous
inputs, exact public bytes, hidden-metadata identity invariance, duplicate rejection, and
refusal to overwrite an existing batch. Retained command receipts and complete
example episodes are under `checks/parametric*` in this return.

No canonical production battery was required or rerun: the production generator
and authorities are unchanged. This prototype supplies authoring evidence only;
it does not approve a new rule variant or admit any generated trajectory.
