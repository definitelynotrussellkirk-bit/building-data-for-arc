# Mixed sampling and export formats

`arcpuzzles export` draws from generators matching the query flags. By default
it requires current effective approval and samples in proportion to recorded
positive mix weights. `--sampling uniform` gives each matching generator equal
probability. `--id` may be repeated to choose a smaller pool; every supplied ID
must also satisfy the filters. Seeds and the full pool are recorded.

## Approved versus unapproved: two commands

After installing this checkout, [the teammate quick start](teammate-start.md)
provides the setup and handoff steps. Pick one pool and a new output directory:

```bash
# Approved generators only; individual episodes still require verification.
arcpuzzles export --approved --count 4 --seed 17 --sampling uniform \
  --style episodes --out var/datasets/approved-s17
arcpuzzles inspect-export var/datasets/approved-s17

# Unapproved generators only, explicitly for research/review.
arcpuzzles export --not-approved --allow-unapproved --count 4 --seed 17 \
  --sampling uniform --style episodes --out var/datasets/unapproved-s17
arcpuzzles inspect-export var/datasets/unapproved-s17
```

`--allow-unapproved` alone permits both pools; it does not mean unapproved-only.
`--not-approved` covers every source failing effective approval, including
changed source hashes and active vetoes. Reference success does not upgrade
approval. Per-episode approval/provenance and the pool are retained privately;
export completion does not grant model-training admission.

## Filters, difficulty and files

```bash
arcpuzzles export --approved --source training --count 20 --seed 17 \
  --train 4 --test 1 --draw-difficulty easy --out var/datasets/public-20
arcpuzzles inspect-export var/datasets/public-20
```

`--difficulty` filters recorded canonical difficulty, as it does in `list`.
`--draw-difficulty` is passed to the generator. `--count` counts accepted episodes,
not rendered rows. A multi-query chat export emits one training row per query.

The output directory must be new. It contains:

| File | Contents |
|---|---|
| `public.jsonl` | Opaque episode IDs, visible demonstrations and query inputs only |
| `labels.private.jsonl` | Matching query outputs and controller provenance |
| `lineage.private.jsonl` | Per-episode official-parent lookup, generator hash, evidence and unresolved reasons; never actor-visible |
| `episodes.private.jsonl` | Generated episodes, reference programs, seeds and source provenance |
| `data.private.jsonl` | Optional rendered training rows, including their targets |
| `tensor-*.private.safetensors` | Optional CPU tensors; inputs and label tensors are separately named, all retained privately |
| `pool.private.json`, `draws.private.jsonl` | Sampling pool, actual draws and projection diagnostics |
| `rejections.jsonl` | Rejected pairs, failed workers and failed/partial projections |
| `runtime.private.json` | Runtime file identities used by the export |
| `plan.json`, `manifest.json` | Configuration, counts, completion state and content hashes |

Only `public.jsonl` is suitable for model-visible evaluation input. Copy that
projection into the actor workspace; keep the export directory with the trusted
controller. Query answers and reference programs never enter the public file.
These are fresh generated tasks, not automatically competition-held-out tasks.

Omitting `--train` (or `n_train` in the Python API) uses the selected, hash-bound
generator's literal `EXAMPLES_NEEDED`, with a floor of three for generation and
four for export. Mixed exports resolve this count separately for each generator.
Explicit counts are preserved. A declared `lesson_identifiable` hook checks the
materialized demonstrations and each labeled query on copies: automatic lessons
fail visibly when unsupported; explicit unsupported lessons carry
`diagnostic_unsupported`. An absent hook is `not_declared`, not proof of general
identifiability. Requested/resolved counts and hook verdicts are retained in
generation provenance and private export lineage. A malformed declaration is
retained under `demonstration_policy_errors` in `runtime.private.json`; drawing
that generator creates a rejected attempt, without disabling checks or blocking
other generators. Source snapshot/hash failures still stop the export. Native tensors enforce their
ten-demonstration limit on resolved counts.

No train/evaluation split is invented. Filters can use recorded family/split
metadata. A trainer must enforce its own protected family partition; missing
lineage remains unknown. ARC2train's selected RL experiment additionally requires
verified official-family lineage before it admits a training episode.
For new generated exports, the producer calls `Catalog.lineage()` against the
current generator source hash and retains the result in `lineage.private.jsonl`.
`inspect-export` checks each row against its private label, generator hash and
official-family evidence. A missing, candidate or changed-hash mapping records
`verified=false` and no family ID. This identifies the **source family**, not
an assigned learner/evaluation split or permission to train. Older exports
without the sidecar remain readable and retain unresolved lineage downstream.

## Four supervised queries per shared demonstration context

Request four query/test pairs independently of the number of demonstrations:

