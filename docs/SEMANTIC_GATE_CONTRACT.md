# Semantic gate contract

This is the current authoring contract implemented by
[`generator_semantic_gate.py`](../shared/tools/generator_semantic_gate.py).
Declare hooks in `generators/<id>/generator.py`. They describe task semantics;
successful generation, marginal similarity, and finite rival checks alone do not
prove that a lesson identifies the intended rule.

Use `arcpuzzles check TASK_ID --stage semantic_gate` for a retained baseline
check. The source under `shared/tools/` requires the copied runtime layout;
inside that layout its entry point is `python3 scripts/generator_semantic_gate.py
TASK_ID`. See [shared tools](../shared/README.md) for staging and the optional
`arcpuzzles lesson-census` command. These checks do not grant approval or admit
training data.

## Core hooks

Grids are integer row lists. A labeled pair is
`{"input": grid, "output": grid}`. Hooks receive deep copies of their arguments.
Keep hooks and rivals deterministic and free of external state.

| Declaration | Contract and meaning |
|---|---|
| `strict_canonical_like(grid)` | Return `[]` or `True` for an input on this task's canonical manifold; return short reasons or `False` otherwise. The gate first checks acceptance of canonical inputs, then measures generated support. |
| `SEMANTIC_WITNESSES = {name: predicate}` | Each predicate receives an input grid and reports whether a named semantic feature or branch is present. Return a boolean. Zero pooled firings fail; band gaps are judged against the observed firing rate. |
| `lesson_identifiable(demos, query)` | `demos` is a list of labeled pairs; `query` is one labeled pair. Return `[]` when the demonstrations determine the query answer, otherwise short reasons. Do not return a boolean. |

Use lists of strings for reasons. For compatibility, the semantic gate also
accepts tuples and stringifies their members; the separate lesson census requires
string members. The strict hook dispatches booleans by type: `False` rejects and
`[]` accepts. Witness results are currently converted with `bool(...)`; authors
should return actual booleans. Exceptions and invalid hook return types are
reported as errors.

`MIN_STRICT_FRAC`, when declared as a number in `[0, 1]`, overrides the CLI
strict-support floor (default `0.05`). Zero measured support is a failure;
nonzero support below the floor is a warning. Invalid declarations warn and
fall back to the CLI value.

## v1.1: rivals, counterexamples, and schedules

These optional declarations extend the original three hooks.

| Declaration | Contract and meaning |
|---|---|
| `SEMANTIC_RIVALS = {name: solve}` | Named alternative rules; each `solve(grid)` returns an output grid. Used to verify witness counterexample claims. |
| `WITNESS_RIVALS = {witness: [rival, ...]}` | On every checked input where that witness fires, at least one named rival must disagree with the canonical Racket output. Names must exist in the corresponding declarations. A single rival string is accepted as shorthand. |
| `LESSON_COMPETITORS = {name: solve}` | Score alternatives on whole lessons. Fitting all demonstrations and changing the query answer is ambiguity. Agreeing on demonstrations and query is `survived_all`, not evidence of an ambiguous query. |
| `CANONICAL_SHORTCUTS = {name: solve}` | Assert that each rule fits **every usable labeled canonical pair**, across all task variants and both splits. A disagreement, execution error or unavailable labeled population fails the declaration. A fitting shortcut needs generated counterexample evidence. These are also scored as lesson competitors; an explicit `LESSON_COMPETITORS` entry of the same name takes precedence. |
| `schedule_profile(seed, sample_index, difficulty=None)` | Return a hashable branch/profile identifier for the draw schedule. |
| `SCHEDULE_PROFILES` | Optional list, tuple, set, or frozenset enumerating the declared profile space. Requires `schedule_profile`; unvisited declared profiles warn. |

Use string names and callable values in the rule dictionaries. A witness claim
refers specifically to `SEMANTIC_RIVALS`, not to another declaration namespace.
A matching shortcut name connects canonical ambiguity to its counterexample
witness. The gate bounds checked firings, so passing is sampled evidence, not
proof over every input. An unsatisfied declared canonical shortcut warns; generic
shortcut matches are notes unless `--require-shortcut-counterexample` is set.
The gate also recognizes certain exact simple selected rules as answer-equivalent
shortcuts and reports that exemption explicitly.

`canonical_ambiguity.declared_validation` reports each declaration's checked,
mismatch and exception totals, plus bounded examples carrying zero-based
canonical row, task variant, split and pair indexes. All labeled pairs are
checked even after an earlier mismatch. Unlabeled query outputs are excluded;
their inputs remain in the profile reader. Generic identity/dihedral nonmatches
are ordinary eliminations and do not create declaration failures.
Partial heuristics belong in `LESSON_COMPETITORS`; no partial-scope exemption
for `CANONICAL_SHORTCUTS` is currently supported. A same-name lesson competitor
does not excuse a false canonical-fitting declaration.

