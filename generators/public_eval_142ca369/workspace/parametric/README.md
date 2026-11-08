# Reflected rays with longest-leg selection

Native hooks: `program(settings)`, `generate(seed,settings,demos,queries)`, `public_turn(episode,index)`. Settings are exactly `{"trace_scope":"all_legs"}` or `{"trace_scope":"longest_leg"}`. Counts: 2–6 demonstrations and independently 1–4 queries; a full lesson requests four. Settings, source indices, programs, future inputs and answers are private.

From the outer packet directory:
```sh
python3 review.py run python3 -m pytest generators/public_eval_142ca369/tests --import-mode=importlib -q
python3 review.py run python3 generators/public_eval_142ca369/workspace/parametric/audit.py --out ../checks/public_eval_142ca369/new-audit --seeds 20
python3 review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_142ca369 --root . --out ../checks/public_eval_142ca369/new-preflight
python3 review.py run python3 generators/public_eval_142ca369/workspace/parametric/audit.py --out ../checks/public_eval_142ca369/new-causal --preflight ../checks/public_eval_142ca369/new-preflight/preflight.json
```
Use new output directories. Python generation makes deterministic label claims; preflight and audit independently execute Racket. After changing Python/Racket or contract files, regenerate preflight and witness. The staged catalog task-test command cannot select a new unregistered public task; use the direct scoped command above before registration.

`reference.rkt` owns all-leg canonical execution. `longest.rkt` adds one selection stage. `model.py` owns independent Python traces and constructive scenes. `audit.py` sweeps API counts, private/public boundaries, executable rivals and current-source witness replay without sibling imports. Keep its `public/` views separate from private audit/witness reports.
