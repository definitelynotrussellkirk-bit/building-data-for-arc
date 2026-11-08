# Reusable probes and task-local verification

Run commands below from the **extracted packet root** after applying the returned source patch to its matching packet. The `run_with_racket.py` wrapper changes into `repo`; therefore report paths start with `../checks/`. Tools make temporary standalone runtimes and record their actual cwd and manifest hash; they do not depend on inherited `PYTHONPATH`. Racket is the label authority.

```sh
python3 setup_racket.py
python3 run_with_racket.py python3 -m pytest -q generators/f7e325967ea1/tests
python3 run_with_racket.py python3 -m arcpuzzles check f7e325967ea1 --battery --timeout 4000 --phase after --out ../checks/replay-battery
python3 run_with_racket.py python3 generators/f7e325967ea1/workspace/lesson_probe.py --lessons-per-band 120 --baseline ../checks/baseline_generator.py --stress --out ../checks/replay-lessons.json
python3 run_with_racket.py python3 generators/f7e325967ea1/workspace/audit_targets.py --out ../checks/replay-audits
```

Use fresh output names for battery runs; existing stage evidence must not be overwritten or deleted merely to permit replay.

## What each file does

`lesson_probe.py` is reusable across per-puzzle tasks declaring `CANONICAL_SHORTCUTS` / `LESSON_COMPETITORS`. Supply `--task TASK_ID` and omit `--stress` for other tasks. It checks actual declared canonical shortcuts against every usable canonical pair, assembles three-demo/one-query lessons through production `runner.run_one`, executes Racket, retains all failures and baseline wrong-query episodes, checks optional validator/mirror hooks, and counts global as well as per-band unique inputs. It returns nonzero for final contract/probe failures. Deliberate baseline failures are comparison evidence and are not falsely treated as final failures. Missing rival contracts reject, not pass. The worker timeout is 480 seconds, recorded explicitly; larger tasks may need a reviewed budget increase.

`--stress` is specific to f7e325967ea1: dimensions {7,18}, foreground counts 3..9, all difficulty values, all three cyclic starts, and seeds 0..9. It checks exact observations and validates every draw; every counterexample-profile draw is additionally checked against real Racket and all declared rivals.

`audit_targets.py` is intentionally bound to the two immutable targets in this packet. It tests the complete explicit D4 pair matrix for 28ad783a6a98 and a scene-profile/band matrix for 20458da8b222. Exit 0 means successful execution, not a clean audit: inspect `report.json` for findings. Do not call the wall-sensitive domain witness a mislabeled example.

`probe_support.py` supplies independent target-centric Python test helpers, canonical readers, and geometric transforms. It is a diagnostic oracle, never the training-label authority. `GENERATOR_UNDER_TEST` can select a retained baseline for red/green comparisons; the path is resolved in the process cwd.

No tool claims universal induction, model accuracy, natural failure traces, or training approval. Read `NEXT_AGENT.md` before extending the sampler.
