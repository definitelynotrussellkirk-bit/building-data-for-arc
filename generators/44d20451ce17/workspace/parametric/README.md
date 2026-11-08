# Proposed `destination_edge` rule parameter

This directory is a **task-local prototype** for original ARC family `3618c87e`
(review task `44d20451ce17`). It does not modify the selected production
`generate(...)` path, canonical Racket authority, `RULE_HASH`, or approval state.

## Parameter

`destination_edge` is chosen once per episode from the deterministic episode seed
and remains fixed for all demonstrations and queries.

| Value | Transformation |
| --- | --- |
| `bottom` | Canonical/default: erase color-1 cells above the last row and put one `1` at the bottom of every column that contained a `1`. |
| `top` | Proposed alternative: erase color-1 cells below row 0 and put one `1` at the top of every column that contained a `1`. |

Both values preserve the same reasoning structure: identify affected columns,
erase source markers away from the destination, collapse same-column multiplicity
to one marker, and preserve non-`1` cells except at the destination. `bottom.rkt`
is byte-for-byte the canonical program; `top.rkt` changes only the destination-row
predicate. Inputs reuse the selected generator's two lawful profiles, so there is
no parameter-dependent resampling.

## Files

- `prototype.py` builds complete Racket-labelled episodes, checks the opposite
  parameter on every query using only the demonstrations, writes private
  evidence, and emits masked public tasks.
- `rules/bottom.rkt` is the exact canonical/default program.
- `rules/top.rkt` is the proposed top-edge variant.
- `examples/<public-id>.json` files are public-form challenges. Each filename is
  the SHA-256 of the exact visible bytes; demonstration labels are present, while
  query answers and hidden semantics are absent. Duplicate visible payloads are
  rejected and files are written in public-ID order.
- `examples/episode-a.json` and `episode-b.json` are identical retirement markers,
  not challenges and not setting maps. The compact return transport cannot delete
  tracked files; the writer rewrites these markers before every materialization.
- `DESIGN.md` and `IMPLEMENTATION_PLAN.md` record the bounded design and build.

Do not distribute this README, the rules, or private evidence beside a challenge
whose episode parameter is intended to remain hidden.

## Reproduce from the outer packet directory

```bash
python3 review.py run python3 \
  generators/44d20451ce17/workspace/parametric/prototype.py \
  --out ../checks/parametric/destination-edge-v2-evidence.json \
  --public-dir generators/44d20451ce17/workspace/parametric/examples \
  --demos 3 --queries 4

python3 review.py run python3 -m pytest -q \
  generators/44d20451ce17/tests/test_parametric_destination_edge.py
```

The retained evidence contains one complete episode for each setting (three
demonstrations and four distinct queries), exact Racket text and hashes,
selected-generator and prototype source hashes, a shared-input differing
witness, Racket/Python parity, and per-query opposite-setting rival checks. All
seven inputs in each episode are distinct. Public files omit the hidden
parameter, program, and query outputs, and their filenames are unaffected by
private seed/setting metadata or hidden query answers.

## Limits

This is bounded evidence for two values and two retained seeds. The opposite
setting is a meaningful rival, not a complete program search. Passing these checks
does not approve the variant, admit it to training, or alter the canonical family.
Main-task source exposure occurred only after the separate blind solve was frozen.
