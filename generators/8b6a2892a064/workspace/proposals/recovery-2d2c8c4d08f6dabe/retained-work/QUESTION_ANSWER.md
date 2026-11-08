# Qwen3.5-9B data-value question

**Question:** Based on your generator review, what one additional automated gate would most improve Qwen3.5-9B training data quality? Name a reproducible failure it would catch, a possible false positive, and the cheapest way to test it.

## Proposed admission requirement: nonvacuous demonstration-consistent rivals for every query

The current worker already checks declared rivals and rejects failures under automatic demonstration policy; explicit-count diagnostic routes can retain findings, and a missing contract reports not_declared. Require a meaningful executable task contract at admission, and reuse those checks across all routes. Before admitting an episode, compute the declared nearby rival rules that agree with every demonstration. Freeze that set. For each query, quarantine the episode if a surviving rival disagrees with the executed rule. Retain per-query outcomes, refuting demonstration indices, and source/input hashes. Labels must come from matching Racket; this is an additional teaching gate, not a label oracle. Query answers must never influence which rivals survived the demonstrations.

This is an admission proposal, not a measured Qwen3.5-9B improvement. The repaired generator exposes four rivals, a task-local gate makes the check runnable, and the separate six-setting prototype already filters its five alternative settings before query evaluation.

## Reproducible failure

Final generator SHA-256: 17a221e4e5ccc47d3cfa15f0cb54b55f4b09ad3b31f7401a7e80a20bc89553e4.
The completed 300-lesson census Racket-labeled all 1,200 pairs. Two raw materialized lessons were ambiguous, as were three of 1,200 query rotations. At easy seed 3165630413, sample index 90, three demonstrations fail to distinguish the true rule from skip_short_lines (rotate only lines of length at least five), but the query distinguishes them. Another occurs at hard seed 3985080662, index 80.

The exact first episode and rival outputs are in checks/ambiguous-canonical-lesson.json. The complete census is checks/lesson-census-retry.json.gz, with restoration metadata in checks/EVIDENCE-COMPRESSION.json; its readable summary is checks/lesson-census-brief.json. The 12-stage after battery passed, so a small smoke test missed this lesson-level defect.

## Possible false positive

Arbitrarily complex rivals can fit any finite demonstration set. Requiring their elimination could reject useful examples or force repetitive scenes. An intentionally ordered curriculum also need not support every query rotation. Limit the gate to reviewed nearby alternatives, state the ordering policy, and retain the named disagreement for review. The result concerns four declared rivals and six prototype settings, not all possible programs.

## Cheapest useful test

Replay the retained counterexample first: the local gate should reject it and name skip_short_lines, while the retained four-query production episode should pass. This needs already retained Racket labels and a few small Python rival evaluations, not a corpus rerun or model job. Then reuse the bounded 100-lessons-per-band census, separating execution errors from semantic failures. Before claiming a Qwen quality gain, compare matched task-family and duplicate-rate slices at a fixed token budget.