`BRANCH_WITNESSES` is a later extension: a collection of witness names declared
as positive branch coverage, without a rival-refutation claim. These are reported
as branch coverage. Other witnesses without `WITNESS_RIVALS` are marked weak;
`--require-rival-witness` promotes weak witnesses to warnings.

## Lessons, rotations, and verdicts

The semantic gate uses the canonical Racket authority to label materialized
lessons. `EXAMPLES_NEEDED` declares the demonstration count: use an integer in
`1..32`. Missing or invalid values fall back to 3 (invalid declarations warn).
One rich demonstration can refute multiple rivals; the actual labeled lesson
determines the result, rather than a universal minimum of two demonstrations.
Normal lessons span difficulty bands and start at `sample_index = i * 11`.
Unsupported difficulty keywords are reported as reduced coverage.
`--legacy-lesson-sample` reproduces the old fixed-start population for comparison.

`--rotate-query` holds out each already labeled pair once and reports separate
diagnostics. `--require-rotations-identifiable` also makes rotation ambiguity,
hook warnings, scoring/materialization errors, or a missing lesson contract fail.
The public wrapper accepts it with `--stage semantic_gate` or `--battery`:

```bash
arcpuzzles check TASK_ID --stage semantic_gate --require-rotations-identifiable \
  --out var/checks/required-rotations
```

The explicit policy is bound into the retained settings and native battery
subject. Repeat the flag with `--resume`; diagnostic evidence cannot satisfy
the stricter requirement. Default checks retain their existing policy. The after-repair battery requests the
diagnostic rotation smoke test. Neither mode enumerates all cyclic windows.

Without core hooks, lesson competitors, or canonical shortcuts, the gate reports
`NO_CONTRACT`; rivals or a schedule alone are insufficient. `--require-contract`
turns this advisory into a failure. Otherwise, task verdicts are `PASS`, `WARN`,
or `FAIL` (`IMPORT_FAIL` for import errors). CLI exits are 2 for failures, 1 for
warnings/advisories under `--strict`, and 0 otherwise. Read the JSON verdict and
diagnostics: exit 0 can include warnings or an untested semantic contract.

The separate lesson census unions all three rival dictionaries with namespace
prefixes, uses consecutive requested starts, and records accepted sample indices.
Its census, saved-label rescore and compact companion report `unique_rivals`,
`declaration_bindings` and `rival_identities`. A unique identity means the same
local name and exact callable object in this run. `declared_in` and `bindings`
retain every namespace. Identical source text alone does not merge closures or
distinct callables; different names remain separate. These counts do not measure
semantic diversity. Pure deterministic namespace aliases share one prediction
per input within canonical scoring or a materialized lesson and its rotations.
Existing per-binding verdicts, errors and counterexamples remain explicit.
It uses `reviewer_support.canonical_pairs(..., labeled_only=True)` only for
canonical rival-fit metadata: test pairs with an absent output key are skipped,
while malformed present outputs fail. No labeled pairs is an error. Generated
lessons still require authoritative labels. The helper's default remains strict.
See [shared tools](../shared/README.md) for census statuses, checkpoints, rotation
policy, and limits.

## Consuming a fixed-seed schedule census

A positive integer `LESSON_SCHEDULE_PERIOD` requests enumeration evidence. A
sampled semantic check alone reports `declared_period_not_enumerated`. To supply
the completed census explicitly:

```bash
python3 -m arcpuzzles check TASK --stage semantic_gate \
  --schedule-census checks/schedule-period-s0.json --schedule-seed 0 \
  --out var/checks/TASK/semantic-with-schedule
```

The same options work with `--battery` and `--stage audit`. The direct portable
script also accepts them, for exactly one task. The checker requires:

- Current generator bytes, canonical rule source and callable hashes, rule
  identity/file and declared rule hash to match the receipt.
- The current declared period, requested uint32 seed, all three bands in their
  standard order and the current demonstration count (default three).
- Complete runtime/instance bindings, every requested starting residue and
  every labelled query rotation; `rotation_policy: require`.
- Completed execution, consistent lesson/pair/rotation counts, no errors or
  hook warnings, the complete current rival inventory, and successful
  declared-rival outcomes in every lesson and
  rotation. A topline zero cannot conceal a failing row.

Accepted coverage is `complete_fixed_seed_reported`, with the receipt hash and
exact population. This consumes reported evidence without re-executing its
reference labels. It removes only the unmet enumeration warning. Other semantic
checks and missing-contract findings retain their severity. The period itself
is a generator declaration; acceptance proves neither all-seed identifiability
nor training eligibility, and closes no audit.

The public check retains the exact input bytes in
`checks/schedule-census-input.json`; their hash and requested seed bind its saved
settings and the native battery subject. Changed inputs cannot reuse earlier
passing markers. A stale, malformed, partial or failing receipt is retained and
reported as a rejection, rather than falling back silently to sampled coverage.
