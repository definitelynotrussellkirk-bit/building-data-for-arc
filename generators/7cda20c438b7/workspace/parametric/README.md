# X and cross centers — proposed parametric family

This runnable authoring prototype preserves the source task's local reasoning:
find black centers whose four required neighbors are green, then fill those
centers yellow while preserving every other cell. One episode-fixed parameter,
`neighborhood`, chooses `diagonal` (an X) or `orthogonal` (a cross). This is a
geometric rule change, not a palette or input-size change.

The default `diagonal.rkt` is byte-for-byte the selected canonical program
(SHA-256 `ac623b9aa2f6690b316c03fc0ea567faf026f53424726751163fa1eb4c27efbc`).
`orthogonal.rkt` changes only the four neighbor locations. Neither rule performs
iterative simulation; simultaneous local pattern completion is the actual
reasoning demand. The production generator, canonical authority, approvals and
open canonical audits are unchanged. These variants are **proposed and
unaccepted**, and are not admitted to training.

## Generate and check four-query examples

From the outer packet directory, after its documented environment setup:

```bash
source WORK/.venv/bin/activate
python3 review.py run python3 generators/7cda20c438b7/workspace/parametric/prototype.py \
  --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/parametric/examples
python3 WORK/check_public_exports.py WORK/checks/parametric/examples/public --demos 3 --queries 4
```

Omitting `--setting` emits both settings for each seed. To select one, pass
`--setting diagonal` or `--setting orthogonal`. The writer refuses an existing
output path, duplicate visible challenges, malformed grids, false labels and
query ambiguities under the declared finite rival family. Every saved label and
rival comparison is executed through Racket before the output directory is
created. `generate()` alone returns Python label claims for the native worker;
the native worker independently executes those claims.

Counts are independent: **2–6 demonstrations** and **1–4 queries**, defaulting
to **3 and 4**. Unsupported counts, unknown settings and non-integer numeric
arguments are rejected. Query sizes, in order, are **7×7, 16×20, 23×29 and
30×30**. Demonstrations use 13×17/17×13 canvases. `sample_input` supports any
height and width in 7..30. The smaller prototype limit is an authoring grammar
choice that leaves room for controlled patterns; the Racket programs themselves
also handle smaller legal ARC grids, as the retained 3×5 witness shows.

## Teaching and sampling

Input randomness uses `(seed, split, index)` only. Hidden settings and requested
query count do not enter that stream. Matched settings therefore receive exactly
the same inputs, and a one-query request has the same demonstrations and first
query as a four-query request.

The first two demonstrations construct shared-arm Xs, shared-arm crosses,
three-arm distractors, occupied centers, wrong-color arms, intersections and
isolated patterns. Patches are shuffled and rotated/reflected; settings are
identified through labels rather than layout. Additional demonstrations add
layout diversity. Large queries place many motifs throughout the canvas, with
boundary contacts and distractors. They are not small scenes with empty padding.
Some small queries lawfully require no change; the demonstrations still teach
which geometry, color and center predicate applies.

`fit_demonstrations(train, settings, reference)` has no query argument. It
executes both setting programs and six explicit shortcuts: identity, either
neighborhood, only three required arms, overwriting occupied centers, accepting
any nonzero arm colors, and filling isolated patterns only. Runtime errors abort
verification; they never count as evidence against a rival. After fitting, each
query is checked against the surviving interpretations. This is a finite-rival
certificate, not uniqueness against every possible program.

The separated-patch grammar guarantees useful contrasts with bounded sampling
work. It does not cover arbitrary crowded scenes or claim measured model
generalization. The old canonical sampler's overlap and override findings remain
open: richer prototype evidence does not repair unchanged production code.

## Controller projection: reveal one query at a time

`public/*.json` is a **controller-side bundle** of visible demonstrations and
four query inputs. Do not send the whole bundle as the first model turn. Keep
`private.jsonl`, which includes settings, programs, answers and certificates,
controller-side as well.

Use the existing projection helper for the first model-visible turn:

```python
from reviewer_support import public_challenge_bytes

turn_zero = public_challenge_bytes({
    "train": episode["train"],
    "test": [{"input": episode["test"][0]["input"]}],
})
```

Those bytes equal the projection of the corresponding one-query episode. The
consumer reveals the next input only after the preceding answer. Do not add
total-count hints, future inputs, private metadata, a bundle ID, or a final-turn
cue to this projection. This prototype supplies data and projection checks; it
does not implement another controller or training loop.

Public filenames are SHA-256 hashes of the exact canonical visible bytes written.
Settings, seeds, programs and query answers cannot affect those names. Files and
private records are sorted by public ID; duplicate visible payloads fail before
publication.

## Reusable checks and native handoff

```bash
python3 review.py run python3 -m pytest -q generators/7cda20c438b7/tests/test_parameters.py
python3 review.py run python3 generators/7cda20c438b7/workspace/parametric/probe.py \
  --out ../checks/parametric/fresh-study.json
```

The bounded probe exercises both settings at seeds 0 and 17 for every supported
demo count, always with four queries. It records successes and failures, exact
source/program bindings, query geometry and shared-arm counts, the retained
overlap counterexample, first-turn equality, and four jobs through the real
protected-Racket native adapter consumer. It does not qualify or accept variants.

`adapter.py` loads the adjacent implementation by exact path, so a different
cached module named `prototype` cannot substitute its implementation.
`promotion.json` supplies the native finite settings/count contract. The native
manifest builder inventories the source and compact task-local execution record:

```bash
python3 review.py run python3 -m arcpuzzles parametric manifest 7cda20c438b7 \
  --evidence generators/7cda20c438b7/workspace/parametric/evidence/current \
  --include generators/7cda20c438b7/tests/test_parameters.py \
  --reported-checks 'Use the actual fresh checks and their limits.'
```

An existing manifest requires its exact `--replace SHA256` guard. Inventory
freshness is not execution or acceptance. The next owner action is to resolve
the unchanged canonical approval/audit prerequisites, then use the repository's
separate qualification and acceptance workflow if this proposed grammar and
rule change are wanted.
