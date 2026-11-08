# Public control and contract probe

`probe_controls.py` is a bounded task-local probe. It calls the current
generator's public `generate`, `self_check`, and `observe_overrides` hooks and
the public `GenCtx` provenance methods. It never executes a reference rule or
reads canonical pairs or solve records. It compiles the exact generator bytes
whose SHA-256 it records, even if another process edits the source afterward.

Use explicit cases so a retired control, a legal control, and an incompatible
combination have deliberately chosen expectations. No list of task axis names
is built into the probe. The generated report introspects the current exports
and hook signatures, and records the complete generated inputs, requested
controls, consumed controls, keyed draws, observations, validation results,
replay failures, source hash, command, and working directory.

## Reproduction from the packet root

The original generator was tested with this command (exit 1):

```sh
python3 run_with_racket.py python3 generators/b86607f34b8b/workspace/contract_review/probe_controls.py --case '{"grid_h":5}' --case '{"grid_w":7}' --case '{"n_markers":5}' --case '{"palette_kind":"warm"}' --out ../checks/contract-review/baseline-controls.json
```

The wrapper's effective working directory was the packet's `repo/`. The
generator SHA-256 was
`b8a16c7f1a55a2b04fc789c2751b306fa654d563cf6a3d36db8f01094221847f`.
The report retains 18 draws (6 cases in each difficulty band) and 24 findings.
At seed 17, sample index 3, easy, `grid_h=5` returned an 8-row grid without
consuming that override. `grid_w=7` raised even though 7 belonged to the declared
domain. `n_markers=5` and `palette_kind="warm"` were accepted without consuming
them. The unknown-key case was accepted in all three bands. This was a focused
reproduction; the full battery measures additional faults.

For a repair with exact `grid_h`, `grid_w`, and `n_colors` controls, for example:

```sh
python3 run_with_racket.py python3 generators/b86607f34b8b/workspace/contract_review/probe_controls.py --case '{"grid_h":9,"grid_w":9,"n_colors":3}' --case '{"grid_h":14,"grid_w":14,"n_colors":5}' --reject-case '{"palette_kind":"warm"}' --out ../checks/contract-review/repaired-controls.json
```

Use a new output filename for every run. `--sample-index 0` and
`--sample-index 1` can test distinct scheduled default branches separately.
The probe's default seed is 17, default sample index is 3, and default bands
are easy, medium, and hard. Every run also checks the default draw and a
deliberately unknown key, then checks five simple malformed inputs against
`self_check`.

## Implemented shared contracts checked during this review

The authoritative implementations are `shared/tools/check_generator_override_contract.py`,
`shared/tools/generator_semantic_gate.py`, `shared/tools/lesson_census.py`, and
`shared/runtime/puzzle_generators/base.py`. The semantic gate mentions a
`docs/SEMANTIC_GATE_CONTRACT.md` file that is absent from this packet; the
implemented declarations and shared regression tests were used instead.

| API | Actual contract |
| --- | --- |
| `AXES` | Mapping from axis name to a `type`/`default`/`valid` specification. Finite integer ranges and pipe-separated enumerations are understood by the shared parser. Fixed string singleton axes produce warnings. |
| `observe_overrides(grid)` | Returns realized values in a dictionary. Exact multi-valued integer, color, and boolean axes require observable values. Dimensions are measured directly. |
| `GenCtx.recorded_draws()` / `overrides_used()` | Public copies of keyed values and consumed overrides. `axis_value`, `draw_bounds`, and `draw_options` are also public. Default draws must match realized exact values. |
| `INCOMPATIBLE_OVERRIDE_COMBINATIONS` | Sequence of mappings or axis-name collections; mapping value `None` is a wildcard. `[]` means no refusal is claimed. Structured `ValueError.incompatible_axes` can identify a value-dependent conflict. An advertised single-axis value must be accepted. |
| `strict_canonical_like(grid)` | Empty reason list or `True` means lawful; reasons or `False` mean rejection. |
| `SEMANTIC_WITNESSES` | Dictionary of named `grid -> bool` predicates. `BRANCH_WITNESSES` lists positive-coverage witnesses. |
| `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, `CANONICAL_SHORTCUTS` | Each is a dictionary of named pure, deterministic `grid -> grid` callables. |
| `WITNESS_RIVALS` | Maps an existing witness name to nonempty existing semantic-rival names. Every firing claims that at least one named rival differs from authority on that input. |
| `lesson_identifiable(demos, query)` | Demonstrations are labeled pair dictionaries and query is a full labeled pair dictionary. Return a list of string reasons; an empty list indicates no reported problem. |
| `schedule_profile(seed, sample_index, difficulty=None)` | Returns a hashable profile. Optional `SCHEDULE_PROFILES` enumerates the claimed schedule space. |

The public census controller is
`arcpuzzles.lesson_census.lesson_census(catalog, task_id, ...)`; it is not a
top-level `arcpuzzles` export. Its worker collects actual declarations from all
three rival dictionaries and retains their namespaces. Its lesson shape is
`{"train": [pair, ...], "test": [pair, ...]}`, unlike the older semantic
gate's internal `demos`/`query` helper. A rival fitting demonstrations but
disagreeing on a query is `ambiguous`; agreement on all pairs is `survived_all`.
`--rotate-query` holds out each labeled pair once, including the original query,
and requires a single query. `--period` changes reporting, not sampling.

## Limits

This probe does not infer compatible domains or reproduce the shared Cartesian
matrix. Its positive cases must have been reviewed as legal, and rejection
cases are expected to raise `ValueError`, `TypeError`, or `KeyError`. It checks
consumption of every supplied control, making that requirement explicit even
where an older shared checker might be permissive. It does not prove a
validator accepts every lawful input, establish semantic authority, execute
declared rivals, or make a lesson-identifiability claim. Use the required
after battery, focused task tests, and source-bound shared lesson census for
those separate questions.
