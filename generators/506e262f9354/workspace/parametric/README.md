# Proposed expansion-direction prototype

This task-local prototype adds one **proposed, unapproved** episode-level rule
parameter to ARC family `training:db3e9e38` / generator `506e262f9354`.
It does not modify the canonical generator, canonical Racket authority,
approval state, or training admission.

## Parameter

| name | values | canonical/default | selected |
|---|---|---|---|
| `expansion_direction` | `up`, `down` | `up` | once per episode from the deterministic episode seed, unless explicitly supplied |

`up` returns the exact canonical Racket source byte-for-byte (raw SHA-256
`7d00cd1a50d3b572eb7a50d096cb5d01f0e7af4d8f9bc403d42a3b905b20dc6f`).
It uses the bottom endpoint of the vertical color-7 source as the apex and
expands upward. `down` uses the top endpoint as the apex and expands downward.
No input constraint depends on this parameter.

Both settings preserve the same reasoning steps:

1. locate one contiguous vertical color-7 source;
2. select the endpoint facing the expansion direction as the apex;
3. paint a canvas-clipped triangle whose horizontal reach grows one cell per row;
4. alternate colors 7 and 8 by horizontal distance from the source column;
5. write zero outside the triangle.

## Exact four-query command

Run from the outer extracted packet directory:

```bash
python3 review.py run python3 generators/506e262f9354/workspace/parametric/prototype.py \
  --seed 17 --difficulty medium --train 3 --test 4 \
  --out ../checks/parametric/506e262f9354-direction-v1
```

The writer executes every canonical check, demonstration, query, rival, and
retained witness with the bundled Racket bridge. The Python implementation is
only an independent parity diagnostic. It computes and validates the complete
public content-ID batch before any public challenge write, rejects duplicate
visible IDs atomically, and emits public files in lexical content-ID order.
Existing output directories are rejected rather than overwritten.

## Output layout

- `report.json`: source hashes, Racket runtime identity, parameter declaration,
  exact counts, canonical-default checks, and explicit limitations.
- `canonical-default-check.json`: every labeled canonical pair executed with the
  exact `up` program.
- `setting-difference-witness.json`: one lawful input and both setting outputs.
- `private/episode-{up,down}.json`: hidden setting, exact Racket program, query
  answers, sample provenance, and declared-rival evidence.
- `private/rules/expansion-{up,down}.rkt`: exact executable rule text.
- `public/challenge-<visible-sha256>.json`: demonstrations plus answer-free query
  inputs only. The opaque identifier hashes only the bytes visible to a solver;
  hidden settings, seeds, programs, and query answers cannot affect it.
- `manifest.json`: byte size and SHA-256 for every retained evidence file.

Each setting receives three demonstrations and four distinct queries drawn from
the same seven lawful inputs. The demonstrations alone refute the other declared
direction setting before query answers are considered.

## Limits

The prototype retains the selected generator's current input domain and source
constraints. Finite evidence against the one declared rival does not prove a
unique induction against every imaginable program. The extension remains
separate from production `generate(...)`, canonical approval, and training use.
For repeated programmatic calls, pass one live `RacketBridge` to `make_episode`,
`write_evidence`, or `main`; this avoids repeated runtime startup and is covered
by the focused tests.

## Python claims and proposed promotion interface

`generate_claims(seed, expansion_direction=..., train_count=..., query_count=...)`
reuses the current deterministic sampler and Python diagnostic mirror without
starting a Racket bridge. It returns label claims for an independent worker to
check. The existing `make_episode` and `write_evidence` paths retain their real
Racket execution and caller-owned bridge support.

`adapter.py` exposes the same episode-fixed `expansion_direction=up|down` law
through `program(settings)` and `generate(seed, settings, demos, queries)`.
`promotion.json` declares the exact canonical default `up`, 3–8 demonstrations
and 1–8 queries. The adapter imports the adjacent prototype explicitly, avoiding
module-name collisions with another task's prototype.

The current writer retains version 1.0.1's complete-batch duplicate preflight and
physical content-ID sorting, with an added assertion that every public ID hashes
the exact payload before the first public write. Current seed-1 output preserves
the prior saved visible bytes exactly.

Current decisions and focused source-bound checks are in
`../../evidence/conflict-reconciliation.json`. The original 76-test writer receipt
and the other return's 79-test/formal qualification receipt remain prior-source,
reviewer-reported evidence. The merged implementation has separate focused tests
and Racket replay; it has not received formal qualification or acceptance.
Variants remain proposed, with no production or training change.
