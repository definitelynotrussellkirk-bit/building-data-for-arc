# Native promotion wrapper — review-8e48265b8c9215ac

The current native contract is `promotion.json`.  It keeps the retained
`beam_width.py` prototype and production `generator.py` unchanged, exposes only
`wing_multiplier` 1 or 2, accepts 2–6 demonstrations, and always emits exactly
four queries.  `adapter.py` uses a pure claim-label path; the native qualification
worker independently executes every label through the protected Racket runtime.
For a fixed seed and demonstration count, both settings receive byte-identical
input streams.  The query schedule ends with a 30×30 case.

Reproduce the bounded matrix audit from `WORK/`:

```bash
python3 run_with_racket.py python3 \
  generators/038f266f3acf/workspace/parametric/audit_native.py \
  --seeds 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 \
  --demos 2 3 4 5 6 \
  --out ../checks/038f266f3acf/native-audit.json
```

After producing native qualification evidence, build and replay the causal
witness with the source-bound helper:

```bash
python3 run_with_racket.py python3 \
  generators/038f266f3acf/workspace/parametric/verify_causal.py \
  --qualification ../checks/038f266f3acf/qualification/qualification.json \
  --out ../checks/038f266f3acf/sequential-dependency
```

That helper selects the maximum-area query for each qualified setting and uses
the `min(depth, 4)` shortcut as a wrong-intermediate counterfactual.  It delegates
construction and replay to `arcpuzzles.review_witness`; the resulting JSON is
finite source-bound evidence, not owner acceptance or training admission.

---

# Marker-derived beam width — proposed prototype

This task-local extension preserves the source extraction and marker-derived
outward-beam reasoning of `training:b527c5c6` / `038f266f3acf`. It is a
**proposed prototype**, separate from the selected generator's production API,
canonical authority, approval, and training admission.

## One meaningful parameter

`wing_multiplier` is the exact integer **1 or 2**, fixed once per episode.
**1 is the canonical/default rule.** The red marker identifies an object's rim,
the rim determines the outward direction, and the distance to the opposite
edge supplies a source depth. The red centre ray extends to the grid boundary;
the green half-width at every step is `wing_multiplier × source_depth`.

The default `materialize_program(1)` returns the exact canonical
`program_solution` bytes, SHA-256:

```text
d4bc451f18638b8e2f71528bb3fa627716cef2327f0656cfdb44e86ec68971a0
```

The multiplier-2 program changes only
`(range 1 (+ half 1))` to `(range 1 (+ (* 2 half) 1))`.
It preserves the alternating row/column source-box growth, original-input
marker lookup, outward direction, full-length red ray, green wing painting,
clipping, and row-major marker processing order. It does not change colors,
source positions, or the source-depth calculation. Canonical source drift or
an ambiguous edit site causes an explicit failure.

## Deep, identifiable teaching scenes

Each input contains two separated solid green rectangles, one red non-corner
rim marker per rectangle, one horizontal launch, and one vertical launch.
The two source depths are **5 and 6**; their assignment varies. At least one
marker is noncentral. Dimensions vary independently over 24–30 rows/columns,
and a whole-grid D4 transform varies orientations and positions. Some wider
wings reach a side boundary and are clipped by the unchanged canonical rule.

The sampler checks the selected generator's current `self_check`. It also
requires the **multiplier-2** beam corridors to avoid every source and each
other, so all narrower declared models have disjoint corridors too. This is a
deliberate teaching restriction; it avoids hidden dependence on paint order.
The mirror still follows row-major marker order, and every retained prediction
is compared with actual Racket execution.

These scenes address a concrete gap in the existing production profiles,
whose source depths are 1–4. The private certificate tests four exact models:

| Model | Green half-width |
|---|---|
| Canonical multiplier 1 | `depth` |
| Proposed multiplier 2 | `2 × depth` |
| Cap-four rival for multiplier 1 | `min(depth, 4)` |
| Cap-four rival for multiplier 2 | `2 × min(depth, 4)` |

The default cap-four rival is the reported shortcut. The multiplier-2 rival
caps source depth before scaling, preserving the analogous shortcut for the
variant. These two rivals are audit models, not additional episode parameters.
Every accepted input must produce distinct observable predictions for all four
models. Merely placing a deep rectangle does not suffice if clipping or other
paint hides the difference.

## Determinism, counts, and rejection limits

The Python entry point is:

```python
generate_episode(seed=17, wing_multiplier=1,
                 n_train=2, n_test=4, max_attempts=128)
```

Demonstration and query counts are independent exact integers in 1–16. Their
defaults are 2 and 4. Every input is distinct within the episode. One
well-chosen demonstration suffices within the declared four-model comparison,
so one demonstration is supported without weakening that finite certificate.

