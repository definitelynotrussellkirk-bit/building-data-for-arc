# Aggregate-count replication — proposed parameter prototype

This is a **proposed, task-local prototype**, separate from the production
`7fc158ab7b70` generator and its canonical Racket authority. The original task
is `ac0a08a4`. No rule variants are admitted or approved by this implementation.

## Rule and finite settings

Count a property of the input, then replicate every input cell by the resulting
factor. The nonzero cells retain their colors and relative order; zero cells
replicate in exactly the same way. The two bounded parameters are selected once
per episode and remain fixed across all demonstrations and queries:

| Parameter | Allowed values | Meaning | Canonical default |
| --- | --- | --- | --- |
| `count_basis` | `cells`, `colors` | Count nonzero cells, or distinct nonzero colors | `cells` |
| `scale_axes` | `both`, `rows`, `columns` | Replicate along both dimensions, rows only, or columns only | `both` |

The Cartesian product contains exactly six settings. The canonical default
`cells` + `both` preserves the selected reference outputs, rather than changing
which canonical rule production uses. Counting an aggregate and then using it
to replicate the grid are the invariant reasoning steps. Distinct-color counting
is a nearby meaningful alternative already known as a plausible shortcut;
one-axis replication changes the spatial execution while preserving that
aggregate-to-replication dependency. No unrelated operation is added.

All settings deliberately share the original conservative domain: square inputs
of side 3..5, 2..6 nonzero cells, colors 0..9, and `side * nonzero_cells <= 30`.
Monochrome inputs contain exactly two spatially separated nonzero cells. These
constraints guarantee an output side at most 30 even for cell count scaling.
They are stronger than strictly necessary for one-axis or color-count variants,
and are independent of the setting. They avoid confounding rule choice with
which input sizes occur. Boundary queries include a 5×5 input with six nonzero
cells, producing 30×30 at the canonical setting. This family does not support
large input grids under its retained canonical domain.

## Teaching and ambiguity evidence

The first three demonstrations have these nonzero-cell / distinct-color counts:

1. `(2, 1)`: a monochrome repeated pair distinguishes cell count from color count.
2. `(4, 2)`: repeated multicolor cells distinguish both count bases and all axes.
3. `(3, 3)`: a unique-color contrast shows that count bases can coincide.

For color-count scaling, the first example alone leaves all three axis settings
indistinguishable because its factor is one. The second example resolves this
ambiguity. Tests explicitly retain that first-demo ambiguity and verify that the
complete demonstration context leaves only the chosen setting.

`identify_demonstrations(demonstrations, labeler)` has no query argument. It
executes the six instantiated programs on the demonstrations and retains only
programs matching all demonstration outputs. Query predictions are scored only
after that survivor set is fixed. Private evidence records each rival's
refuting demonstration indices and every query's alternative prediction hash,
shape, agreement with the selected output, demonstration survival, and ambiguity.
This is finite evidence against six declared settings, not a proof against all
possible ARC rules. Per-query alternatives can agree with the selected rule even
when their episode semantics were already ruled out by demonstrations.

## Run from an extracted packet

Use the packet's Python environment for **both** wrapper and payload. The wrapper
sets the included offline Racket runtime and makes `WORK/repo` the effective
working directory. The following commands run from the outer extraction folder;
substitute that folder's absolute path for `PACKET`:

```bash
PACKET=/workspace/scratch/4bbe6d6743f0/arc-review
"$PACKET/WORK/.venv/bin/python" "$PACKET/review.py" run \
  "$PACKET/WORK/.venv/bin/python" \
  generators/7fc158ab7b70/workspace/parametric/scaling.py \
  --all-settings --seed 17 --train 3 --test 4 \
  --out ../checks/parametric/six-settings-seed17
```

This is the exact six-setting, four-query evidence recipe. A single fixed setting
uses `--count-basis colors --scale-axes rows` instead of `--all-settings`. Omitting
both setting flags selects the canonical default. `--seedchoose` selects one of
the six settings deterministically from the episode seed, using a separate RNG
stream from input generation, and cannot be combined with explicit settings.
The selected setting is stored only in private evidence. Rule selection occurs
once, before any pair is labeled; pair creation never resamples it.

`--train` and `--test` are separate. Defaults are three demonstrations and four
queries. Supported bounds are 3..20 demonstrations and 1..100 queries. Fewer than
three demonstrations are rejected because this teaching contract requires the
contrastive prefix. Every input is distinct across both splits. The sampler has
an explicit 5,000-attempt cap per input and raises on exhaustion, rather than
cloning a query or returning fewer pairs. Output directories must be new.

A focused test command is:

```bash
"$PACKET/WORK/.venv/bin/python" "$PACKET/review.py" run \
  "$PACKET/WORK/.venv/bin/python" -m pytest -q \
  generators/7fc158ab7b70/tests/test_parametric_scaling.py
```

## Authority and outputs

`RacketLabeler` reuses the included protected `arc_repl.racket_bridge.RacketBridge`.
Each emitted callable Racket expression is applied to every input. The exact
expression and SHA-256 are retained in each private episode and `rule.rkt`.
The Python mirror checks parity but never supplies authoritative labels.
The selected canonical Racket text is separately executed over all episode
inputs and compared with the prototype's default behavior. Its original full
text/hash, the selected generator hash, and the actual runtime identity are
retained. The canonical `(rule! ...)` wrapper is removed solely to apply its
unchanged callable body through the same bridge; no canonical source is edited.

For a six-setting suite at one seed, the input grids are shared across settings.
The bridge executes 42 setting/input combinations plus seven canonical-reference
applications. Results are cached by exact source SHA-256 and input SHA-256;
repeated identifiability checks reuse those actual executions, rather than
spawning extra runtimes or substituting the mirror.

Each setting directory has separate files:

- `public.json`: exactly demonstration inputs/outputs and query inputs. No
  settings, rule text, reference metadata, or query answers.
- `private.json`: answers, selected setting, exact Racket, hashes, canonical
  parity, domain receipts, and demonstration/query rival evidence.
- `rule.rkt`: the exact matching callable Racket expression for authoring use.

The suite `manifest.json` binds source files, command, seed, counts, selections,
public/private file hashes, runtime identity, and actual Racket evaluation count.
Do not expose private files or the suite manifest as a model-visible challenge.
The runtime bridge and production interfaces remain unchanged. Evidence is
bounded to the recorded seed/settings; it establishes neither universal
identifiability nor training eligibility.

The focused tests use `reviewer_support.find_root` and
`load_selected_generator`, preserving portable source binding. They check the
six distinct witness shapes, legal deterministic input generation, separate
counts, setting validation/selection, canonical parity, actual Racket labels,
all demonstration-only survivors, query ambiguity, and public/private separation.
