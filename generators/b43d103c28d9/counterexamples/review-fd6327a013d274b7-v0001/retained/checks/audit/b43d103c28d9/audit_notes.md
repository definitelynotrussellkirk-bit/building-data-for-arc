## b43d103c28d9 — accepted interleaving exceeds the sampler's order coverage

**Classification: reproduced distribution ambiguity within the validator's accepted domain; no generated-label error claimed.** Current generator v3.0.0, SHA-256 `9130060c0791667161cb26c103102a26c228f31061e193144d3fd097e3735bfc`. Canonical Racket hash `a2f07dce6b36`, verified against the selected catalog authority. This is a findings-only audit; target source, notes, inherited tests, and review index were not changed.

### Primary finding: the A–B–A schedule leaves a plausible ordering shortcut alive

The canonical rule independently moves each column's nonzero cells upward while preserving their order. A simple competing rule agrees on all current sampled shapes: keep the leading run of the column's first color A, then place every remaining non-A cell, then every returning A cell. This reproduces A*–B* and A*–B*–A* columns, but changes A–B–A–B to A–B–B–A.

The newly authored `group_middle_color` rival matched all four canonical input/output pairs and all 600 current-source sampled inputs: 200 each in easy, medium and hard, seed `2026101900 + sample_index`, indexes 0–199, no overrides. Each difficulty cohort contained 100 canonical histogram, 50 floating histogram and 50 interleaved samples; none had more than three nonzero color runs in a column. Source inspection explains the restriction: both histogram constructors create A*–B* columns; `_draw_interleaved` places one B between the leading A and returning A cells. The four-sample schedule cannot introduce a fourth color run.

The decisive query is an 8×8 grid with contiguous occupied columns 2, 3 and 4. All three contain color 1 at row 1, color 2 at row 3 and color 1 at row 5. Column 3 also contains color 2 at row 7. Its nonzero column sequences are therefore `[1,2,1]`, `[1,2,1,2]`, `[1,2,1]`. Every occupied column starts with the same color, so this does **not** rely on the inherited audit's rejected mixed-first-color construction.

The current `self_check` accepts that query with `[]`. Four actual generated demonstrations using seed `20261019`, hard difficulty and indexes 0–3 all fit the rival. `lesson_identifiable` accepts those four reference-labelled demonstrations and this query with `[]`, although the rival predicts `[1,2,2,1]` in query column 3 and Racket returns `[1,2,1,2]`.

Public `Catalog.apply(reference="canonical", check_generator_domain=True)` executed 34 inputs: 24 cohort samples covering two schedules in each difficulty, all four canonical inputs, the four demonstration inputs, the query, and one scalar-override witness. Every independent stable-pack probe matched its Racket-derived label; the rival disagreed on the query. The selected source and rule hashes are retained in the evidence.

**Suggested next decision:** if `interleaved_columns` is intended to teach general stable order within its presently accepted domain, include A–B–A–B or longer return sequences in the sampler and register a corresponding rival/witness. Narrower intended curriculum scope should be stated explicitly. This is a distribution-coverage finding, not a claim that the current generated labels are wrong or that any finite rival gate establishes universal identifiability.

### Additional observation: integer grid-size overrides are coerced

For seed 17 and sample index 0, `grid_size=14.9` returns a valid 14×14 grid despite the declared axis being integer 8–14. `10.9`, `10.0` and the string `"10"` similarly produce size 10. Integer boundaries 8 and 14 succeed; integers 7 and 15 and both Booleans are rejected. The observable-axis assertion compares the grid against the already-coerced value, so it does not detect the original request/value mismatch.

The 14.9 witness was also executed through the canonical Racket rule. This is scalar-contract hardening, not a semantic label defect: it follows the legacy shared `draw_int` behavior, and the shared documentation makes strict integer draws opt-in. If exact typed overrides are intended for this generator, validate the original scalar or adopt `draw_int_strict`.

### Retained task tests cannot reach execution

The supported `arcpuzzles check b43d103c28d9 --stage task_tests` command exited 1; its result records payload exit 2, `passed: false`, `test_status: "preflight_failed"`, and `test_counts: null`. The failure occurs before pytest. The retained test's fixed `Path(__file__).resolve().parents[1]` root constructs `generators/b43d103c28d9/data/canonical/puzzles.jsonl` inside the staged runtime, where that file does not exist. The tool gives a precise diagnostic at test line 205. The same fixed root also constructs its generator path below the task directory. The canonical helper import uses the legacy `scripts` namespace and receives a warning.

The relevant follow-up is to port these task tests to `reviewer_support.find_root`, `load_selected_generator`, `canonical_pairs`, and `canonical_path`. No inherited tests were edited here, and **no passing or failing executed-test count is claimed** for this preflight failure.

### Evidence and commands

- `checks/audit/b43d103c28d9/probe.py` — standalone, pinned-source reproduction; it writes only within its audit directory.
- `checks/audit/b43d103c28d9/finding.json` — compact findings, query input/reference output/rival, exact demonstration seeds/indexes/overrides, acceptance results, cohort counts and scalar witnesses.
- `checks/audit/b43d103c28d9/racket.json` — complete reference execution results for the 34 inputs, with hashes and rival comparisons.
- `checks/audit/b43d103c28d9/task_tests/result.json` and `RUNTIME_MANIFEST.json` — actual staged-test preflight failure and selected source bindings.
- `checks/audit/b43d103c28d9/commands.json` — exact authoritative check commands, working directories, exit codes, source/test/probe hashes, and result paths.

Both commands below were run from `/workspace/scratch/dec470f4e42e/arc_review/WORK`:

```bash
.venv/bin/python3 run_with_racket.py \
  /workspace/scratch/dec470f4e42e/arc_review/WORK/.venv/bin/python3 \
  -m arcpuzzles check b43d103c28d9 --stage task_tests \
  --out ../checks/audit/b43d103c28d9/task_tests

.venv/bin/python3 run_with_racket.py \
  /workspace/scratch/dec470f4e42e/arc_review/WORK/.venv/bin/python3 \
  ../checks/audit/b43d103c28d9/probe.py
```

The first command exits 1 with preflight failure; the second exits 0 after asserting the reproduced ambiguity and source/rule bindings. The output directory of the first command must be new on a rerun.

### Limits and relation to existing evidence

The existing unresolved audit on this exact source concerns a mixed-first-color grid rejected by the declared domain. Its status was left unchanged. This audit adds a separate accepted-domain witness with a different rival. The 600-input cohort is a finite distribution check against an independent Python probe; only the explicitly listed 34 inputs were run through Racket. The failing query was hand-constructed, not generated. No full battery, private solve inspection, target repair or approval action was performed.
