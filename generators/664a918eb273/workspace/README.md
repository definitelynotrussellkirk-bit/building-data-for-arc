# Task-local reproducible path review tools

The selected implementation is `../generator.py`. These tools are review aids;
none bypasses Racket label generation or training admission. Run the following
from the **extracted review packet root**, after applying the source patch there.

```bash
python3 setup_racket.py
export RACKET_PATH="$PWD/.review/racket-runtime/racket/bin/racket"

python3 repo/generators/664a918eb273/workspace/path_probe.py \
  --repo-root repo --samples 9000 --racket-samples 450 \
  --out checks/path-recheck.json
python3 -m pytest -q repo/generators/664a918eb273/tests/test_path_contract.py
python3 repo/generators/664a918eb273/workspace/portable_check.py \
  --repo-root repo --out checks/portable-recheck
python3 repo/generators/664a918eb273/workspace/adversarial_audits.py \
  --repo-root repo --out checks/audits-recheck.json
```

`path_probe.py` independently inspects component endpoints, placement, cell
conservation, and safe geometric output. It actually invokes the canonical Racket
program through a persistent runtime for `--racket-samples` cases. Its report binds
the generator SHA256, records exact counterexamples, and reports errors rather
than treating successful Racket execution as evidence of semantic correctness.
As a diagnostic census, its process exit code is not a semantic pass/fail verdict;
inspect the report or use portable_check, which checks the complete semantic counts.
The geometry model is task-specific: pixel conservation is not a global ARC rule.

To compare the frozen old generator without overwriting the repair:

```bash
python3 repo/generators/664a918eb273/workspace/path_probe.py \
  --repo-root repo \
  --generator .review/baseline/repo/generators/664a918eb273/generator.py \
  --samples 900 --racket-samples 450 --out checks/baseline-recheck.json
```

The baseline path exists in the original assigned packet, not in the small delta
return by itself. `unsafe_inputs.json` retains the exact original witnesses for
regressions without requiring that baseline module.

`portable_check.py` builds a copied runtime, explicitly adds the newly created
workspace/tests files omitted by the old frozen runtime mapping, **renames the
staging directory before execution**, and runs tests plus a 600/90 census there.
It retains the actual runtime path, command arrays, return codes, logs, and code
hash. Its verdict requires both successful commands and a complete zero-defect
600/90 report with all five canonical examples matched. It uses clean child imports and `-E -s`; it does not claim OS-enforced denial
of access to the source tree. A current installed pytest and accessible Racket
executable are still required. Temporary runtime directories are removed afterward.

`adversarial_audits.py` is a read-only probe of the two immutable audit assignments
plus the assigned task's strongest canonical-fit rival. It retains exact grids,
actual Racket outputs, shortcut comparisons, sample counts, and source hashes.
Audit findings are not silently converted into source changes or admission status.

The regression suite tests malformed grids, original unsafe cases, canonical
examples, all difficulty bands, deterministic generation, boundary overrides,
canonical-authority synchronization, and executable witness/rival disagreements.
The independent probe is not a universal solver or a proof of lesson uniqueness.
