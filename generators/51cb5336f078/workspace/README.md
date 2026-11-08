# Frame-generator review tools

`lesson_probe.py` is an executable task-local probe, not an alternative generator or label authority. Run from an extracted packet:

```sh
python3 run_with_racket.py python3 generators/51cb5336f078/workspace/lesson_probe.py --out ../checks/new-probe.json
```

The wrapper runs from `repo/`. The probe exhausts 12,288 combinations of dimensions, size, endpoint colors, three bands and both schedule residues at seed 73. It then checks seeds 0..99, sample indices 0..11 in each band: 3,600 draws, 2,400 overlapping four-pair windows and all 9,600 one-query rotations. Rival declarations are discovered from the generator rather than hard-coded. Sixty inputs are checked against canonical Racket through `Catalog.apply`; Python-spec outputs are never exported as training labels.

To reproduce the retained baseline ambiguity, supply the original source copy from the return:

```sh
python3 run_with_racket.py python3 generators/51cb5336f078/workspace/lesson_probe.py --generator ../checks/baseline-generator.py --baseline-counterexample --out ../checks/new-baseline-ambiguity.json
```

The baseline counterexample's input source hash is separate from the selected-source identity in the Racket apply receipt. The rule is unchanged, so the receipt can authoritatively label these hand-supplied baseline inputs. The tool verifies the Python specification against those Racket outputs.

For production lesson assembly, including actual accepted sample indices and possible rejection behavior, use the shared public census instead:

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 51cb5336f078 --per-band 100 --rotate-query --timeout 1800 --out ../checks/new-lesson-census.json
```

Focused tests live in `../tests/` and are portable via `reviewer_support`. Run them with the dedicated `arcpuzzles check ... --stage task_tests` command; the normal repository suite does not discover task-local tests. Never use these authoring tools during a visible-only solve.
