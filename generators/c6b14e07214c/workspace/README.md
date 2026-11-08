# Reusable reviewer tools and handoff

## Complete-lesson census

`probe_lessons.py` is generic over a task's declared `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, witnesses and cycle length. It stages an independent copied runtime, explicitly selects canonical Racket authority, caches labels within a seed, checks validators and runner-pair validity, verifies witness claims, then evaluates entire demo/query windows. It retains source hashes, seed/index ledger, actual runtime location, all failures and representative counterexamples. It never supplies Python positive labels and never sends offline query answers to a solve prompt.

From packet root after applying the delta:

```sh
python3 run_with_racket.py python3 generators/c6b14e07214c/workspace/probe_lessons.py --seeds-per-band 100 --out ../checks/new-census.json
python3 run_with_racket.py python3 generators/c6b14e07214c/workspace/probe_lessons.py --seeds-per-band 10 --demos 2 --out ../checks/new-negative-control.json
```

The first checks100 seeds ×3 cyclic starts ×3 bands=900 windows, with overlapping windows counted separately from unique inputs. The second deliberately degrades teaching and should exit2 for this source. Existing evidence files cannot be overwritten. `--starts`, `--sample-step`, `--demos`, and JSON `--overrides` support alternative assembly probes. A different step or override may legitimately remove required contrasts and produce failures. `--task-id` can target another generator with executable rivals. The current query policy is generated queries only; canonical/domain-counterexample queries are a future extension. The tool is not a universal identifiability proof or an arbitrary-language hypothesis searcher.

## Read-only assigned audits

```sh
python3 run_with_racket.py python3 generators/c6b14e07214c/workspace/audit_assigned.py --seeds 100 --out-dir ../checks/new-assigned-audits
```

This second tool is deliberately restricted to the two immutable targets of assignment `review-a17bad0aece71558`, not a general audit dispatcher. It does not select another task, mutate either target, or generate training labels in Python. It reproduces a clamped-cycle rival, a column-projection segmentation rival, exact-control probes, canonical checks, and source-bound hand-constructed counterexamples. Exit0 means the harness completed, not that the target generators passed an admission gate.

## Tests

```sh
python3 run_with_racket.py python3 -m pytest -q generators/c6b14e07214c/tests
python3 run_with_racket.py python3 -m pytest -q
```

The first discovers19 task-local tests; the second discovers174 repository tests in this packet. Run both, because repository discovery does not include the new task tests automatically. The Python tools use only standard-library modules plus the existing ARCpuzzles runtime. Racket is supplied by the packet's setup/wrapper; no extra package install is needed.

## Next agent

Read the final return's REVIEW/DECISIONS and `checks/acceptance-*` evidence first. The folders named `after` and `final` inside the history archive are failed intermediate iterations, not final acceptance. Do not rebuild a four-corner generator or relax the canonical/profile controls to silence a gate. Preserve RULE_HASH and approval state. A new generator edit must get a new full battery, source-bound census, and fresh solve episode; old green results are not transferable to new bytes.
