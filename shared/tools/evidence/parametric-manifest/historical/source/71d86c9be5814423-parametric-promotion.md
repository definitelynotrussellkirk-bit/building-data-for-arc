# Accept and use a parametric prototype

A retained prototype is authoring evidence. Its variants become usable through
an explicit promotion path: **adapter → qualification → acceptance → export**.
`parametric list` shows currently accepted families; `parametric status ID`
explains source drift. Acceptance is separate from the fixed canonical generator
and from the training agent's decision to use data or change its mixture.

## Accepted families

| Family | Private episode parameters | Supported counts |
|---|---|---|
| `48fee61713bb` | `stack_side`: `toward_main`, `toward_small` | 3–32 demos, 1–32 queries |
| `581bb11ff645` | `count_mode`: `cells`, `components`; `direction`: `ascending`, `descending` | 1–16 demos and queries independently |
| `7b0cb3b9a618` | `target_layer`: `front`, `back` | 2–12 demos, 1–32 queries |

The crossing-band family infers the visible occlusion order and selects its
unique front or back band as a 1×1 color answer. Its input sampler is matched
across settings, and demonstrations reject eight declared shortcuts under both
rules. It retains the reviewed six profiles (3×3 through 11×13), including the
canonical thin vertical-front restriction; it does not add large grids. See its
[workspace guide](../generators/7b0cb3b9a618/workspace/parametric/README.md).

The hole-ranking family preserves whole red groups and counts black cells or
four-neighbor black regions before sorting. Its adapter uses identical inputs
across settings for the same seed/counts, with a separate input RNG stream.
The first demonstration distinguishes every setting from the other settings and
the prototype's declared extra shortcuts. Queries include 21×29 and 30×29 grids.
Ties and boundary zeros have literal Racket checks; sampled scores are distinct
and sampled zero regions stay inside red perimeters. Exact 30×30 is unavailable
under its equal-slot geometry. See its
[workspace guide](../generators/581bb11ff645/workspace/parametric/README.md).

For three demonstrations and four queries from this family:

```bash
arcpuzzles parametric export 581bb11ff645 --count 4 --seed 12 \
  --demos 3 --queries 4 --out var/datasets/accepted-hole-ranking
arcpuzzles parametric verify-export var/datasets/accepted-hole-ranking
```

The omitted inline demo count uses the adapter's minimum (one for hole ranking);
pass `--train 3` explicitly when comparing three-demo/four-query datasets.

## Stack-side example

The stack-side family `48fee61713bb` exposes `stack_side=toward_main|toward_small`.
Its default is the exact canonical Racket program. It samples one setting per
episode and checks labels and finite-rival identifiability on every generation.

```bash
arcpuzzles parametric list
arcpuzzles parametric status 48fee61713bb
arcpuzzles parametric export 48fee61713bb --count 4 --seed 100 \
  --demos 3 --queries 4 --out var/datasets/accepted-stack-side
arcpuzzles parametric verify-export var/datasets/accepted-stack-side
```

The export contains `public.jsonl` and exact visible-byte, hash-named challenges
under `public/`. Give those to the model. `private.jsonl` contains query answers,
settings, reference programs, source/acceptance hashes, Racket runtime identity
and demonstration-only certificates. The manifest binds serialized files; export
verification checks hashes, strict grids and public/private projection. Generation
and acceptance execute Racket; the serialized verifier does not claim another
Racket replay. Existing output directories are refused. A duplicate visible
batch fails before creating its destination; publication writes the manifest last.

Python consumers use `Catalog.generate_parametric(ID, count=..., seed=...,
demos=3, queries=4)` or `Catalog.export_parametric(ID, output, count=..., ...)`.
`--settings '{"stack_side":"toward_small"}'` chooses one setting explicitly;
omitting it chooses deterministically from the seed. Parameters remain private
and fixed across all demonstration/query pairs. The default `generate`/`export`
behavior keeps its canonical reference contract.

## Use accepted families in a standard export

The trainer can use one episode format instead of importing the separate
parametric-export format. This is an explicit data-production option:

```bash
arcpuzzles export --approved --id 48fee61713bb --accepted-parameters \
  --style episodes --count 4 --seed 17 --train 3 --test 4 \
  --out var/datasets/inline-stack-side
arcpuzzles inspect-export var/datasets/inline-stack-side
```

The generator pool and its weights stay the same. A draw from a currently
accepted family chooses one setting deterministically from its draw seed and
holds it across all pairs. A generator without an accepted family still uses
its canonical rule. An existing but stale acceptance fails before publication
instead of silently falling back. Source drift after planning rejects the draw.
Within this opt-in export, duplicate visible challenges are rejected even if
their private answers differ. This also covers generations retained after a
render failure; it prevents contradictory copies within the exported batch.

Each parameterized record in `episodes.private.jsonl` carries its actual Racket
`program`, its whitespace-normalized `executed_rule_hash`, and:

```json
{"parametric":{"family":"48fee61713bb","settings":{"stack_side":"toward_small"},"acceptance_sha256":"...","source_sha256":"..."}}
```

`source_sha256` is the base generator hash; the acceptance hash binds its full
adapter/reference/runtime closure. `reference` is `accepted_parametric` and the
canonical rule hash remains separately in provenance. Parameters and query
answers stay private. Inline parameter IDs hash only the canonical visible
train/test challenge bytes; existing canonical episode IDs are unchanged.
Original-family lineage stays attached for split protection and does not imply
that the alternative rule equals its source ARC rule. Canonical explanatory
prose is not reused to describe the variant program.

