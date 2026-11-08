# Task-local probes and replay

The selected implementation is ../generator.py. These are reviewer diagnostics,
not replacement label generators. They require the existing ARCpuzzles packet
or an equivalent declared source layout; the return ZIP is a delta, not a full
standalone repository. Apply it through normal maintainer intake first.

Run all following commands from the extracted **packet_root**:

```sh
python3 -m pytest -q repo/generators/4a6d26e0b6ae/tests
python3 repo/generators/4a6d26e0b6ae/workspace/verify_distribution.py --seeds 1000 --indices 0,7 --bands none,easy,medium,hard --out checks/replay-integrity
python3 run_with_racket.py python3 -m arcpuzzles check 4a6d26e0b6ae --battery --timeout 4000 --phase after --out ../checks/replay-battery
python3 run_with_racket.py python3 generators/4a6d26e0b6ae/workspace/reference_and_audits.py --mode reference --out ../checks/replay-reference
python3 run_with_racket.py python3 generators/4a6d26e0b6ae/workspace/portable_probe.py --out ../checks/replay-portable
```

`verify_distribution.py` independently finds all gaps from pixels, validates
complete pairs and moats, compares requested/drawn count with observed count,
and retains full source-bound failure records. Exit 1 means a structural failure.
`--source` can select an earlier generator for a before/after test, `--override`
accepts repeated `KEY=JSON` arguments, and seed/index/band controls are explicit. The normal
validator is intentionally task-specific; negative modes need their own domain.

`reference_and_audits.py --mode reference` checks actual Racket parity against
canonical examples and independent diagnostic expectations. Its three extension
fixtures are not claimed as ordinary generated inputs. `--mode audits` reproduces
the unchanged assigned audit findings. Audit command success means the experiment
ran, not that the audited generators passed. Both modes use prepare_runtime and
retain actual runtime paths/manifests. The first failed source-layout attempts
are retained under root checks/ for traceability.

`portable_probe.py` stages only declared runtime files and executes the copied
generator in a fresh child with no PYTHONPATH/PYTHONHOME. It verifies module file
locations, generator SHA, deterministic repeats, self-checks and dense controls.
The actual temporary execution directory is recorded before cleanup, not inferred
from the source tree's parent depth.

The root RESULT/INTAKE reports bind evidence to code; no tool here promotes
catalog approval. Current limitations and the unrelated repository pytest failure
are documented in REVIEW.md. Never erase red iterations to make intake look clean.


## Round 2: fail-closed checks and bounded adversarial coverage

Use a **new output directory** for every run. The integrity tool now refuses
overwrites and duplicate override keys. Independent constraints take explicit
requests before the generator's reported draws. A self-check rejection is a
failure even when pixel structure otherwise looks valid.

```sh
python3 repo/generators/4a6d26e0b6ae/workspace/verify_boundary_contract.py --seeds 3 --mutation-seeds 25 --out checks/replay-round2-boundary
python3 run_with_racket.py python3 generators/4a6d26e0b6ae/workspace/verify_repository_fixture.py --suite full --out ../checks/replay-round2-fixture
```

The boundary tool traverses all 100 declared shapes, all seven textures and
counts 1..8 for nonblank modes. It requires structured refusal outside the
conservative capacity. It exercises `_lattice_fallback` directly: these are
**separate unit-level fallback cases**, not claims about the fallback frequency
in normal sampling. It also checks six mutations and eight dihedral/color
transforms of each positive control. Explicit negatives receive generator
self-check validation, not an independent completeness proof.

`--compare-source checks/round2/source-before/generator.py` compares every
request against the retained round-one source (output grids AND exceptions).
The summary records exact source/probe/scanner hashes and request schedules.

The fixture tool copies the repository, proves the original synthetic-packet
import failure, adds CLI sources to **that fixture's library before packing**,
and reruns the selected tests. It writes `proposed-shared-test.patch` and exact
actual runtime paths. The real shared source and subprocess isolation remain
unchanged. This proposal must be promoted separately by the shared-tool owner;
it is not silently installed by the generator delta.

The sampler's VERSION remains 3.0.0 deliberately: changing it would change its
keyed RNG stream. This round changes validation, not sampling. Source hashes,
not the sampler version string alone, identify the reviewed revision.
