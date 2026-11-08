# Task-local authoring tools

The selected implementation is `../generator.py`. These tools do not select or
approve a different rule.

## Reproduce the mirror teaching contract

From the original packet root after Racket setup, run:

```bash
python3 review.py run python3 generators/72f0b65569a4/workspace/mirror_contract_probe.py --out ../checks/mirror-contract.json
```

Use the Python environment containing the packet's requirements for both wrapper
and payload when necessary. `--help` lists bounded seed, band and window controls.
The default checks 36 overlapping lessons and all 144 single-query rotations,
plus canonical and manual counterexamples, obtaining all labels through Racket.
The output includes exact grids, rule/source hashes, rival predictions and failures.
This diagnostic is separate from the production sampler's larger `lesson-census`.

## Proposed parametric rules

See `parametric/README.md` for complete runnable commands. The prototype materializes
four exact Racket programs from axis × output-color settings, fixes settings once
per episode, and separates public puzzles from private verification evidence.
Its sampler is independent of the selected generator. It does not grant production
parametric support or training admission.
