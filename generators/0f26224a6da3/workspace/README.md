# Reusable probes and next-agent handoff

Selected implementation: `../generator.py`, version 3.0.0. Assignment: `review-82548b4b24894693`. Do not reroll the assignment. Workspace scripts are tools, not alternate selected generators. They use Python and the packet's existing runtime; no GPU or model download is needed.

## Maintainer intake first

The return is a delta ZIP with `patches/source.patch`, top-level reports, all decisive check logs, and the visible solve record. Apply through the repository's normal hash-bound intake workflow. Patch paths include `repo/`; a manual `git apply --check` must run from the corresponding extracted packet root, not from inside repo. Do not bypass conflicting baseline hashes or silently overwrite parallel work.

Read `REVIEW.md`, `RESULTS.json`, and `AUDIT.md` in the retained ZIP. Racket rules and audit target sources were not changed. The selected generator is not marked approved. Exact historical commands, exit codes, source hashes, actual temporary runtime directories, and limitations are retained; use fresh output names for reruns because reports are intentionally exclusive-created.

## Explicit task-local tests

From the extracted packet root:

```sh
python3 -m pytest -q repo/generators/0f26224a6da3/tests
```

The review's final run has 43 passes. The root repository suite may not collect these tests. With Racket configured, the separate shared suite has one known failing timeout fixture; see the retained diagnostic rather than changing shared files inside a task-scoped review.

## Independent Racket-backed curriculum census

```sh
python3 setup_racket.py
python3 run_with_racket.py python3 generators/0f26224a6da3/workspace/probe_curriculum.py --out ../checks/curriculum-rerun.json --baseline ../checks/baseline_generator.py
```

The baseline argument is optional. It is available when the retained return evidence is unpacked into checks/. The tool stages an isolated runtime, uses actual canonical Racket outputs, imports the selected generator's rival declarations, checks every canonical pair, and tests all cyclic starts for three-demo lessons. It records repeated-draw versus unique-input counts. Its own runtime directory is captured rather than inferred from path depth. Default census is seeds 0..9, indices 0..8, four bands; lesson starts 0..5 overlap.

## Gate actual exported lessons after assembly

To create a fresh author-side labeled export from the current unapproved source:

```sh
python3 run_with_racket.py python3 -m arcpuzzles generate 0f26224a6da3 --count 3 --seed 317 --train 3 --test 1 --allow-unapproved --out ../checks/episodes-rerun.jsonl
python3 repo/generators/0f26224a6da3/workspace/check_assembled_lessons.py checks/episodes-rerun.jsonl --out checks/gate-rerun.json
python3 repo/generators/0f26224a6da3/workspace/make_assembly_stress.py checks/episodes-rerun.jsonl --out checks/stress-rerun.jsonl
python3 repo/generators/0f26224a6da3/workspace/check_assembled_lessons.py checks/stress-rerun.jsonl --out checks/stress-gate-rerun.json
```

The ordinary gate should exit 0 on that exact reproducible export; the final deliberately under-informative lesson must exit 1. Its labels are unmodified Racket-derived labels and it is explicitly marked an intentional assembly negative. Do not record it as a natural solve failure. Gate private labeled authoring data only, never public answer-free solve challenges. Current-source identity is checked. A finite declared-rival check does not certify all possible rules or replace reference-label validation.

For generic reuse, call `check_episode(episode, rivals)`. A missing rival contract, missing labels, or rival exception is not a pass. The CLI is pinned to this task's current generator; a shared integration must resolve and verify each task's contract instead of reusing this task's rival set for unrelated tasks.

## Audit and timeout reproductions

```sh
python3 run_with_racket.py python3 generators/0f26224a6da3/workspace/audit_assigned.py --out ../checks/audits-rerun
python3 run_with_racket.py python3 generators/0f26224a6da3/workspace/probe_runtime_timeout.py --out ../checks/timeout-rerun.json
```

Audit target 5ffd8d801705 has a measured positional shortcut; 6027a830c96e has a domain-qualified validator/reference mismatch plus ignored overrides. Both remain unchanged. The timeout probe contrasts normal/site-disabled child startup and several deadlines; it does not patch shared tests or relax production timeouts.

## Next work, in priority order

Integrate the post-assembly gate at the real training-admission boundary after maintainer review, retaining the upstream Racket/source/rule checks. Hash-deduplicate final examples before counting training-data volume. Fix audit targets only in their own assignments. Address the shared timeout fixture independently, with a readiness-aware test rather than a blanket timeout increase. Then evaluate held-out model performance; no Qwen training or accuracy uplift is established by this review.

A fresh solve exists and is bound to the final generator hash. Do not change generator.py and reuse that solve as if fresh; preserve it and prepare a new episode if the source changes. Earlier rule exposure was yes, consultation during solve no, private-query score unknown. No genuine failed candidate was produced.
