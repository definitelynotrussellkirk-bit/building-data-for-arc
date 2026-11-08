# Current notes: 5000bcb83fa9

## Intended rule and authority

For each maximal nonzero horizontal run of odd length, erase every run cell except its unique center. Preserve the center color and position; background is 0. The selected Racket authority was **not changed**. Generator version `3.0.0` pins `RULE_HASH = "2b45ada2fe3e"`.

Final generator SHA-256 used for the current after checks: `147ccd0e4a3b449adb2c59ac663083715b1dee85ad1d9009e3a76177ea06b7aa`.

## Repair trigger and prior evidence

The selected baseline was version `2.0.1`, SHA-256 `315ef6154f31cfb7f4649201cdef0bfc5c427c0f520d081fb5aab79744c75d0c`. I used unresolved audit `review-5f5dffd562b3002e:v0001` as a lead and independently reproduced its two defects:

1. `generate(0, 0, difficulty="easy", run_count=5)` contradicted the advertised `run_count` domain by raising.
2. `self_check` accepted a length-2 run whenever another odd run appeared later, because it stopped at the first odd run.

Baseline probing additionally found six advertised axes that were inert or unobservable, unknown overrides silently accepted, negative textures treated as ordinary generation controls, all-singleton identity scenes, and no executable semantic/lesson contract. The initial focused test run intentionally recorded **31 failures / 12 passes** before source changes.

## Current sampler contract

The public exact axes are deliberately limited to four recoverable controls:

- `grid_h`: integer 5..9
- `grid_w`: integer 9..13
- `run_count`: integer 3..5
- `singleton_count`: integer 0..2

All Cartesian combinations are constructive in every difficulty band. Unknown keys, bools, floats, strings, and out-of-range values fail loudly. Each generated scene has one run per occupied row, distinct nonzero colors, lengths only in `{1,3,5}`, at most two singletons, and at least one non-singleton, so every ordinary input is nonidentity.

Defaults cycle through canonical shapes `(6,10)`, `(7,9)`, `(5,11)`, always with four runs, one singleton, and four run colors plus background. Difficulty affects long-run length evidence: easy uses length 3, hard uses length 5, and medium/default alternates 3 and 5. Layout rows, starts, color assignments, and ordering remain keyed-random and deterministic.

## Validation and teaching contract

`self_check` now validates shape, ARC integer cells, dimensions, run count, exact odd lengths, singleton count, nonidentity, one run per row, and one run per color. `observe_overrides` recovers every public control. `strict_canonical_like` requires the exact profile shared by all four canonical inputs.

The diagnostic Python mirror is checked against the selected Racket authority. Declared rivals are `left_endpoint`, `right_endpoint`, and `keep_singletons_only`; every default input contains a nontrivial odd run that refutes all three. `lesson_identifiable` screens the actual demonstrations and query against those finite rivals. This is not a proof against every possible program.

## Focused regressions and evidence

`tests/test_generator.py` is a portable 43-test suite covering:

- the pinned rule and all four canonical pairs;
- both historical counterexamples;
- exact-control corner combinations in every band;
- strict type/range/unknown-key rejection;
- deterministic canonical-profile defaults with positional/color/length diversity;
- malformed and out-of-manifold validator cases;
- witness/rival and all-query-rotation lesson checks.

The final source passed **43/43** locally and **43/43** in the source-bound `task_tests` stage. Final battery receipts are under `checks/after/`; see `REVIEW.md` and `RESULTS.json` for the aggregate verdict and exact commands.

## Deliberate limits and open questions

The sampler is narrower than the full mathematical Racket domain: it fixes background 0, samples only lengths 1/3/5, uses 3..5 runs, places at most one run on a row, and requires distinct run colors. `self_check` intentionally validates this sampled training manifold rather than every input on which the Racket program could produce an answer. The finite rival set covers elementary endpoint/singleton shortcuts only; undeclared hypotheses remain unknown.
## Current reviewer considerations

Source SHA-256: `147ccd0e4a3b449adb2c59ac663083715b1dee85ad1d9009e3a76177ea06b7aa`.

# Repair decisions — 5000bcb83fa9

## D1 — Replace nine advertised axes with four honest exact controls

**Prior choice:** version 2.0.1 advertised grid dimensions, palette kind/size, run count, position bias, distinct-color count, density, and texture. Only dimensions and run count materially affected normal generation; several values were unobservable, and difficulty silently narrowed the supposedly valid ranges.

