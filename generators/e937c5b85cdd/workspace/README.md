# Reusable review probes — e937c5b85cdd

The selected implementation is `../generator.py`. Workspace drafts and historical snapshots are never automatically selected. Both current probes discover the actual live `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS` rather than hard-coding two known names. The cycle probe merges in that order; the rescorer deduplicates identical aliases and rejects conflicting implementations with one name. The historical `rival-analysis/` folder is pinned to the baseline and records the original investigation.

## Exhaustive starts of the four-draw teaching cycle

From the full packet root, after `python3 setup_racket.py`:

```bash
python3 run_with_racket.py python3 generators/e937c5b85cdd/workspace/probe_lessons.py --out ../checks/cycles-new.json
```

The default uses seeds 0–11, three bands, indices 0–6, all four cyclic starts, and each possible single query holdout. It labels unique inputs through public `Catalog.apply`, keeps full grids/outputs, rule and generator hashes, seed/index identities, canonical fit, declaration names, failures, and an exact-override control. `--seeds 1` is a smaller smoke run. A fresh output path is required.

The full final review measured 252 draws, 164 unique labelled inputs including the control, 144 overlapping windows, and 576 query rotations. Counts of windows are not counts of independent inputs. The claimed assembly is three demonstrations plus one query from four consecutive ordinary draws; arbitrary overrides, rejected indices or multiple query holdouts need a separate probe.

## Rescore saved authority labels with current rivals

First obtain a complete production census using the shared command:

```bash
python3 run_with_racket.py python3 -m arcpuzzles lesson-census e937c5b85cdd --per-band 100 --rotate-query --period 4 --timeout 1800 --out ../checks/census-new.json
```

After adding or improving a rival, reuse those same labelled inputs:

```bash
python3 run_with_racket.py python3 generators/e937c5b85cdd/workspace/rescore_census.py --census ../checks/census-new.json --out ../checks/rescore-new.json
```

Rescoring does not regenerate inputs or execute Racket. It distinguishes the census input-generator SHA from the live rival-source SHA, binds the census bytes and rule, records exact differing query identities, and keeps scoring errors separate from ambiguity. The cycle probe separately verifies canonical fit. Use only complete source-bound evidence; incomplete, empty, errored or mismatched censuses cannot support a clean verdict. A zero result only concerns the current finite set of declared rivals.

This tool found 25 production ambiguities and 141 ambiguous query rotations in the retained 300-lesson census of the first two-rival candidate. The final source's same-size census has zero. Old and final labels remain separate so these results cannot be mistaken for a resampling improvement.

The companion validation probe checks 20 compact in-memory mutations of retained evidence plus both real controls:

```bash
python3 run_with_racket.py python3 generators/e937c5b85cdd/workspace/validate_rescore_census.py --tool generators/e937c5b85cdd/workspace/rescore_census.py --old ../checks/lesson-census.json --final ../checks/final-lesson-census.json --expect guarded --out ../checks/rescore-guards-new.json
```

It uses the named old/final review censuses as data, not as executable source. All 20 invalid cases must produce an error verdict and nonzero exit status, while the old control remains ambiguous and the final control remains clean. This checks internal evidence bindings and grid structure; it does not independently certify the retained reference labels.

## Task regressions

From the packet root with pytest installed in the selected Python environment:

```bash
python3 run_with_racket.py python3 -m pytest --import-mode=importlib -q generators/e937c5b85cdd/tests
```

For the supported portable-layout check:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check e937c5b85cdd --stage task_tests --phase after --timeout 600 --out ../checks/task-tests-new
```

The staged runner may execute source-equivalent legacy fixture tests twice; report unique tests separately from total JUnit executions. The task tests use `reviewer_support.find_root` and `canonical_pairs`, so no fixed parent-depth guess is needed.

All authoring helpers expose reference answers. Keep them closed during visible-only solve episodes. The return ZIP preserves the actual review commands, failed iterations, frozen solve notes, and source hashes in its top-level reports and `checks/` evidence.
