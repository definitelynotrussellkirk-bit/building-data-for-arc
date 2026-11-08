# Proposed `scale_basis` parametric family

Status: **prototype only**. This family is not qualified, accepted, approved, or admitted to training. The selected production generator and canonical catalog row are unchanged.

## Rule parameter

One hidden setting is fixed for the entire episode:

| `scale_basis` | Executed rule |
|---|---|
| `longer_side` | Canonical/default. Scale the two-color template isotropically by the larger side of the seed's common-color rectangle. The returned Racket source is byte-for-byte the catalog program. |
| `shorter_side` | Nearby alternative. Use the smaller side instead; template/seed detection, color substitution, placement, and clipping are unchanged. |

Inputs use an asymmetric rectangular common-color seed so the two settings always produce different labels. Demonstrations are constructive rather than rejection-sampled: each supported demonstration profile distinguishes both rules, and the same sampled inputs are used for both settings.

## Episode contract

- Demonstrations: independently selectable from **2 through 6**; default 3.
- Queries: **exactly four**, all distinct and novel relative to demonstrations.
- The fourth query is a substantive **30×30** scene with multiple seeds and output contact on all four boundaries.
- Every label is executed through the bundled Racket bridge. `apply_python` is an independent authoring mirror and must agree with Racket for both settings.
- Public challenges contain only demonstration inputs/outputs and query inputs. The hidden setting, Racket program, query answers, sampling metadata, and alternative-setting outputs stay private.
- Sequential publication produces four separate one-query challenges. No turn includes future inputs or a total-count field; turn 0 is exactly the ordinary single-query projection.
- Public IDs and filenames hash exact visible bytes only. The verifier binds inventory, hashes, source/program provenance, projections, turn order, and optionally replays Racket.

## Files

- `prototype.py` — sampler, exact Racket materialization, Python mirror, public/private projections, atomic exporter, verifier, and CLI.
- `adapter.py` — guarded native promotion adapter implementing `program(settings)` and `generate(seed, settings, demos, queries)`.
- `promotion.json` — bounded settings and count contract.
- `evidence/manifest.json` — native source/evidence inventory once generated; it is an author report, not acceptance.

## Focused commands

From the packet's `WORK/` directory:

```bash
python3 review.py run python3 -m pytest \
  generators/78a914ac492e/tests/test_parametric_scale_basis.py -q

python3 review.py run python3 \
  generators/78a914ac492e/workspace/parametric/prototype.py build \
  --seed 7802 --scale-basis longer_side --demos 2 --queries 4 \
  --out ../checks/78a914ac492e-parametric/longer-d2

python3 review.py run python3 \
  generators/78a914ac492e/workspace/parametric/prototype.py verify \
  ../checks/78a914ac492e-parametric/longer-d2
```

The packet does not install the `arcpuzzles` console script, so create the native inventory through its module entry point:

```bash
python3 review.py run python3 -m arcpuzzles parametric manifest 78a914ac492e \
  --evidence generators/78a914ac492e/workspace/parametric/evidence/current \
  --include generators/78a914ac492e/tests/test_parametric_scale_basis.py \
  --reported-checks 'Focused prototype tests plus two Racket-replayed exports: longer_side with 2 demos and shorter_side with 6 demos, each with 4 queries.'
```

## Known limits

The sampler intentionally covers one bounded semantic axis and one template grammar. It proves agreement with the two materialized programs and a finite demonstration distinction; it does not prove universal human/model identifiability. Promotion still requires independent owner qualification and acceptance.
