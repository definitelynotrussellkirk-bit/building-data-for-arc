## 07dbda8c31c9

**Findings-only audit: two reproduced implementation/test defects and one reproduced production-lesson ambiguity. Target sources, tests, notes, shared files, and rule authority were left unchanged.**

All results below bind to generator SHA-256 `620ecc1e508e2511a32b2abd5746f50be9cab10d619660e7a5308e205329e31a`, version `4.0.0`, and executed canonical rule hash `bd0e3c33843a`. The raw canonical rule SHA-256 is `fc218eea07b991a743ab08983d4144d5da984cd8102cf91dc1518f8091c13b47`; the executed callable SHA-256 is `9302808e746e581af7704f597ca3e6ffb3596ec87b83a1255f6491588f737d1d`. These are distinct representations, both retained. The task had no `evidence/review_index.json`; its working notes and catalog-associated decisions were inspected.

### A07-1: Reproduced production lesson ambiguity under an additional width shortcut

The actual public materializer, with seed `17`, difficulty `easy`, sample start `0`, three demonstrations and one query, accepts indices `0,1,2,3` with zero rejections. The three demonstration input widths are `6,5,6`, and their Racket output widths are also `6,5,6`. Therefore the rival `[[2] * input_width]` fits every demonstration. The query has width `5` but only three red cells: its actual Racket output is `[[2,2,2]]`, whereas the rival returns `[[2,2,2,2,2]]`.

All four inputs are distinct, pass the target validator, and match an independently retained `arcpuzzles apply` receipt exactly. Query input SHA-256: `641f7331f3e455777a16ea686cd13edef6aefb139263c5060b62f64516550a70`. This is generated production support, not a validator-only construction. The production receipt reports `lesson_check.status: not_declared` and no rival contract.

Evidence: `checks/audit/07dbda8c31c9/production-witness.jsonl`, `verdict.json` under `production_witness`, and `racket.json` results `23..26`. The materialized episode SHA-256 is `5593d612f90fb77b0e792a07e308581c2791607299b6af45dc955e6381910b5e`. Suggested follow-up: declare the width rival and require a distinguishing demonstration when the query depends on cell count differing from input width. The two shortcuts already discussed in the source are refuted here; they do not exhaust plausible rivals.

### A07-2: Reproduced integer-axis coercion

All **36/36** tested invalid integer overrides were accepted: `grid_h` and `grid_w` values `4.0`, `4.75`, `"4"`, and `n_red` values `5.0`, `5.75`, `"5"`, each at seed `991`, sample index `0`, and difficulty `None/easy/medium/hard`. `_choose_axes` calls `int(...)`, and `_record_exact_int` uses the coercing integer helper.

For example, `generate(991, 0, difficulty=None, n_red=5.75)` returns a validator-accepted `10x17` grid with exactly five red cells, rather than rejecting the fractional request. Its input SHA-256 is `c9b9d286487302c986241aa5e338b2f9f7a2c7bcdfe4ec23707c3b0208f12ccf`; Racket result `52` confirms a five-cell red bar. This is an API/type contract defect, not a wrong Racket label. Evidence: `prepared.json` under `invalid_integer_overrides` and `racket.json`. Suggested follow-up: reject non-integer concrete axis values before conversion, preserving the documented `None` sentinel.

### A07-3: Reproduced portable task-test failure

The sole selected check stage, `task_tests --phase audit`, fails before pytest because `tests/test_generator_07dbda8c31c9.py:18` reads a missing task-relative `data/canonical/puzzles.jsonl` after defining `ROOT = Path(__file__).resolve().parents[1]`. Prerequisite checks passed. Public command exit: `1`; retained internal stage exit: `2`; `test_status: preflight_failed`; test counts remain unknown and no tests executed. Evidence: `task-tests/result.json` and its retained runtime manifest. Suggested follow-up: use `reviewer_support.find_root`, `canonical_path`/`canonical_pairs`, and the supported selected-generator loader.

### Bounded checks and limits

The supported Racket apply command labelled **53/53 unique retained inputs** correctly as red-cell counts, and all 53 passed its generator-domain check: five canonical inputs; 36 ordinary draws from seeds `0,17`, indices `0..5`, and `easy/medium/hard`; nine exact single-axis boundary/profile probes at seed `701`, indices `0..8`, difficulty `medium`; and three representative accepted-invalid-scalar inputs. All **9/9** boundary requests were exact, including width `30` and red count `28`.

Both named canonical shortcuts, count-all-nonzero and count-red-components, fit **5/5** canonical examples. Across **18** consecutive three-demo/one-query windows from those ordinary draws (two seeds, three bands, starts `0..2`), those two shortcuts were refuted, but the additional width rival caused **1/18** ordered ambiguities. Across all four holdouts per window, **25/72** rotations were ambiguous. These rotations overlap the ordered windows and are not independent samples. Four explicit rivals were checked; this is not an all-seed or all-hypothesis claim. Only the exact width witness was additionally materialized through public production generation.

`probe.py` reproduces preparation, Racket-receipt scoring, and production-witness verification. Exact commands, environments, exit statuses, and evidence paths are in `commands.json`. A genuine first scoring-probe failure caused by confusing raw-source and callable hash fields is retained in `score-failure.json`; it was corrected without changing target source or Racket evidence.