If `wing_multiplier` is omitted, one value is selected once from the seed by a
separate deterministic random stream. Explicit multipliers share the same
seed-based scene stream for controlled comparisons. Seeds must be exact
integers from 0 through `2**64 - 1`; bools, floats, and numeric strings are
rejected by the Python API. Both settings use identical input constraints.

There are at most `max_attempts` scene draws, default 128 and permitted range
1–4096. Each construction attempt enumerates finite placements and a grid of
at most 30×30 cells. Construction failures, structural failures, collisions,
unobservable distinctions, and duplicate inputs consume attempts. Insufficient
accepted inputs raises `SamplingExhausted` with counts and reasons; a partial
episode is never returned. The maximum accepted argument values are API bounds,
not a claim that every seed succeeds at those counts or budgets.

## Exact labels and demonstration-only certificates

Python is a candidate-screening mirror. Every retained input is then evaluated
under **all four exact Racket programs** through the protected `RacketBridge`.
The outer `rule!` command wrapper is removed to apply its unchanged lambda;
`h` and `w` are bound to the actual input dimensions, as the canonical executor
provides them. These bindings do not alter the program bytes. A mirror mismatch
aborts generation. In-process caching uses the exact input hash and model name;
cache entries originate in executed Racket results.

The certificate compares each model's executed predictions with demonstration
outputs, records the demonstrations that reject it, and retains surviving
models. It then evaluates each query **input**, records prediction hashes and
parameter/cap-rival disagreement counts, and checks agreement among survivors.
It never reads query answers, private seed fields, or private parameter fields.
Generation requires the selected multiplier to be the sole surviving model.

This is a finite rival certificate, **not universal rule uniqueness**. A test
using an ordinary shallow production demonstration confirms that the cap-four
rival survives and the deep queries are reported as unidentifiable. The
prototype does not call production `lesson_identifiable`, whose demonstration
requirements and profile-anchor checks are a separate contract.

## Exact four-query command

From the packet's `WORK/` directory, with the included runtime configured:

```bash
python3 run_with_racket.py python3 \
  generators/038f266f3acf/workspace/parametric/beam_width.py \
  --seed 17 --settings 1 2 --train 2 --test 4 --max-attempts 128 \
  --out ../checks/parametric/batch
```

The wrapper runs the payload from `WORK/repo/`, so the destination is
`WORK/checks/parametric/batch`. It must be a new directory. This writes two
complete episodes, with four distinct queries each, and all four exact Racket
programs. In an ordinary checkout, run the payload directly from its repository
root with Racket on `PATH` or `RACKET_PATH` set and choose a new output path.

Run the focused tests from `WORK/`:

```bash
python3 run_with_racket.py python3 \
  generators/038f266f3acf/tests/test_parametric_beam.py
```

The suite uses standard-library `unittest`; pytest is unnecessary. Actual
Racket and the existing runtime dependencies are required. Missing Racket is
an execution failure, not a skipped success.

## Public and private exports

Give a solver **only `batch/public/`**. It contains exactly visible training
inputs/outputs and query inputs. Canonical public bytes and full SHA-256
filenames come directly from the shared
`reviewer_support.public_challenge_bytes` and `public_challenge_id` helpers.
Filenames have no parameter, seed, or setting-associated ordinal. Batch order
is sorted by visible-content IDs. Hidden-field or query-answer changes cannot
change a public ID. Duplicate visible payloads are rejected before creating
the output directory. Use a neutral caller-chosen destination name too.

`batch/private/` retains complete episodes, all four models' executed outputs,
parameters, seeds, source-object witnesses, certificates, exact program text
and hashes, and the runtime/export receipt. Source hashes cover this prototype,
the selected generator actually used for grammar checks, the shared projection
helper, Racket bridge, and prelude. The writer validates every materialized
program against its declared model and exact digest. Private evidence must
remain separate from the public challenges.

## Focused coverage and remaining limits

Tests cover strict numeric types and bounds; canonical byte identity; default
Racket/mirror parity on all 10 supplied labeled canonical pairs; actual Racket
parity for all four models; deep/clean/multiple-source witnesses;
reproducibility; independent counts; four distinct queries; demonstration-only
certificates; shallow-demo ambiguity; bounded duplicate retries; exact shared
public projection; opaque sorted identifiers; private program materialization;
duplicate-visible rejection; and a real CLI invocation with runtime receipt.

The retained runs are bounded evidence. They do not certify every seed,
maximum counts, arbitrary overlapping beams, or all structurally legal inputs.
The teaching sampler deliberately uses two deep rectangles and separated
corridors at 24–30 scale; it does not establish that production sampling now
covers those cases. Production sampler expansion, the canonical lesson-guard
repair, variant approval, and training admission remain separate work.
