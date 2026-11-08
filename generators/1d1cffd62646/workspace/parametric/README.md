# Three-dot concentric squares: proposed ring stride

This task-local extension preserves the original `training:5c2c9af4` inference:
find the middle of three equally spaced dots, infer Chebyshev spacing, and draw
concentric square outlines clipped by the grid. It is a proposed family, with a
promotion adapter ready for the owner's separate qualification/acceptance step.
Neither this prototype nor its examples are admitted to training automatically.

## One meaningful rule parameter

| `ring_stride` | Executed rule |
|---|---|
| `1` (canonical default) | Center and every ring at radius `k * dot_spacing`. |
| `2` | Center and positive odd-numbered rings: radii `spacing`, `3 * spacing`, `5 * spacing`, etc. |

The first ring always contains the endpoint dots. Stride 1 returns the exact
canonical Racket source in `canonical.rkt`, without rewriting it. Stride 2 applies
one checked substitution to ring enumeration. Production uses the unchanged
canonical rule; this extension does not replace it. The parameter changes output
geometry, while preserving center selection, dot-distance inference and clipping.

## Run from the outer packet folder

```bash
python3 review.py setup
python3 review.py run python3 generators/1d1cffd62646/workspace/parametric/prototype.py build --seed 17 --demos 2 --queries 4 --out ../checks/rings-new
python3 review.py run python3 generators/1d1cffd62646/workspace/parametric/prototype.py verify ../checks/rings-new
python3 WORK/check_public_exports.py WORK/checks/rings-new/public --demos 2 --queries 4
python3 review.py run python3 -m unittest discover -s generators/1d1cffd62646/tests -v
```

`build` emits both settings on the same inputs. Select one with `--ring-stride 1`
or `--ring-stride 2`. Use a fresh output directory. No pytest install is needed.
Every exported target is executed through matching Racket and checked against an
independent distance-based Python mirror. `verify` replays both parameter programs
on every saved demonstration/query, then recomputes labels and certificates.

Only `public/` contains model-visible challenges. Its filenames are SHA-256 of
the exact visible bytes written: demonstrations plus query inputs. Hidden seeds,
parameters, programs and query targets appear only in `private/episodes.jsonl`.
The writer sorts by public ID, rejects duplicate visible payloads before creating
its directory, and refuses existing destinations. The manifest is written last.
Calling `verify_episode` or `verify_batch` without a bridge performs structural,
source/hash, Python-label and certificate checks only; it makes no Racket replay claim.

## Sampling and teachability limits

Demonstration count is independently configurable in **2..8**, query count in
**1..8**; booleans, floats and numeric strings are refused. The default is two
demos and four distinct queries, all under the same parameter setting. Queries
include 21x27, 30x30, 27x18 and 19x30 grids. No padding or copied input pairs is
used to meet the requested count. Sampler inputs are identical across settings
for the same seed/counts, with an input seed separate from the rule parameter.

Sampling uses the repaired production generator's horizontal, vertical and two
diagonal directions. Its two initial demos use different dot spacings. Up to 64
complete attempts are allowed; exhausted sampling raises instead of emitting a
partial episode. The transform/certificate also accepts smaller lawful grids
(up to 30 per side) for underidentification witnesses; ordinary sampling starts
at 10 per side. Arbitrary non-45-degree slopes admitted by production validation
are outside this prototype's declared grammar.

Each episode's demonstrations are checked against **22 explicit hypotheses**:
both parameter settings plus, under each setting, first/last-dot centers, fixed
spacings 2..6, Manhattan rings, first-ring-only and wholly-contained-square-only
shortcuts. The certificate reads demonstration labels and query inputs only;
changing hidden settings or query answers cannot influence it. A surviving
hypothesis is problematic only if it changes a query prediction. Generated
lessons additionally require the selected setting to be the sole survivor.
These finite rivals do not prove uniqueness against arbitrary programs. Shortcut
predictions are Python hypotheses; both lawful parameter programs are checked
against actual Racket.

## Owner pickup

`adapter.py` reuses the same sampler, mirror and certificate. It returns Python
claims for the public qualification worker to re-execute through protected
Racket; it does not run an extra Racket process itself. `promotion.json` declares
the exact parameter domain, default, independent counts and canonical resource.
The source/evidence manifest is an inventory, not a qualification or approval.
The production repair must be accepted separately before owner qualification.
