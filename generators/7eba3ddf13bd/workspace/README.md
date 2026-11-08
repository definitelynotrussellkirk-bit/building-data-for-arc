# Portal review tools

The selected input implementation is `../generator.py`. These workspace tools do not become an alternate label authority.

## Differential probe

From the portable packet root after applying the source patch:

```bash
python3 setup_racket.py
python3 run_with_racket.py python3 generators/7eba3ddf13bd/workspace/portal_probe.py \
  --seeds 200 \
  --cases generators/7eba3ddf13bd/workspace/portal_cases.json \
  --out ../checks/my-portal-probe
```

The output directory must not already exist. `--seeds` is the number per difficulty band, so 200 means 600 generated inputs. `--help` does not require Racket. Invalid sample counts fail before creating the output directory.

The probe creates an isolated execution layout from the local repository, executes the selected canonical Racket program, compares the Python diagnostic mirror, and records every input and output in `cases.jsonl`. `report.json` contains source bindings, deterministic sampling protocol, counts, failures, and diagnostic timing. `witnesses.json` contains the first generated counterexample to each named rival, with exact seed/index/band, input, true output, and rival output.

For an old or alternate implementation of the same task:

```bash
python3 run_with_racket.py python3 generators/7eba3ddf13bd/workspace/portal_probe.py \
  --generator ../.review/baseline/repo/generators/7eba3ddf13bd/generator.py \
  --seeds 200 --out ../checks/my-baseline-probe
```

The analyzer remains the revised source, while the target generator is copied from the supplied path. Both hashes are reported. Nonzero exit is expected for the original 2.0.0 baseline under the retained protocol because some generated outputs are identity.

## Boundary fixtures

`portal_cases.json` covers input color-8 portals, exactly-three multiplicity, mandatory teleport-on-entry, external shortest-path ties, and an unreachable grid. Some fixtures are valid for rule execution but intentionally fail ordinary training admission. Do not move them into legal generation overrides.

The canonical 4→5 portal intervention is included automatically by the probe, independently of random generation.

## Tests and semantics

```bash
python3 run_with_racket.py python3 -m pytest -q generators/7eba3ddf13bd/tests
python3 run_with_racket.py python3 -m pytest -q
```

The first command runs task-local regressions; the second runs the repository's configured public suite. Both are required. `EXAMPLES_NEEDED=4` assumes consecutive sample indices. The semantic hooks cover only four declared rivals, and the Python mirror is for construction/diagnostics, never a replacement for executed Racket labels.
