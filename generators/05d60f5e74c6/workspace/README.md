# Reusable review workspace

The selected implementation is ../generator.py. These are explicit tools, not
alternate automatically selected generators. Run all commands below from the
extracted packet_root unless noted. `run_with_racket.py` selects the supplied
verified Racket installation and changes to repo; its Python subprocess then
uses the native staged runtime. Install/setup it with `python3 setup_racket.py`.

## Selected-task contract tests

```sh
python3 -m pytest -q repo/generators/05d60f5e74c6/tests/test_review_contract.py
python3 -m pytest -q repo/generators/05d60f5e74c6/tests/test_review_tools.py
```

## Source-bound probe

```sh
python3 run_with_racket.py python3 generators/05d60f5e74c6/workspace/review_probe.py --task-id 05d60f5e74c6 --phase final --racket --seeds 100 --samples 8 --bands easy medium hard --textures default --out ../checks/final_census.json
python3 run_with_racket.py python3 generators/05d60f5e74c6/workspace/review_probe.py --task-id 05d60f5e74c6 --phase final --racket --seeds 100 --samples 1 --bands easy --textures blob thin l_merge --out ../checks/final_forced_textures.json
```

Add `--baseline --phase before` in place of `--phase final` to inspect the
assignment's immutable baseline. This needs that packet's `.review/baseline`;
do not expect the returned delta alone to contain the complete repository.
Exit0 means no failures in the measured scope; exit1 means retained failures.
Actual source/rule/row/prelude hashes and historical runtime directory are in
reports. The stage is a native source runtime, not a fresh wheel installation.

The tool reads actual CANONICAL_SHORTCUTS and LESSON_COMPETITORS dictionaries.
A missing registry is not universal identifiability evidence. Generic geometry,
source binding and runtime code can serve other generators; blob/thin/L checks
are specific to this task family. Complete consecutive windows are tested, not
arbitrary random permutations. Use new output names to preserve earlier evidence.

## Exact audit evidence

```sh
python3 run_with_racket.py python3 generators/05d60f5e74c6/workspace/audit_targets.py --out ../checks/audit_findings_final.json
python3 run_with_racket.py python3 generators/05d60f5e74c6/workspace/counterexamples.py --out-dir ../checks/counterexamples
```

`audit_targets.py` is fixed to the immutable two-target draw. Exit1 is expected
for current reproduced findings. `counterexamples.py` regenerates four compact
Racket-checked fixtures, asserts the expected discrepancy and exits0. It adds
source identity, exact command and explicit validator/domain status. Audit1's
rival fits canonical train only, not its labeled test. Audit2's diagonal witness
is intentionally outside its 8-halo-separated sampling domain. Do not confuse
these with generic in-domain label errors.

All tools use only standard Python plus the supplied ARCpuzzles runtime stack.
No subprocess executes a downloaded dependency or alternate reference program.