```bash
arcpuzzles export --approved --count 4 --seed 17 --test 4 \
  --style episodes --out var/datasets/four-query-episodes
arcpuzzles inspect-export var/datasets/four-query-episodes
```

Here `--count 4` requests four episodes and `--test 4` requests four queries in
each episode. Omit `--train` to respect each generator's demonstration policy,
or set it separately when appropriate. The query count does not set or cap the
demonstration count. Keep all queries under the episode's same reference rule;
parametric prototypes must likewise keep one parameter setting across all pairs.
The authoring preference is to obtain more supervised targets per shared context;
it is not a measured learning gain or a claim that every family supports it.

Retain distinct lawful query inputs and Racket-derived labels, and inspect each
query's lesson verdict. A family's sampling or teaching limits may reject a draw;
incomplete exports remain failures. Query answers stay in private files, never
in `public.jsonl`. `--style grids --render chatml` projects one row per query;
`--style native --group-queries` retains the four query slots together. The
separate lesson-census rotation diagnostic still requires `--test 1`.

## Existing training formats

```bash
# Grid or Racket-code chat targets; raw, chatml and harmony are supported:
arcpuzzles export --id 6c68e1b008a5 --count 2 --seed 17 \
  --train 2 --test 2 --style grids --render chatml --out var/datasets/grid-chat
arcpuzzles export --id 6c68e1b008a5 --count 2 --seed 17 \
  --style code --render harmony --out var/datasets/code-chat

# Full qwen9b_raw_instance_v1 rows, including demo-derived facts:
arcpuzzles export --count 10 --seed 17 --style episodes --out var/datasets/raw

# Closed-vocabulary token rows, using the retained DSL serializer:
arcpuzzles export --count 10 --seed 17 --style dsl \
  --mode predict --mode exec --out var/datasets/dsl

# Executed program mutations and random program-prefix traces:
arcpuzzles export --id 6c68e1b008a5 --count 1 --seed 17 \
  --train 2 --style hindsight --mutations 8 --out var/datasets/mutations
arcpuzzles export --count 2 --seed 17 --style synthpipe --stages 3 \
  --out var/datasets/prefixes
```

Default DSL modes are `predict`, `synth`, `exec`, and `invert`. Explicit optional
modes are `repair`, `refine`, and `pred_facts`. These preserve the historical
serializer, including its stochastic fact-row emission and empty-facts fallback;
the manifest records the rows actually produced. Selecting a training export
does not start SFT or change the selected RL-before-SFT experiment.

Hindsight runs mutated programs against fresh inputs and labels their actual
outputs. The mutation helper preserves its style and output checks, reporting
attempted, accepted and rejected mutation counts. It does not expose individual
mutation rejection reasons; the exported diagnostics state that limitation.
Derived mutations and synthetic chains are labeled unreviewed; approval of a
parent generator does not approve the derived program. A truncated synthetic
chain retains its successful prefixes and records the missing-stage count.

## Native grid rows and tensors

`--style native` emits the retained native numeric-grid format. Individual
queries use `arc_native_episode_v1`; `--group-queries` keeps every query in one
`arc_native_episode_v2` row. JSON-only export uses no Torch dependency. It invokes
the four pure row helpers from the pinned local builder, without running that
builder's old source-tree discovery or CLI.

```bash
arcpuzzles export --id 6c68e1b008a5 --count 1 --seed 17 \
  --train 2 --test 2 --style native --out var/datasets/native-json

# Install the optional tensor packages in this repo's own environment.
# A CPU PyTorch build suffices; use the appropriate declared wheel for your host.
.venv/bin/python -m pip install -e '.[runtime,tensors]'
arcpuzzles export --id 6c68e1b008a5 --count 1 --seed 17 \
  --train 2 --test 2 --style native --tensors native \
  --out var/datasets/native-tensors
arcpuzzles export --id 6c68e1b008a5 --count 1 --seed 17 \
  --train 2 --test 2 --style native --group-queries --tensors bottleneck \
  --out var/datasets/bottleneck-tensors
```

The native layout supports up to ten demonstrations and one query per row.
The bottleneck layout preserves all requested query slots when grouped, with
context/query capacities recorded in its metadata. No augmentation or pair
corruption is applied. `--canvas-size` defaults to30; oversized grids are rejected
with the worker failure retained, rather than cropped.

Each tensor artifact has a corresponding row containing its hash, size, layout,
tensor names/shapes/dtypes and non-tensor metadata. Native target placeholders
contain only the NULL cell value10; query answers are in the separately named
`labels` tensors. Bottleneck query inputs and labels are also distinct tensors.
These are training artifacts and belong with the trusted controller; continue
to give evaluation actors only `public.jsonl`.

