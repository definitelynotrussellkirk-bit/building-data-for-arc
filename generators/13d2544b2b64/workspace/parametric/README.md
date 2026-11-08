# Crossing-priority episode prototype

**Status: proposed task-local prototype.** This extension does not change the
selected generator interface, the canonical Racket authority, approval records,
or production generation. The ordinary generator repair has separate coverage.

## Parameter and preserved reasoning

| Parameter | Allowed values | Original/default value | Executed effect |
|---|---|---|---|
| `crossing_priority` | `horizontal`, `vertical` | `horizontal` | When both agreements propose different non-background colors at a center-panel cell, choose the named orientation. |

`materialize_rule()` returns the exact canonical Racket text. The alternate
program swaps only the final two `cond` branches for `h-mark` and `v-mark`.
Both complete programs are retained under the evidence bundle's `private/rules/`.

The following constraints are the same for both settings; none is conditional
on the hidden parameter:

- Two all-zero separator rows and columns divide the input into a 3×3 array of
  equal panels. Generated examples are 8×8, with nine 2×2 panels.
- Color `0` remains the separator color; color `1` remains the panel background.
  Markers are colors `2..9`. Their identities do not define the parameter.
- An opposite pair must have exactly equal colors other than `1` to propose a
  mark. Unequal colors and a single source do not suffice.
- Horizontal agreements act in the middle column of panels; vertical
  agreements act in the middle row. Outer middle panels still transform.
- Matching pairs can overwrite an occupied target. All proposals read the
  original input, so newly painted cells cannot trigger further fills.

Every episode uses four demonstrations: canonical controls, an equality
near-miss, a different-color crossing, and an overwrite example. The query is a
different crossing input. Query sampling retries at most 64 indices to avoid
duplicating a demonstration. Input draws are independent of priority.

The hidden parameter is selected for the episode using the first eight bytes of
SHA-256 of `13d2544b2b64:crossing_priority:SEED`, interpreted big-endian, modulo
two. Seeds are literal nonnegative integers; booleans and coercible strings are
rejected. The same selected rule labels every demonstration and query. An
explicit priority override is available for controlled comparisons and is
recorded privately as an explicit selection.

## Exact commands

Run these commands from **`WORK/`**. The wrapper changes the payload working
directory to `WORK/repo/`, so the second interpreter path starts with `../`.
Dependencies are the packet's Python 3.12+, NumPy, Pillow and pytest, plus its
included offline Racket runtime.

```bash
.venv-review/bin/python run_with_racket.py ../.venv-review/bin/python generators/13d2544b2b64/workspace/parametric/prototype.py build --out ../checks/parametric/final --seeds 0 5

.venv-review/bin/python run_with_racket.py ../.venv-review/bin/python generators/13d2544b2b64/workspace/parametric/prototype.py verify ../checks/parametric/final

.venv-review/bin/python run_with_racket.py ../.venv-review/bin/python -m pytest -q generators/13d2544b2b64/tests/test_parametric.py --tb=short --junitxml=../checks/parametric/tests-final.xml
```

The builder requires a new output directory. To regenerate an already retained
bundle, use a fresh `--out` path; to check the existing bundle, use `verify`.
For an explicitly fixed rule, add `--priority horizontal` or `--priority vertical`
to `build`. Omitting that option selects the rule from each episode seed. Invalid
parameters, invalid seeds, stale source bindings, and failed checks fail loudly.

## Retained evidence

The current evidence is in `WORK/checks/parametric/final/`. Exact commands, exit
codes and stdout/stderr are retained beside it in `build-final-command.json`,
`verify-final-command.json` and `tests-final-command.json` with their named output
files. `red-command.json`/`red-pytest.txt` retain the initial test-first failure;
`inventory-red-*` and `inventory-green-*` retain the checker regression cycle.

| Episode seed | Selected priority | Alternate priority | Demonstration that refutes it | Query also differs |
|---|---|---|---|---|
| `0` | `horizontal` | `vertical` | Third demonstration, index `2` | Yes |
| `5` | `vertical` | `horizontal` | Third demonstration, index `2` | Yes |