The export freezes exact acceptance bytes in hash-named private files and indexes
them in `parametric.private.json`. Inspection checks those records, program/source
bindings, counts, distinct inputs and public/private projections. It does not
re-execute Racket or independently authenticate an untrusted rewritten bundle.

Demo/query counts are independent. An omitted demo count uses the accepted
adapter's minimum; other canonical draws keep their existing minimum/floor.
Accepted adapters have no difficulty control, so an explicit `--draw-difficulty`
is rejected when one is in the pool. Archival references and `synthpipe` cannot
combine with this option. A renderer can still reject a supported episode under
its existing bounds. `training_admitted` stays false: enabling a trainer reader,
choosing a mixture and admitting these records remain downstream decisions.

## Prepare another prototype

Keep its selected production generator approved and its task-local prototype
manifest current. Resolve exporter/teaching findings before qualifying it.
Add two task-local files under `generators/ID/workspace/parametric/`:

- `adapter.py`: `program(settings)` returns the exact Racket source;
  `generate(seed, settings, demos, queries)` returns a dictionary with
  `train`, `test` and `program_solution`. Pair labels may be Python claims:
  the independent worker re-executes every label through protected Racket.
- `promotion.json`: the bounded settings and request limits, for example:

```json
{
  "schema": "arcpuzzles-parametric-adapter-v1",
  "adapter": "generators/ID/workspace/parametric/adapter.py",
  "parameters": {"side": ["canonical", "alternate"]},
  "default": {"side": "canonical"},
  "limits": {"demos": [3, 8], "queries": [1, 8]}
}
```

After focused checks, create the source/evidence inventory with the native helper:

```bash
arcpuzzles parametric manifest ID \
  --evidence generators/ID/workspace/parametric/evidence/current \
  --include generators/ID/tests/test_parameters.py \
  --reported-checks 'Describe only the checks you actually ran and their limits'
```

Put the small scoped receipts/logs in the declared task-local evidence directory.
The command reads the current catalog/rule binding and adapter contract, hashes
the prototype sources/resources plus evidence and explicit includes, and writes
`workspace/parametric/evidence/manifest.json`. It never imports the adapter or
executes Racket. The checks description is author-reported; the inventory grants
no qualification, approval or training admission. Include paths and relative
evidence paths resolve from the selected library root; an explicit `--out` is
relative to the shell's working directory. Library outputs stay in the task or
ignored `var/`/`build/`; external JSON previews are also supported.

Existing outputs are refused and their hash is shown. To deliberately replace a
current report, pass that exact `--replace SHA256` and report the new checks;
old passing claims are not copied. Source/evidence must remain unchanged during
the write. Use `--out var/review/prototype-manifest.json` for a separate preview.
An existing public-ID correction hold stays pending in previews and replacements;
the inventory command cannot resolve it.
Keep useful prior evidence and current decisions with the task. Updating an
inventory does not refresh an accepted qualification; changed accepted source
still needs fresh qualification and acceptance.

Every setting must be total over the admitted grammar; failed rival execution cannot
serve as teaching evidence. Use 2–16 Cartesian settings. Declare any additional
prototype resources in a `resources` list of repository-relative task-local paths.
Keep the adapter thin: reuse the reviewed prototype rather than fork its rule.
Load task-local modules by exact adjacent path so another adapter's cached
`prototype` module cannot supply the implementation. For settings sharing an
input grammar, prefer matched inputs across settings and separate input/setting
RNG streams; make demonstrations identify the setting through their labels.
The accepted rule binds the selected `rule_task_id`, including distinct authority
rows that need no corresponding generator in a rotating packet.

## Qualify and accept exact bytes

```bash
arcpuzzles parametric qualify ID --seed 0 --seed 17 --demos 3 --queries 4 \
  --out var/review/qualification-ID
arcpuzzles parametric accept ID \
  --qualification var/review/qualification-ID/qualification.json \
  --reason 'Reviewed the parameter meaning, input grammar and bounded evidence'
```

Qualification exercises every setting on at least two distinct seeds with at
least four queries. Counts must be independent, all inputs distinct, and all
cells exact integer colors. The canonical default must match the selected
reference program byte-for-byte. The worker fits all declared programs to
**demonstrations only**, requires the chosen setting alone to survive, then
checks query labels. Alternative runtime errors fail qualification.

Acceptance re-executes the pinned jobs itself; an editable receipt claiming
`protected=true` cannot replace real execution. Review the parameter semantics
and grammar before accepting. The command stores compact task-owned evidence
and `generators/ID/parametric/accepted.json`. Generation refuses acceptance after
generator, selected reference, adapter, prototype, parser or runtime-helper drift,
or an active production safety veto. New draws are checked again with Racket.

The evidence covers the declared settings and sampled seeds, not arbitrary
alternative rules or every future seed. Request limits describe supported APIs;
a bounded sampler may still reject an episode. Acceptance does not establish
measured learning benefit, admit trajectories to training, or alter allocation
weights. The training agent owns those downstream decisions.

The prototype's original evidence keeps its reported/proposed status. A current
`parametric/accepted.json` and successful `parametric status` are the separate
authority for usable accepted variants; counting retained prototypes alone does
not count accepted parameterized generators.