The tensorizer uses the copied ARC-native modules on CPU. Safetensors avoids
pickled Python objects; layout metadata is ordinary JSON. `inspect-export`
checks the full file inventory and row-to-tensor hash bindings without importing
Torch. The export diagnostics record the actual Torch and safetensors versions.

## Bounds and failed runs

The default draw cap is twice `--count`; set `--max-attempts` explicitly to change
it. Each generation and rendering worker has a `--timeout` in seconds. No
unbounded producer or watchdog is launched. Duplicate episode content within an
export is rejected. Failed attempts retain their errors and process output.

If the draw cap is exhausted, `manifest.json` says `incomplete` and the CLI exits
nonzero. The verifier refuses incomplete or altered exports. Do not treat a
short export as a completed training dataset. The directory is retained for
diagnosis; use a new output path for another run.

## Generation compatibility census

```bash
arcpuzzles census --workers 4 --seed 17 --draw-difficulty medium \
  --timeout 12 --out var/census
```

This compares one train and one test pair from every selected generator against
the retained historical runner, using local copied code and authorities. It
records equal pairs, differing outputs, routes working only in one implementation,
and failures in both. The new API uses current canonical authority and adds
self-checking, so a difference requires inspection rather than automatic rollback.
It never changes an approval label. One seed is compatibility evidence, not a
full semantic review or a proof covering every override and seed.

The completed v0.3 census covered all 3,941 generators at seed17/medium:
3,911 equal, 21 current-only, 2 historical-only, 4 different and 3 failures in
both routes. All 449 approved generators matched. The
[classification](migration/census-classification.md) explains every exception
and the subsequent v0.5 compatibility changes. The original results remain
unchanged, including failures.

## Explicit archival rules

```bash
arcpuzzles generate 7c7796f15a18 --seed 17 --train 1 --test 1 \
  --reference archival --allow-unapproved --out var/archival-example.jsonl
arcpuzzles export --id 7c7796f15a18 --count 1 --seed 17 \
  --reference archival --allow-unapproved --sampling uniform \
  --out var/datasets/archival-research
```

`reference="archival"` is also available on `Catalog.generate()` and
`Catalog.export()`. It selects the retained historical rule authority for a
per-puzzle generator. Canonical remains the default; a failure never silently
switches authorities. Archival output is always unapproved, even when the
generator's canonical route is approved. An existing unsafe label stays unsafe;
other archival outputs are unverified. Provenance records both actual executed
and catalog rule hashes, plus the reference choice and original catalog labels.
Generator self-checks, well-formedness, duplicate/identity rejection and attempt
bounds still apply. Archival selection is incompatible with `synthpipe`, whose
rules are newly synthesized rather than selected from an authority.

Generic generators use their own emitted program. If it is a bare expression,
the episode retains `emitted_program`, records `expression_to_rule` normalization,
and exposes the equivalent executable `program` whose hash is in provenance.
Every supplied pair must still agree with Racket before it is exported.

Other historical producer launchers remain copied source in prepared `workspace`
trees. A preserved launcher is not implicitly a supported public route; use the
documented export styles and consult the migration map for remaining work.

## Original public host tasks

For original host challenges, use the explicit host exporter; it never invokes
a generator or applies generator approval filters. It preserves all original
demonstrations and query inputs, with query answers in labels.private.jsonl.

```bash
PYTHONPATH=src .venv/bin/python -m arcpuzzles.host_dataset \
  --source shared/data/raw --out var/datasets/NEW-HOST-EXPORT

# Explicitly include original training and public-evaluation source splits:
PYTHONPATH=src .venv/bin/python -m arcpuzzles.host_dataset \
  --source shared/data/raw --all-public --out var/datasets/NEW-ALL-PUBLIC-EXPORT
```

The default still emits only training tasks. `--all-public` requires both
original source splits, rejects overlapping task IDs or missing query labels,
and marks the manifest `source_split=mixed_public` with per-split counts. Each
private label retains its original `training` or `evaluation` source; all four
original JSON snapshots and their hashes remain in `source.private/`. Both
variants use the verified `arcpuzzles-dataset-v1` envelope and
`score_scope=host_queries`. No training admission is implied. The September 12
training-only export contains 1,000 tasks and 1,076 queries, dataset
`5708a54a974f2b0c8fa43767c0c1ade49a59d7ec92d7bf508ee7df91ce4e811d`.
The September 26 all-public export at
`var/datasets/arc2-all-public-original-20260926-v1/` passed the verifier with
1,000 training tasks, 120 public-evaluation tasks and 1,248 masked queries;
its dataset ID is
`8596009a86af0e93aeca3e0fcc980fc25681f616b1f1e893de3359a50025a0b4`.
ARC2kaggle imports this with scripts/import_puzzles.py --score-scope host_queries,
then runs repeated Pi attempts against the original private query answers.