The bundle contains two complete episodes: eight demonstrations and two
queries, ten pairs total. The builder performs 46 actual Racket rule evaluations
covering labels, both parameter candidates, deterministic repetition, four
canonical pairs and both versions of the crossing witness. Independent bundle
replay performs 26 Racket evaluations, including all ten episode pairs under
both settings. The default matches all four canonical input/output pairs.

The explicit crossing witness is lawful under the task grammar. At zero-based
cell `(3,3)`, horizontal priority produces color `3` and vertical priority
produces color `9`; its complete input and both executed outputs are retained.
Both episode checks require the rival to fail on demonstrations before examining
whether the query distinguishes it. A query answer cannot rescue ambiguous
demonstrations.

The focused tests cover canonical source/label parity, a simultaneous-read
cascade trap, overwritten targets, unequal and one-sided negatives, deterministic
selection and generation, both priority values, strict public projection,
malformed parameters/seeds, ambiguous demonstrations, tampered answers, artifact
hashes and complete episode inventory. The inventory regression checks that an
edited report cannot omit or duplicate a retained episode even after its own
manifest hash has been updated.

### Exact source hashes

These are SHA-256 hashes of the full source bytes, distinct from the canonical
generator's short normalized rule identifier `301b331591ad`.

| Source | SHA-256 |
|---|---|
| `prototype.py` | `5d0c7534a3c355318d281331261875298ee2dcb0de3a169c8fd85cddffad55f2` |
| `episode_tools.py` | `1b35f9dc1ba37a0ce974b81768f1ec76706536f9764a8cf3e206e279005e5e60` |
| Selected generator, version `3.1.0` | `89e62ab17177d9587fdfa03f593245e3e7eacdacfb388452e03079d61e1fe96e` |
| Default/horizontal Racket | `a699bbb01d8be15bf86293fdf76bebcf226ebfb019c6968f8917cc74a4f0e0c8` |
| Alternate/vertical Racket | `f2d208c9181de9520fb946f589a642d6032d8014e05187fe414471cadc1999ad` |

Each private episode includes the exact selected program, parameters, seed,
sample indices/profiles, labels and source hashes. `report.json` includes the
executed Racket binary, bridge and prelude identity. `manifest.json` binds every
retained artifact. Verification rejects source drift, an inconsistent artifact
inventory, omitted/duplicated episode indices, mismatched public projections and
labels that disagree with execution.

## Public files and reusable interfaces

Only `public/challenge-*.json` files are solver-facing. Each has exactly `train`
and `test`; demonstrations contain `input` and `output`, while queries contain
only `input`. There are no parameters, seed, reference source, hashes, rule
metadata or query answers in these files. Treat the report and `private/` files
as controller/authoring data.

`episode_tools.py` provides reusable primitives without changing shared code:

- `ParameterSpace`: bounded declarations, strict validation, defaults and stable
  seed selection.
- `RacketRunner`: exact `rule!` source execution through the included protected
  bridge, with input/output/program hashes and live runtime identity. It has no
  Python-output fallback.
- `rival_report`: runs every declared candidate and records exact pixel
  differences, keeping demonstration refutation separate from query differences.
- `public_challenge`: creates an independent copy using an explicit field
  allowlist.

`prototype.py` supplies the task-specific `materialize_rule`, `sample_inputs`,
`build_episode`, `check_episode`, `write_bundle` and `verify_bundle` interfaces.
Its source discovery uses `reviewer_support` to stay within its current library
or relocated runtime. The selected generator is loaded through the manifest-aware
public loader; there are no predecessor or sibling source dependencies.

## Limits

This is bounded authoring evidence for one meaningful two-value rule change.
The parameter rival check covers those two settings; it is not a proof against
every conceivable shortcut. Generated episodes currently use medium difficulty,
fixed canonical panel dimensions and four demonstrations. The retained two
seeds do not establish coverage over all seeds or all lawful grids. No production
parametric API, shared integration, catalog change, approval or training
admission is implied.
