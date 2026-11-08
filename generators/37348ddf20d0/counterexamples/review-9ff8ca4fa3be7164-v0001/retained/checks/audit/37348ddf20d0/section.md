## 37348ddf20d0

**Classification: reproduced defect.** Two findings remain open on generator version `3.0.0`, SHA-256 `222bb3faed0e93a1ef53073874042a3e63e7e150fff1b49564f0735996448ba6`. The selected canonical Racket rule was executed with rule hash `6d8410c29906` and rule-text SHA-256 `18209fc40960fbfd6d366caa211d46cdc92dfe160310da6f4c388df89c34a194`. No audited source, rule, or test was edited.

### A1 — Ordered production lesson admits a canonical-fitting distance shortcut

**Priority: high; reproduced teaching defect.** The rival respects color-5 walls when finding connected components, then compares the nearest red and green seeds by Manhattan distance inside each component. It preserves seeds/walls and leaves ties and seedless components black. This is a plausible simplification of wall-aware shortest-path distance: it agrees on rectangular chambers but can ignore a detour inside a connected chamber.

The rival matches **all five canonical pairs** after replay through the actual selected Racket rule. It also matches every demonstration in the ordinary production lesson `seed=16`, `difficulty="easy"`, `sample_index=0`, `n_train=5`, `n_test=1`, with no overrides. Accepted sample indices are exactly `0,1,2,3,4,5`, with **zero rejected draws**. The profile order is `wall_detour`, `tie_rooms`, `seedless_rooms`, `mixed_rooms`, `open_voronoi`, followed by the `wall_detour` query.

All five demonstrations fit the rival, but the query differs at six cells. For example, at zero-based `(row=1, col=3)`, the canonical Racket output is red `2` and the rival predicts green `3`. The other five differences are red `2` versus black `0`. The full cell list and grids are retained in the JSON evidence.

This case requires **no query rotation or nonconsecutive assembly**. The public `Catalog.generate` production materializer reproduced all six retained pairs exactly and reported `lesson_check.status="passed_declared_hook"`. All six inputs pass `self_check`, and `lesson_identifiable()` returns `[]`.

**Cause.** `_build_wall_detour` places a detour-shaped wall and randomized seeds but does not ensure that the example distinguishes path distance from component-restricted Manhattan distance. `_observe_texture` recognizes topology rather than this semantic distinction. The declared `ignore_walls_manhattan` rival is weaker: complete-wall examples can refute it even when the detour demonstration provides no evidence about distances within a connected chamber. Thus cycling through all five profile names is insufficient for this lesson.

**Recommended follow-up.** Add the component-restricted rival to the executable teaching contract and retain this exact ordered lesson as a regression. Ensure the scheduled detour demonstration actually refutes it, constructively or with bounded rejection that preserves the lesson's coverage. The canonical Racket rule itself does not need a change based on this evidence.

**Evidence files, relative to `WORK/`:**

- `checks/audit/37348ddf20d0/adversarial_probe.py` — reusable source-pinned adversarial solver and candidate search; Python mirroring only screens candidates, and every retained semantic verdict uses actual Racket labels.
- `checks/audit/37348ddf20d0/probe.json` — five canonical pairs and six generated pairs labeled by canonical Racket; all rival outputs, query differences, hook result, source/rule hashes, and scalar cases.
- `checks/audit/37348ddf20d0/production_replay.py` — independently replays the retained candidate through the public production materializer.
- `checks/audit/37348ddf20d0/production.json` — complete production episode, accepted indices, no-rejection receipt, declared gate result, and exact equality with the retained lesson.

### A2 — Exact integer controls silently accept and coerce invalid types

**Priority: medium; reproduced request-contract defect.** The exact integer axes call `ctx.draw_int`, which uses `int(value)`, while `_validate_call` only checks difficulty and unknown keys. Examples at `seed=1, sample_index=0` include `grid_h=11.75` producing height `11`, `grid_w=12.75` producing width `12`, `n_red=2.75` producing two red seeds, and `n_red=True` producing one red seed. Integer-looking strings are also accepted. The generated grids pass the task's self-check, which discards the supplied metadata.

Direct `generate()` also accepts Boolean, float, and string seed/index values and a negative sample index. These seed/index findings concern the generator entry point: the public `Catalog.generate` wrapper separately validates its explicit seed and sample-index parameters. No equivalent strict override validation is present in this generator. Thirteen concrete accepted calls and their observed axes are retained in `probe.json` under `scalar_cases`; they are not semantic label failures.

**Recommended follow-up.** Validate literal Python integers for seed/index and advertised integer axes before conversion; retain `None` only where the existing no-override convention intends it. Reject negative sample indices. Cover fractional, Boolean, and string controls in the task-local regression suite.

### Commands and limits

Both commands ran from the extracted packet root `/workspace/scratch/a33c88b1b147/arc_review`; `review.py run` executed their payloads inside `WORK/repo`. Both exited **0**, meaning the audit/reproduction completed, not that the audited generator passed the new adversarial checks.

```sh
python3 review.py run ../.venv/bin/python ../checks/audit/37348ddf20d0/adversarial_probe.py --root . --search-limit 500 --out ../checks/audit/37348ddf20d0/probe.json
python3 review.py run ../.venv/bin/python ../checks/audit/37348ddf20d0/production_replay.py --root . --candidate ../checks/audit/37348ddf20d0/probe.json --out ../checks/audit/37348ddf20d0/production.json
```

Exact command, working-directory, elapsed-time, return-code, and log records are `checks/audit/37348ddf20d0/command-search.json` and `checks/audit/37348ddf20d0/command-production.json`; console output is retained in `probe.log` and `production.log` in the same directory.

The search stopped at the fourth tested detour pair, on the first band (`easy`); it is a concrete counterexample, **not an ambiguity-rate estimate or a completed 500-case census**. Racket replay verified all five canonical pairs and six generated pairs, and the production replay separately verified the six-pair episode. No wrong canonical label was found in that scope. The existing focused tests, notes, and current review index were read; no unnecessary full battery was run. This audit does not establish universal identifiability, change approval, or admit any data to training.
