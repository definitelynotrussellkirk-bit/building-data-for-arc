# Proposed rectangle-anchor parameter family

**Status:** proposed task-local authoring prototype. It does not alter the approved
`generator.py`, the canonical `5abbdbb61293` rule, approval state, or training
admission. Source parent: `training:ddf7fa4f`.

## Rule family

Each episode fixes one private `anchor` value. The input grammar and core reasoning
stay unchanged: read row-0 markers, find each color-5 rectangle, choose the uniquely
nearest marker to one horizontal point of that rectangle, and recolor the whole
rectangle.

| `anchor` | Horizontal point used for nearest-marker selection |
| --- | --- |
| `midpoint` | `(left + right) // 2`; exact byte-for-byte canonical default |
| `left_edge` | rectangle's left bbox column |
| `right_edge` | rectangle's right bbox column |

The prototype admits only canonical-generator inputs with no exact nearest-marker
tie under **any** declared anchor. Every retained demonstration set includes both
a left-edge witness and a right-edge witness, so fitting the three exact Racket
programs to demonstrations alone leaves only the episode's fixed setting. Query
answers are never used to choose that setting.

## Run the retained three-setting comparison

From the extracted review root:

```sh
python3 review.py run python3 \
  generators/424c822d69f3/workspace/parametric/prototype.py \
  --seed 17 --anchor all --demos 3 --queries 4 --max-attempts 512 \
  --out ../checks/parametric-anchor/final-evidence
```

The output separates visible challenges under `public/` from settings, query
answers, exact Racket programs, source hashes, and certificates under `private/`.
Public filenames are hashes of visible bytes only. The destination must be new or
empty.

Run the focused contract:

```sh
python3 review.py run python3 -m pytest \
  generators/424c822d69f3/tests/test_parametric_anchor.py -q
```

## Adapter surface

`adapter.py` exposes `program(settings)` and
`generate(seed, settings, demos, queries)` for a future owner-controlled
qualification. `promotion.json` declares `anchor`, the canonical default, and
independent count limits: 2–16 demonstrations and 1–16 queries. The default
evidence uses three demonstrations and four distinct queries. A bounded sampler
can still fail explicitly when the requested witness mix is unavailable within
`max_attempts`.

## Evidence limits

The finite rival family is exactly the three declared anchors; identifiability is
not a proof against every imaginable program. The retained evidence exercises one
shared input set at seed 17, while the focused tests cover deterministic selection,
strict numeric boundaries, real-Racket/oracle parity, public/private projection,
duplicate rejection, and tampered-label rejection. Promotion and downstream use
remain separate owner decisions.
