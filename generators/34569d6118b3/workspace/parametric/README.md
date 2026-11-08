# Ordered-template parameters: runnable proposed prototype

Status: **proposed prototype, not approved or admitted to training**. This is
separate from the selected canonical generator and its rule authority. It uses
only the selected checkout's Python standard library and included Racket bridge.

## Rule and parameters

The input retains the original family: non-gray color swatches and gray template
masks occupy the header; its first all-zero row separates a dense color layout.
The layout expands into colored copies of the masks. Parsing the header, matching
swatch colors, finding the layout, preserving mask holes, and composing the
expanded output remain necessary in every setting.

| Parameter | Allowed values | Canonical default | Executed change |
| --- | --- | --- | --- |
| `template_order` | `forward`, `reverse` | `forward` | Pair left-to-right swatches with left-to-right or right-to-left templates. |
| `mirror` | literal `false`, `true` | `false` | Reflect each chosen mask horizontally before coloring it. |

Mirroring is local to each mask; it preserves the layout's positions and colors.
The two parameters give four settings. A setting is chosen explicitly once per
episode and held fixed for every demonstration and query. `--all-settings`
creates one separate episode for each setting with a common deterministic input
seed. Parameters never appear in the public challenge.

`forward,false` returns the canonical ledger's **exact original Racket string**,
whose SHA-256 is
`213d60bb58991cfb0f063a34f4ad178ac1fe312f144a5583abcfc166cfe8fc8f`.
The canonical normalized rule hash remains `e2b81b5e525c`. Alternative references
replace one or two exact expressions, each required to occur exactly once; source
drift fails closed. The shared `strip_rule_wrapper` helper exposes the already
closed lambda for the bridge. These pinned references use standard Racket syntax
and bind their own `h` and `w`; no rewritten shorthand or implicit bindings are
needed. Both exact reference and executed callable hashes are retained privately.

## Run from `WORK/`

Prepare the included runtime:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B setup_racket.py
```

Generate all four settings, **three demonstrations and four distinct queries
per episode**, with labels and every parameter rival executed in Racket:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B run_with_racket.py python3 -B \
  generators/34569d6118b3/workspace/parametric/prototype.py \
  --all-settings --seed 42426 --demo-count 3 --query-count 4 \
  --out ../checks/parametric/episodes
```

The destination must be new. For a rerun, choose another output directory. For
one alternative with an independent demonstration count:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B run_with_racket.py python3 -B \
  generators/34569d6118b3/workspace/parametric/prototype.py \
  --template-order reverse --mirror true --seed 17 \
  --demo-count 1 --query-count 4 --out ../checks/parametric/one-demo
```

Run the focused, dependency-free regression suite:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B run_with_racket.py python3 -B \
  generators/34569d6118b3/tests/test_parametric_34569d6118b3.py
```

The suite uses `unittest`; pytest is not required. A direct invocation without a
Racket executable explicitly skips the two Racket integration tests. Such a run
does not establish Racket parity. The wrapper exercises the full suite.

## Sampling and identifiability

The sampler calls the unchanged generator's ten general profiles, cycling them
in their declared order with deterministic `(seed, sample_index)` draws. It
rejects duplicate complete inputs across both splits. Counts are independently
configurable from 1 through 32, with a default maximum of 512 candidate draws;
`--max-attempts` accepts at most 4096. Exhaustion raises `SamplingError` with the
actual rejection rows, never a short or cloned batch. Canonical generator
construction failures propagate rather than being converted into success.

The first demonstration must give four different outputs under the four
settings. This is stronger than merely identifying the selected setting and
intentionally biases the teaching examples toward an informative witness.
The other inputs retain the general profiles, including compact cases.

The compact two-color profile exposes a real failure mode: its two distinct
2-by-2 masks have a full gray top row and one gray bottom cell, so they are each
other's horizontal reflections. `forward,false` and `reverse,true` then agree;
`forward,true` and `reverse,false` agree. Such an input alone cannot identify both
parameters. The sampler rejects it as the first demonstration, and a regression
checks that an ambiguous demo retains both rivals and fails to identify a
distinguishing query.

Every retained input is executed under all four exact matching Racket references,
with Python mirror parity required for every result. Survivors are computed
from **demonstration inputs and outputs only**. Each query input is evaluated
against those survivors without consulting its hidden answer. A complete episode
requires the selected setting to be the sole survivor and every query to have a
single survivor prediction. The first demo's four executed outputs are retained
as a compact private witness. This tests the declared parameter rivals; it is
not a census of all plausible ARC programs or shortcuts.

## Public/private export contract

Publish only the `public/` child of an export:

- Each challenge is `<sha256>.json`, containing exactly the bytes returned by
  `reviewer_support.public_challenge_bytes`. The filename is its
  `public_challenge_id`, the SHA-256 of those exact bytes.
- `index.json` contains only the sorted opaque identifiers. Filenames and order
  do not encode seeds, settings, setting ordinals, programs, or query answers.
- Hidden metadata and query-answer changes cannot change public bytes or names.
  Duplicate public projections reject the entire batch before any files or
  directories are created, even when private metadata or query answers differ.

The `private/` child retains full episodes, settings, seeds, queries and answers,
sampling/rejection records, demonstration-only survivor checks, exact Racket
reference files named by their hashes, runtime identity, source hashes, and a
receipt. No private setting map is stored under `public/`.

The writer validates and serializes the complete batch before staging it. Linux
`renameat2(RENAME_NOREPLACE)` publishes the directory atomically and refuses an
existing destination, including one created concurrently. This export operation
requires Linux, the included runtime's platform; unsupported systems fail rather
than weaken the no-overwrite contract. The writer itself projects supplied
episodes; verified labeling is guaranteed by `build_episode`, not by trusting
arbitrary user-provided dictionaries passed to `write_export`.

## Small Python API

`Settings`, `reference_program`, `python_mirror`, `sample_inputs`,
`surviving_settings`, `check_query_identifiability`, `RacketOracle`,
`build_episode`, and `write_export` are exposed from `prototype.py`.
`build_episode(seed, setting=Settings(), demo_count=3, query_count=4)` owns a
Racket bridge by default; callers may supply one to reuse the runtime across
episodes. `sample_inputs` and the Python mirror are authoring helpers, not a
Racket-free labeling fallback.

The canonical generator, canonical examples, authorities, runtime interfaces,
approval records and frozen fixtures are unchanged. Bounded seed/profile checks
support this prototype only; there is no universal seed-success claim or
production parametric API integration.
