# Proposed maze connectivity/phase episodes for `44690b1b635f`

**Status:** task-local, proposed, and unapproved. The selected production generator, canonical ledger row, approval hashes, and training admission are unchanged.

This prototype keeps the original reasoning pattern: identify the singleton marker as the BFS origin, treat color `8` as walls, preserve markers/walls/unreachable zeros, and color reachable zeros by distance parity. It varies only two fixed-per-episode rule choices:

| Parameter | Values | Canonical default |
|---|---|---|
| `connectivity` | `cardinal`, `king` (8-neighbor) | `cardinal` |
| `phase` | `center_even`, `arm_even` | `center_even` |

The default Racket source is byte-identical to the canonical authority (SHA-256 `d78c0152b4b3f003a6ceaf2601ffb3234247354b626267c771a1bcf51d25e618`; normalized rule hash `72a0e00e932b`). The other three programs are guarded substitutions of exactly the connectivity token and/or parity-color branch.

## What is built

- `prototype.py`: strict settings/grid validation, exact Racket materialization, independent Python BFS oracle, procedural maze sampler, fixed-setting episode generator, visible-only projection, atomic evidence writer, and CLI.
- `adapter.py`: thin future-qualification adapter exposing `program(settings)` and `generate(seed, settings, demos, queries)`.
- `promotion.json`: machine-readable proposed parameter/limit contract; it is not an approval record.
- `evidence/manifest.json`: task-local owner inventory binding the reviewed prototype, adapter, contract, documentation, focused test, unchanged generator, and canonical authority hashes.
- `tests/test_parametric_route_variants.py`: Racket-backed focused tests, including public/private redaction, duplicate-visible-output refusal, and inventory verification.

Every admitted input contains a cardinally reachable component, an additional component reachable only with 8-neighbor traversal, and a zero pocket unreachable under either setting. All four declared settings therefore produce distinct outputs on every retained input. Inputs depend on seed/slot only—not the hidden setting. Demonstrations alone must leave one setting, and each query must disagree with all three eliminated rivals.

## Run from the packet root

```bash
python3 review.py setup
python3 review.py run python3 -m pytest -q \
  generators/44690b1b635f/tests/test_parametric_route_variants.py

python3 review.py run python3 \
  generators/44690b1b635f/workspace/parametric/prototype.py \
  --out ../checks/parametric/44690b1b635f-maze-connectivity-phase-v1 \
  --seeds 0 1 2 3 --demos 3 --queries 4
```

The retained run writes content-hash-named visible challenges under `public/`; seeds, settings, Racket text, hashes, and query answers stay under `private/`. `manifest.json` hashes every retained public/private data file and lists episodes sorted by visible content ID.

## Limits

- Counts are independently configurable from `1..8`; the retained evidence uses 3 demonstrations and 4 queries.
- The declared rival family is exactly the four connectivity/phase combinations, not every imaginable maze program.
- Finite seed evidence is not a proof over all procedural seeds.
- Promotion still requires owner qualification through the repository’s normal parametric process.
