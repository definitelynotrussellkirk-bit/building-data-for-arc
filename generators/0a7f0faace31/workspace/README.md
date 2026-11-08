# Workspace: 0a7f0faace31

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Reusable final verifier

`verify_review.py` is the current source-bound authoring command. It resolves
the local repository with public `reviewer_support`, imports the selected
generator through `importlib`, and iterates its actual `CANONICAL_SHORTCUTS`,
`LESSON_COMPETITORS` and `SEMANTIC_RIVALS` dictionaries. It does not copy a
rival-name list, read solve records or import private runners. Actual reference
outputs come from public `Catalog.apply`; Python mirrors remain checks.

From the extracted packet root, write to a **new** output path:

```bash
python3 run_with_racket.py python3 generators/0a7f0faace31/workspace/verify_review.py --seeds 1 --out ../checks/reusable-probe-final.json
```

The wrapper's payload cwd is `repo`, so generator paths start with
`generators/` and packet-level evidence paths start with `../checks/`.
`--seeds` takes explicit seed integers; `--seeds 1` means seed 1. Multiple seeds
may be supplied, but the final retained full census uses one seed. `--quick`
reduces each dimension to its minimum/middle/maximum and tests the default
difficulty setting; it does not stand in for the full joint-control census.

The full command tests all declared height/width values, styles and textures
at `None`, `easy`, `medium` and `hard`. It records structured declared
incompatibilities, validates generated inputs, observes controls from pixels,
checks all canonical rival fits, and obtains one small reference batch. Reports
include source and probe hashes, exact argv/cwd, seeds, enumeration/index policy,
counts, unique inputs, representative reference grids and bounded first
counterexamples. Existing output paths are refused; source changes during the
run are failures. This verifier leaves production lesson assembly and rotations
to the shared `arcpuzzles lesson-census` command.

The final retained run on 3.0.1 hash
`48efc388363dec9a69e0ac82dca3fbddc25b049255e9d39ea6dfad9714c9b13e`
accepted 11,492 of 13,520 joint attempts and recorded 2,028 declared full-frame
incompatibilities. Exact controls and validator checks passed on all 11,492
accepted unique inputs; Racket parity passed 33/33 labels,25 unique inputs.
All 18 rivals in each namespace fit all 3 canonical pairs. These are finite
checks, with full details in `checks/reusable-probe-final.json`.

## Historical semantic analysis

`semantic_probe.py` and `semantic_analysis.md` retain the initial 2.2.0
canonical analysis, thirteen rivals and compact authored witnesses. Their
packet evidence is under `checks/semantic/`. The final generator subsequently
added five rivals and changed its compound geometry; do not present those
historical files' thirteen-rival counts or initial compound as the final
curriculum. `checks/reusable-probe-intermediate.json` likewise belongs to the
earlier 3.0.0 source. Counterexamples and failed intermediate checks are retained
as evidence rather than rewritten into final successes.

## Interpretation limits

Default period 3 `teaching, teaching, ordinary` provides redundant compound
witnesses for three-demo lessons and single-query rotations. Teaching shapes
have fixed relative geometry and 3×4 selected crops. Ordinary slots supply
broader connected shapes and frame styles; explicit overrides can replace the
curriculum. Final 300 production lessons and 1,200 rotations were clean against
the 18 declared rivals, but neither the schedule nor finite census proves
universal identifiability. See `../notes.md` for exact scope and controls.

The final census is retained losslessly as
`checks/lesson-census-final.json.gz`; the earlier census is
`checks/lesson-census.json.gz`. Packet `checks/COMPRESSED-EVIDENCE.json` maps
original paths, sizes and SHA-256 values and records the roundtrip check.
Follow `checks/COMPRESSED-EVIDENCE.md` to restore the JSON reports before a
tool expects their original filenames. Compression does not alter the source
identity or measured counts.
