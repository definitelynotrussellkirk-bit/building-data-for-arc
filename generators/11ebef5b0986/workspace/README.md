# Review workspace

The selected implementation remains `../generator.py`. These diagnostic tools never become label authorities and do not modify other tasks.

## Tests (from the original packet root)

```sh
python3 -m pytest -q repo/generators/11ebef5b0986/tests
python3 setup_racket.py
python3 run_with_racket.py python3 -m arcpuzzles check 11ebef5b0986 --battery --timeout 4000 --phase after --out ../checks/recheck
```

Use the packet's `run_with_racket.py` wrapper: it enters `repo`, configures the bundled Racket executable and makes `arcpuzzles` importable. For a standalone checkout, run the child commands from the repository root with `src` importable and Racket available. NumPy and pytest are needed by the existing runtime/test stack; no new third-party dependency was added.

## Reusable finite-rival census

```sh
python3 run_with_racket.py python3 generators/11ebef5b0986/workspace/review_probe.py --repo . --phase final --out ../checks/recheck_census.json
```

Defaults: easy/medium/hard; seeds 0..19; indices 0..14; three-demo overlapping windows; no overrides. The tool stages an independent runtime, calls real Racket for every generated input and canonical pair, checks a diagnostic mirror where supplied, hashes source/rules, and saves exact counterexamples plus per-input/output manifests. It reports **draws, unique inputs and overlapping windows separately**. Nonzero failure counts must not be presented as semantic success merely because a process ran.

Use `--task-id OTHER_ID`, `--generator PATH` and `--rivals-from PATH` for another task or an older generator. Canonical `test` accepts either one pair dict or a list of pair dicts. Rival tests are limited to the candidate functions the supplied module actually exposes; no-rival output is not a claim of identifiability. Use `--help` for sampling flags. Returned evidence records the actual temporary runtime location, not a guessed source-relative path.

The recorded baseline run used the frozen baseline generator and the intermediate rival module retained in the review ZIP as `checks/generator_intermediate.py`; their exact hashes are in `checks/census_before.json`. `checks/census_final.json` is an intermediate candidate despite its historical phase label. The authoritative final report is `checks/census_final_v2.json` (generator `3058ecb...`).

## Two assigned audit reproducers

```sh
python3 run_with_racket.py python3 generators/11ebef5b0986/workspace/audit_probe.py --repo . --out ../checks/recheck_audits.json
```

This findings-only tool inspects `d414585aa873` and `4199aa353fa1`, runs 600 ordinary draws for each through real Racket, checks all canonical pairs, and retains targeted override/validator/lesson counterexamples. Its reports distinguish canonical-but-generator-excluded inputs from valid ordinary generated inputs and intentionally invalid mutations. Both audit sources remain unchanged.

## Handoff and failure preservation

See the returned `REVIEW.md`, `DECISIONS.md`, `AUDIT.md`, `QUESTION_ANSWER.md`, `FEEDBACK_TO_CODEX.md` and `RESULTS.json`. Failed regression iterations and the unrelated shared timeout-test failure are retained under `checks/`, with a separate read-only environment probe at `checks/runtime_timeout_diagnostic.py`. Do not infer a semantic Racket change from the comment-only base-authority synchronization.
