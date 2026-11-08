# Task-local review tools

These tools accompany review-07a244fdb4952d5c. They supplement, not replace, the standard battery. Run wrapper commands from the extracted packet root after applying the source patch. Existing evidence files are intentionally not overwritten; use new output filenames on replay. No GPU or model API is required.

## contract_probe.py — declared-domain structural and reference census

```sh
python3 setup_racket.py
python3 run_with_racket.py python3 generators/0ae119475d57/workspace/contract_probe.py   --seeds 1000 --racket-per-stratum 12 --out ../checks/contract-replay.json
```

The wrapper switches to repo and configures the offline Racket runtime. The probe tests default width plus each declared width 4..16 in each band, with sample_index=seed%4. It records source/rule hashes, observed and unique-input counts, every failure, independent unique-separator checks, branch counts, witnesses, replay checks and full selected Racket input/output pairs. Racket parity uses a runtime prepared through the public API; the report names its actual temporary directory. Exit 0 means no recorded failure; exit 1 means a counterexample was found.

`--seeds 200 --racket-per-stratum 0 --generator PATH` supports structural comparison against a staged older source. The path is relative to the inner repo working directory when used through the wrapper. A count of observations is not a count of unique inputs: default and explicit width strata can overlap. Global random state is checked, but the report does not claim every possible seed was tested.

## lesson_palette_gate.py — visible-only episode ambiguity

```sh
python3 repo/generators/0ae119475d57/workspace/lesson_palette_gate.py   --challenge solve/challenge.json --out checks/palette-replay-original.json
# Exit 1 expected for the retained episode.
python3 repo/generators/0ae119475d57/workspace/lesson_palette_gate.py   --challenge checks/palette-contrast-lesson.json --out checks/palette-replay-contrast.json
# Exit 0 expected for the separately supplemented lesson.
```

The six explicit candidates are lower overlay, upper overlay, copy upper, copy lower, minimum nonzero color and numeric maximum. Candidates must fit every demonstration; surviving query predictions must agree. Distinct surviving programs are not rejected when they agree on the query. The tool reads only visible JSON and refuses query output labels. It imports no generator or reference solver. Exit 0 means finite-candidate agreement, 1 means ambiguity, and 2 means malformed or unsupported input. No result is a proof against all programs.

The returned `checks/build_contrastive_lesson.py` reproduces a separate augmented lesson using one already-scored donor in `checks/contract-final.json`. It never modifies the frozen solve or reads private query labels. Retain its provenance. Shared assembler integration is not part of this patch.

## Tests and portable runtime

The two workspace test files run from packet_root:

```sh
python3 -m pytest -q repo/generators/0ae119475d57/workspace/test_contract_probe.py
python3 -m pytest -q repo/generators/0ae119475d57/workspace/test_lesson_palette_gate.py
```

They contain four and five tests respectively. The 77 generator tests belong to the portable runtime, not the source-layout import path:

```sh
python3 run_with_racket.py python3 -c "from pathlib import Path; from arcpuzzles import Catalog; from arcpuzzles.runtime import prepare_runtime; prepare_runtime(Catalog(), Path('../.review/test-replay'), '0ae119475d57')"
cd .review/test-replay
python3 -m pytest -q tests/test_generator_0ae119475d57.py
```

The actual final runtime used during the review was `.review/test-final`; the above deliberately uses a new directory on replay. The repository command `python3 run_with_racket.py python3 -m pytest -q` is additional, not a substitute for these task-local commands. It retained one unrelated startup-budget-sensitive failure in this environment. See root RESULTS.json and checks/ for exact executed commands, exit codes, intermediate failures and final source hashes.
