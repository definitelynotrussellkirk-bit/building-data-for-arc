## d3633a9fb1cd

**Classification: domain question / reproduced arbitrary-query-rotation hole, not a wrong-label defect under the documented ordered policy.** Audited generator SHA-256: `9f4712ba17e90e8418b30ad432ae12825229bc0d23dc52f639a90e12b1355b5f`.

A fresh source-bound census materialized 100 lessons in each band (300 total, three demonstrations plus one query). The ordered production lessons had **0/300** declared-rival ambiguities, no materialization/scoring errors, and 1,200 unique inputs. Holding out every pair once produced **121/1,200 ambiguous rotations**: easy 60/400, medium 47/400, hard 14/400. Compact counts and source binding are in `checks/audit/d3633a9fb1cd/census-compact.json`.

The exact fresh reproducer uses easy seed `3226059948`, sample indices `[1,2,3,4]`, and rotates sample index `3` (pair position 2) into the query. With samples 1, 2, and 4 as demonstrations, both declared competitors `component_manhattan` and `tie_break_low_color` match all three demonstrations and differ from the live Racket-labelled query. The ordinary ordered query at sample 4 is not ambiguous. Exact grids, outputs, rival predictions, rule hash, and assertions are in `checks/audit/d3633a9fb1cd/rotation-report.json`; runnable probe: `checks/audit/d3633a9fb1cd/reproduce_rotation.py`.

This is actionable only if downstream assembly permits arbitrary query rotation. Under the task’s stated deterministic ordered curriculum, I did not reproduce a production defect, invalid label, override failure, or authority mismatch. No audited target file was modified.