**Decision:** retain only `grid_h`, `grid_w`, `run_count`, and a new directly observable `singleton_count`. Every value in every declared range is constructive in every band, and `observe_overrides` recovers all four.

**Alternatives rejected:**

- Implement all legacy palette/texture aliases. This would add conditioning surface without changing the rule evidence and would preserve ambiguity about whether palette size includes background.
- Keep degenerate textures as ordinary exact controls. `no_runs`, `all_singletons`, and `even_length_runs` violate the sampled manifold or produce identity scenes; they belong in tests/negative fixtures, not the training sampler.
- Merely widen each difficulty-specific draw. That would close the historical `run_count=5` symptom but leave inert axes, silent typos, and unobservable interventions.

**Evidence:** initial source-bound override/profile probes under `checks/before*`; historical audit in `generators/5000bcb83fa9/evidence/review_index.json`; focused regressions in `generators/5000bcb83fa9/tests/test_generator.py`.

## D2 — Use constructive one-run-per-row placement

**Prior choice:** random rejection placement tried up to 300 times per color and could silently emit fewer runs.

**Decision:** sample distinct rows once, assign one requested run to each row, and choose its start directly. This makes all exact combinations total, removes retry-dependent under-realization, and makes run count and singleton count trivially observable.

**Alternative rejected:** retain multiple runs per row with buffer packing. That expands the layout domain but requires a capacity solver and creates touching/different-color segmentation edge cases unrelated to the canonical examples. The narrower manifold is explicit instead of pretending to support a broader one.

**Failure mode retained as a limit:** the sampler does not train multiple same-row runs or repeated colors; the selected Racket rule may still be meaningful there.

## D3 — Bind defaults to canonical profiles in every band

**Decision:** cycle `(6,10)`, `(7,9)`, and `(5,11)` at sample-index period three, with four runs, one singleton, and four nonzero colors. This guarantees profile-floor support instead of hoping random dimensions/palette counts collide with a canonical profile.

**Difficulty role:** easy presents length-3 long runs, hard presents length-5 long runs, and medium/default alternates both. Difficulty no longer changes legal override bounds.

**Alternative rejected:** broad random dimensions by default. The baseline measured only 3/60 exact-profile hits and 10/60 envelope hits, with no medium/hard exact profile support. Broad dimensions remain available through exact overrides.

## D4 — Make `self_check` a sampled-manifold validator

**Prior choice:** return success after finding any odd run, ignoring even runs and most declared invariants.

**Decision:** collect independent errors for malformed cells/shape, out-of-domain dimensions, run count, illegal/even run lengths, too many singletons, all-singleton identity, repeated rows, and repeated colors. Canonical inputs and every generated exact combination must pass.

**Alternative rejected:** validate the full Racket domain. The generator cannot claim exhaustive knowledge of every lawful authority input; a strict sampler validator is more honest and supports mutation sensitivity and exact-control observation.

**Known tradeoff:** some Racket-lawful grids outside the sampled manifold are rejected. This is intentional and documented.

## D5 — Add executable semantic and lesson contracts

**Decision:** pin rule hash `2b45ada2fe3e`, add a Python mirror, declare three plausible elementary rivals (`left_endpoint`, `right_endpoint`, `keep_singletons_only`), require a nontrivial odd-run witness, and screen complete lessons with `lesson_identifiable`.

**Alternative rejected:** descriptive comments only. They cannot be scored by the semantic gate and do not prove that generated examples distinguish the intended center operation.

**Limit:** finite rivals are not universal induction. No canonical-fitting shortcut was found among the declared rivals, so no larger 100-per-band census was required solely by the assignment rule; query rotations are nevertheless required in the after semantic smoke and exhaustively exercised by the task tests.

## D6 — Preserve authority, change only the sampler

The selected Racket rule and canonical data were left untouched. Rule smoke and all four canonical pairs are the authority checks; the Python mirror is diagnostic only. Any mismatch would have blocked acceptance rather than being “fixed” by changing expected outputs.

## D7 — Tests are the reusable future-agent tool

Rather than add another task-specific command wrapper, the repair includes a portable 43-test qualification suite. It runs against a staged source via `GENERATOR_UNDER_TEST`, uses `reviewer_support` to locate canonical data, and encodes the historical failures, exact-axis corners, distribution invariants, and teaching rivals. Future agents can replay it directly or through the source-bound `task_tests` stage.
