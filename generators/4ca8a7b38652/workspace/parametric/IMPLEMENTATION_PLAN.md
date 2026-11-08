# Four-query count-scope prototype implementation plan

> For agentic workers: execute this bounded plan inline with test-first changes. The issued task authorizes implementation without a separate approval pause.

**Goal:** Make the proposed count-scope prototype emit independently requested demonstration and query counts, including four distinct queries under one fixed hidden rule.

**Architecture:** Preserve exact canonical Racket text and selected production sampling. Select one setting per episode, draw unique lawful inputs with a bounded rejection budget, execute each candidate setting on those inputs, and decide query identifiability from demonstration consistency. Export only visible demonstrations and query inputs under content-derived opaque public names.

**Tech stack:** Python 3.12, pytest, included protected Racket bridge.

**Spec:** `WORK/PARAMETRIC-RULES.md`, `WORK/ARC-DESIGN.md`, and task delegation for `review-739adb393a726593`.

## Global constraints

- Own only this parametric workspace, focused task parametric tests/probes, and `WORK/checks/parametric-v2/` evidence.
- Preserve `generator.py`, all canonical/shared authority, and old proposal evidence.
- Keep `count_scope` in `{nonzero, all}` fixed for every episode; `nonzero` remains canonical.
- Default to 4 demonstrations and 4 queries; support separate `--train` and `--test` values.
- Query inputs must be distinct from all other episode inputs. A bounded exhausted sampler raises explicitly.
- All retained labels and rival predictions use exact materialized Racket, with Python parity as an additional check.
- Only demonstration consistency determines which settings remain plausible; no query answer becomes teaching evidence.
- Public content and names contain no private setting, seed, reference program, or query answer. Generic public schema and content hashes are public-visible only.
- Run executable probes through the official outer `python review.py run python ...` wrapper.

## Review focus

- Non-default counts retain the requested split and one shared setting.
- Repeated candidate inputs cause retries, or a clear sampling failure at the declared cap.
- Ambiguous zero-free demonstrations cannot identify a zero-present query by borrowing another query answer.
- Bool/float/string/zero/negative counts are rejected before sampling; episode count is bounded to 64 total pairs.
- Public filenames stay unchanged when any private metadata or query answer changes.

## Task 1: Episode counts, unique sampling, and per-query inference

Files: `prototype.py`, `tests/test_parametric_count_scope.py`.
Interfaces: `make_episode(seed, setting=None, *, train_count=4, test_count=4, root=None, verify_racket=True)`, `build_input(seed, pair_index, *, attempt=0, root=None)`, `_assess_query_identifiability(demonstrations, predictions, selected)`.

- [x] Add regression tests for 4/4 defaults, an independent 6/3 split, count validation, repeated candidate rejection, and demo-only per-query identification.
- [x] Run the focused tests and retain the expected pre-fix failures.
- [x] Implement counts, deterministic profile cycling, bounded duplicate rejection, all-setting reference predictions, and explicit per-query evidence.
- [x] Re-run focused tests and retain green evidence.

## Task 2: Reproducible exports and bounded executed evidence

Files: `prototype.py`, `README.md`, `tests/test_parametric_public_names.py`, task-local evidence probe.
Interfaces: `write_evidence(out_dir, *, seeds=None, train_count=4, test_count=4)` plus CLI `--train`, `--test`, and `--seed`.

- [x] Add failing export tests for complete counts, source/program provenance, exact program file hashes, and generic public payloads.
- [x] Implement metadata and CLI forwarding without public setting/seed names or maps.
- [x] Run the complete available selected-task suite: 37 passed. The issued packet has no root `repo/tests/` suite; unrelated audit/proposal trees were not recursively executed.
- [x] Execute complete four-query episodes for both settings on bounded consecutive seed pairs, inspect actual counts, uniqueness, all-setting Racket execution, per-query ambiguity checks, and public/private separation.
- [x] Document exact commands, supported limits, failures, source hashes, and execution counts in a compact task receipt.

## Decisions and ledger

- Ruling: use the already isolated issued checkout, which has no `.git` metadata; keep source-bound receipts instead of creating a new git repository. Cost if wrong: parent integration must rely on issued packet diffs, as designed.
- Ruling: cap an episode at 64 total pairs with 64 draws per requested input. This is an explicit prototype operational bound, not a claim of finite-domain exhaustion.
- Ruling: retain `verify_racket=False` only for fast unit tests; exported evidence always executes Racket.
- Pre-flight: export consumes episode metadata and query checks from Task 1; preserve old private `rival_diff_cells` as a compatible diagnostic.

- Task 1 complete: `red-regressions.txt` retained 7 failures / 15 passes, followed by 25 passing parametric tests. The final selected-task suite contains 37 passing tests after the public-boundary regression fix.
- Task 2 export fixes: `red-export-regressions.txt` retained 2 failures, including the exact rule-file hash mismatch caused by an added newline; `red-public-projection.txt` retained the private training-pair metadata leak before whitelisting.
- Ruling: use the complete selected-task suite because the issued packet omits the configured root `repo/tests/` suite. Recursive discovery would include unrelated audit tasks and old proposals, beyond the bounded assignment. Cost if wrong: project-wide interactions outside the issued task are not exercised here.
- Environment recovery: initial primary-Python pytest was missing; the parent supplied an isolated venv. A transient ENOSPC interrupted a test-file append; the file was reconstructed atomically, compiled, and the intended regression then ran. Task TMPDIR avoids the full overlay filesystem. No prototype code was lost.

- Task 2 complete: three CLI exports cover seeds 0/1, 16/17, and 42/43, with 4/4, 4/4, and 6/4 demo/query counts. All 52 retained inputs and all 24 queries are unique across this bounded collection. Every retained label and rival prediction was executed in Racket: 104 evaluations total.
- Evidence inspection: `verify_evidence.py` completed with status pass, independently checking source/program/file hashes, lawful inputs, counts, public/private projection, and all 24 per-query demo-only rival checks. It did not re-execute Racket or add labels.
- Final source state: selected generator SHA remains `9e39ddd0012e5dba7be9e7ae10f3ac8de0ca736e8c7bfad79a3535b4ae352ac5`; prototype source SHA is `d5fe57a4181bf4b3ce9fb4b65455aa76437a287d56987dc6de9c84eecc1d861c`.
- Final review handoff: parent has the stable review surface and exact evidence paths; no additional implementer subagent could be dispatched because all four collaboration slots were occupied.
