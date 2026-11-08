# Pair-span scope prototype (`0eabac67e70a`)

This task-local prototype is separate from the approved canonical generator. It
adds one episode-fixed rule parameter while preserving the exact canonical
Racket program as the default. It does not change production approval, native
acceptance, training admission, or allocation.

## Rule parameter

Each nonzero endpoint color occurs exactly twice. Its two cells define an
inclusive horizontal, vertical, or 45-degree sign-step span.

| `span_scope` | Executed transformation |
|---|---|
| `all_pairs` (default) | Paint every endpoint pair's complete span with color 8. `program()` returns the exact canonical Racket text (SHA-256 `4a7acff260a86c686966744190dc9d977bc36b50cefaf25d5996fc6642fc5129`). |
| `junction_cluster` | First compute every pair span and the unique cell covered by two spans. Then paint only the two spans that contain that input-dependent junction. |

The alternative has a required sequential dependency:

1. **A:** form every same-color endpoint span and count span coverage by cell.
2. **Intermediate:** the unique multiply covered junction coordinate.
3. **B:** select and paint only spans containing that coordinate.

B cannot choose its spans before A identifies the junction. A protected-Racket
counterfactual witness is retained with native qualification evidence.

## Constructive input family

Every scene contains one crossing horizontal/vertical pair plus one to four
non-crossing horizontal distractor pairs. Inputs are identical across settings
for the same seed and counts. The first two demonstrations deliberately refute
four finite shortcuts: reuse the first demonstration's colors, choose the two
longest spans, choose the two shortest spans, or choose the two spans nearest
the grid center.

Supported API counts are 2–6 demonstrations and exactly four queries. Query
shapes are 7×7, 12×16, 22×26, and a substantive 30×30 stress case with six
endpoint pairs. All inputs within an episode are distinct.

## Reproduce focused checks and evidence

From the extracted packet's outer directory:

```bash
python3 review.py task-tests 0eabac67e70a --phase after \
  --out ../checks/0eabac67e70a-tests

python3 review.py run python3 \
  generators/0eabac67e70a/workspace/parametric/verify.py \
  --seed 0 --seed 17 --demos 3 \
  --out ../checks/0eabac67e70a/evidence-rebuild

python3 WORK/check_public_exports.py \
  WORK/checks/0eabac67e70a/evidence-rebuild/public \
  --queries 1 --demos 3
```

Each public file repeats the demonstrations and reveals exactly one query input,
without settings, seed, program, query answer, future query, or total-query hint.
Its filename is the SHA-256 of the exact visible bytes produced by
`reviewer_support.public_challenge_bytes`. Private query ordering and metadata
remain in `projection-index.json`.

After the evidence inventory is current, qualify every setting through protected
Racket:

```bash
python3 review.py run python3 -m arcpuzzles parametric qualify 0eabac67e70a \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/0eabac67e70a/qualification --summary
```

## Evidence limits

The teaching audit checks two declared settings and four named shortcut families
across seeds 0–11 at 2, 3, and 6 demonstrations. It is not a proof of uniqueness
against every possible ARC program. Public projection checks establish visible
serialization and isolation, not label correctness. Native qualification and the
causal witness provide bounded protected-Racket execution; exact-source owner
acceptance is still required after integration.
