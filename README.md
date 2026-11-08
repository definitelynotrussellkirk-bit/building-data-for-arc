# ARCpuzzles

**[HQ / all five lanes](https://github.com/definitelynotrussellkirk-bit/ARC2HQ#what-do-you-want-to-do)** · **[Generate puzzles or review generators](docs/teammate-start.md)**

Query puzzles, generate verified examples, and prepare generator improvement
reviews from one independent repository. No ARCagi2 or sibling checkout is needed.

New teammates can start with the
[ARC2 repo map](https://github.com/definitelynotrussellkirk-bit/ARC2HQ/blob/main/README.md#new-teammate-first-five-minutes),
then use [teammate pickup](docs/onboarding.md) for read-only commands, current
work leads, ownership, and artifacts missing from a clone. Read this repo's
[rules](AGENTS.md), [placement guide](docs/placement.md), and
[review guide](REVIEW/README.md) before generator assignments.

Use `arcpuzzles stats` for current library and approval counts. Each generator has its
own implementation, summary, notes, workspace, and retained evidence. Common
helpers, linters, reference execution, and data live under `shared/`.

Generator-specific decisions live in `generators/<id>/notes.md` and are exposed
as `notes` metadata. Counterexamples, focused tests and source-bound audits stay
with that generator. Use `arcpuzzles list --audit-unresolved --format json` to
find unresolved or untriaged audits. Common tool requests live as a current list in
`REVIEW/suggestions.json`. Processed returns are compacted into task-owned current
state; historical review ledgers and managed ZIP copies are removed after verification.
See the [notes, audit and ZIP-disposal workflow](docs/placement.md#generator-notes-and-review-retention).

## Install and start

Requires Python 3.12+. Querying and the HTTP API use Python's standard library.
Generation and execution checks also need **Racket** on PATH (or `RACKET_PATH`),
NumPy, and Pillow. On Debian/Ubuntu, Racket is available as `apt install racket`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[runtime,dev]'

arcpuzzles stats
arcpuzzles list --approved --limit 10
arcpuzzles --help
```

`python -m arcpuzzles` is equivalent to `arcpuzzles`. Commands work from any
working directory after installation. Use `--library /path/to/ARCpuzzles` before
the command, or set `ARCPUZZLES_HOME`, to choose a different explicit library.
A normal wheel includes the code and library; it also works without the source
checkout. See [installation and isolation checks](docs/verification.md).

## Generate a dataset: approved or unapproved

After installation, choose one command. Use a new output directory each time:

```bash
# New accepted rule families: four queries, automatic supported 2–6 demos.
arcpuzzles export --parametric-only --count 4 --seed 17 --sampling uniform \
  --style episodes --out var/datasets/accepted-s17
arcpuzzles inspect-export var/datasets/accepted-s17

# Approved only
arcpuzzles export --approved --count 4 --seed 17 --sampling uniform \
  --style episodes --out var/datasets/approved-s17
arcpuzzles inspect-export var/datasets/approved-s17

# Unapproved only: explicit research/review, not automatic training admission
arcpuzzles export --not-approved --allow-unapproved --count 4 --seed 17 \
  --sampling uniform --style episodes --out var/datasets/unapproved-s17
arcpuzzles inspect-export var/datasets/unapproved-s17
```

Increase `--count` after the small export verifies. The controller projects one
current query from `public.jsonl` at a time; the full file also contains future
query inputs. Private labels and reference rules stay with the controller.
The export records source approval, seeds, hashes and failed draws. Approval
does not guarantee every draw succeeds. See [the complete quick start](docs/teammate-start.md)
for difficulty choices, supervised targets and handoff, or [export options](docs/datasets.md).

## Portable dataset generation

Teammates can use the [portable generator handoff](https://github.com/Mhdaw/kaggle-ml-toolkit/tree/main/arcpuzzles)
for a pinned approved-source bundle, bundled Linux Racket, checksums, and a tested
CPU quickstart. The guide includes canonical and accepted-parametric exports with
four queries, private answers, and one-query model messages.

Owners rebuild that artifact with `PYTHONPATH=src python tools/build_generator_handoff.py
--out NEW_DIR/arcpuzzles-library.zip --racket-archive PATH_TO_PINNED_RACKET.tgz`.
It keeps current acceptance dependencies and fails if one is missing or changed;
source/rule approval and training admission remain separate.

## Query with flags

```bash
arcpuzzles list --approved --source training --limit 20
arcpuzzles list --approved --primitive objects --format json
arcpuzzles list --skill reflection --difficulty hard --format jsonl
arcpuzzles list --search 'fill' --sample 5 --seed 42
arcpuzzles list --kind generic --format ids
arcpuzzles list --not-approved --train-safety unverified --limit 10
arcpuzzles list --approved --count
arcpuzzles list --approved --all --format ids
arcpuzzles list --approved --offset 50 --limit 50
```

Filters combine with **AND**. Results are sorted by ID. `--sample` uses a local
seeded random draw from matching results. Default display limit is 50; `--all`
removes it. `--count` reports all matches before paging. `query` aliases `list`.

| Flag | Meaning |
|---|---|
| `--approved` / `--not-approved` | Effective approval from the current source and recorded evidence |
| `--train-safety LABEL` | Raw imported review label, such as `reviewed_safe` or `unverified` |
| `--source SOURCE` | Exact source or family: `training`, `bank`, `augmented`, `custom`, or `bank:<id>` |
| `--skill TAG` | Exact skill tag, case insensitive |
| `--primitive NAME` | Exact Racket primitive, such as `objects` or `flip-lr` |
| `--difficulty easy\|medium\|hard` | Recorded canonical difficulty, not a new measurement |
| `--kind per_puzzle\|generic` | Generator kind |
| `--search TEXT` | Substring in ID, summary, or skill tags |
| `--family ID` / `--split NAME` | Recorded family/split metadata; missing lineage stays unknown |
| `--has-generator` | Require an implementation file |
| `--format table\|json\|jsonl\|ids` | Human or machine output |

**What approved means:** `reviewed_safe`, positive mix weight, no active semantic
veto, an existing generator matching its review hash, and an unambiguous canonical
rule matching its recorded rule hash. This preserves the existing safe-pool
boundary and additionally detects stale code/rules. It does not perform a new
semantic review just by listing a puzzle.

At import, 453 entries have the raw `reviewed_safe` label and **449** meet the
full filter. One has a changed canonical rule hash; three have no canonical rule
entry (including two generic generators). Their labels/evidence are retained.
`show ID` explains exclusions under `approval_reasons`. Editing generator code
revokes effective approval until it has appropriate new review evidence; do not
refresh hashes simply to regain approval.

**October 3 owner policy:** an accepted repair counts as the generator's safety
review. Full-packet integration records `reviewed_safe`, pins the reviewed live
source/rule hashes and retains the reviewer-reported or independently-checked
evidence basis. Later edits revoke effective approval; random adversarial
findings remain available to reopen it. This does not admit model trajectories
to training. See [the fast review workflow](REVIEW/README.md).

## Inspect and generate

```bash
arcpuzzles show 6c68e1b008a5
arcpuzzles show aba27056 --challenge  # Original ARC training IDs also work
arcpuzzles show 3ef9eae12446 --challenge --variant 0 --out var/challenge.json
arcpuzzles generate 6c68e1b008a5 --count 2 --seed 17 --train 2 --test 1 \
  --out var/examples.jsonl
```

`show` (also `get`) is an **authoring view**: it includes reference programs,
canonical variants, and associated notes. `--challenge` emits only demonstration
pairs and query inputs as integer grids, omitting query answers and solution metadata. It does
not make a public training puzzle into a competition-heldout task.

Generation requires approval by default. Explicit research can use
`--allow-unapproved`; outputs retain that label. `--difficulty` controls the
generator's difficulty band. Generic generators must supply at least the
requested numbers of train/test pairs or generation fails visibly.

Generated output is JSONL. Every episode carries seed, program, provenance, and
recorded rejections. Outputs are executed/checked through Racket. Per-puzzle
generation uses the selected canonical rule and verifies its executed hash
against the approval record. To reproduce an older rule explicitly, use
`--reference archival --allow-unapproved`; this always produces unapproved
research data and retains self-checks. It is never an automatic fallback. Generic
generators execute their emitted program and require research opt-in. Bare Racket
expressions are wrapped as a rule, with the original expression retained.

Generation fails if it cannot produce the requested pairs; it never silently emits a short
batch. `--timeout` bounds the worker process group. Output paths must be new.

## Mix generators and export datasets

```bash
arcpuzzles export --approved --source training --count 20 --seed 17 \
  --draw-difficulty easy --out var/datasets/public-20
arcpuzzles export --id 6c68e1b008a5 --count 2 --seed 17 \
  --style grids --render chatml --out var/datasets/grid-chat
arcpuzzles export --id 6c68e1b008a5 --count 1 --seed 17 \
  --style native --out var/datasets/native-json
arcpuzzles inspect-export var/datasets/public-20
```

The default export separates public challenges from private labels and source
metadata. Optional styles include full episodes, grids, code, DSL token rows,
executed program mutations, synthetic execution traces, and ARC-native JSON or
private tensors (`--tensors native|bottleneck`, optional Torch/safetensors install).
`--group-queries` retains all queries in one native row. Sampling uses the
query flags and recorded weights, with an explicit attempt cap and retained
rejections. See [formats, bounds and compatibility checks](docs/datasets.md).

## Python API

```python
from arcpuzzles import Catalog

puzzles = Catalog()
rows = puzzles.query(approved=True, source="training", limit=10)
puzzle = puzzles.get("6c68e1b008a5")
challenge = puzzles.challenge("6c68e1b008a5", variant=0)
episodes = puzzles.generate("6c68e1b008a5", count=2, seed=17,
                            n_train=2, n_test=1)
result = puzzles.check("6c68e1b008a5", stage="lint")
manifest = puzzles.export("var/datasets/example", count=4, seed=17,
                          filters={"source": "training"})
```

`Catalog.query()` supports the same filters and paging as the CLI; its default
limit is unlimited. Returned dictionaries are independent copies. `get()`
preserves all canonical variants for an ID. Exact, unambiguous recorded aliases
are supported; ambiguous/unknown IDs raise an error.

## HTTP API

```bash
arcpuzzles serve --host 127.0.0.1 --port 8765
curl 'http://127.0.0.1:8765/v1/puzzles?approved=true&limit=10'
curl 'http://127.0.0.1:8765/v1/puzzles/6c68e1b008a5/challenge?variant=0'
```

Read-only endpoints: `/health`, `/v1/stats`, `/v1/puzzles`,
`/v1/puzzles/<id>`, and `/v1/puzzles/<id>/challenge`. Filters use underscore names
(`train_safety`, `has_generator`) and booleans `true`/`false`. HTTP pages default
to 50 rows and allow at most 1,000. Use `offset` for more. Invalid filters return
400; unknown IDs return 404. Requests never start generation, reviews, or checks.

## Checks and reviews

The [latest reviewer release](https://github.com/definitelynotrussellkirk-bit/ARCpuzzles/releases/latest)
contains the self-contained ZIP and checksums. The current trial draws one unapproved
base from a rotating 500-generator subset and requires one full parametric build
with deep adversarial self-review. No peer audits or solves are assigned by default.
Reviewers start at `START-HERE.md`, then `python3 review.py start` and `duties`.
Owners publish quickly with `review pack-full --fast`; [review operations](REVIEW/README.md)
records the frozen policies, source-bound intake and separate verification status.
The generator ZIP to send is local
`var/review/SEND-THIS-ARCpuzzles-review.zip`. It is an ignored generated
artifact, so a GitHub clone does not contain it. The
[review guide](REVIEW/README.md) records how to obtain or rebuild the packet
from its hash-bound sources. The separate
`var/review/SEND-THIS-ARC2-loop-review.zip` reviews the rollout-to-distillation
process: one random improvement ticket plus two audits. Its code and intake
belong to [ARC2train](https://github.com/definitelynotrussellkirk-bit/ARC2train/blob/main/docs/harness-review.md).
The small [Flash-to-Qwen9 validation packet](https://github.com/definitelynotrussellkirk-bit/ARC2train/blob/main/docs/teammate-validation.md)
is a separate CPU teammate handoff at `var/review/SEND-THIS-Flash-Qwen9-validation.zip`.
It includes English-first instructions, a Chinese translation and three pinned
historical traces; it does not grant compute or training admission.
The working folder shows the sendable packets and `INTERNAL`; retained
receipts and packet libraries keep stable paths behind that clean view.

Blind and exposed Python solves are optional historical lanes. Issued packets
retain their original contracts; current one-build packets require neither.
The [solve-loop guide](REVIEW/solves/README.md) covers intake, independent
replay, the local `var/review/solves/index.html` tracker, and the hashed
question/attempt feed for a separately cloned trainer.

```bash
arcpuzzles tools
arcpuzzles lint --verify-import
arcpuzzles lint --imports  # Import every generator in a separate runtime
arcpuzzles check 6c68e1b008a5 --stage lint --out var/checks/lint
arcpuzzles check 6c68e1b008a5 --stage selfcheck --out var/checks/selfcheck
# Full inherited 12-stage baseline; allow enough time:
arcpuzzles check 6c68e1b008a5 --battery --timeout 4000 --out var/checks/battery

# Prepare a random, source-bound first-tranche generator packet:
arcpuzzles review pick --cohort var/derived/verified-unapproved-official-generator-review-20260926-v1/receipt.json \
  --not-approved --source training --train-safety provisionally_safe --seed 42
arcpuzzles review list
arcpuzzles review pack review-REPLACE_WITH_ID --out var/review/request.zip
```

`lint` checks repository structure; `--verify-import` also compares copied source
bytes against the original import manifest. Legitimate later edits will appear
as differences. `check` runs the inherited generator checks, preserves their
warnings/failures, and retains logs/receipts when `--out` is supplied. Read the
battery summary: an advisory is not a green semantic result. Generation success
and structural lint do not establish that every generator is semantically sound.

`review pick` creates a source-bound request, baseline copy, and portable workspace
with shared tools and rule data. Active assignments are excluded from new picks.
`review intake`, `check`, `assess`, `integrate`, `feedback`, and `close` retain the
returned ZIP, verify a disposable candidate, and require an explicit selection
before any source change. No agent is spawned and no message is sent. See
[REVIEW/README.md](REVIEW/README.md) for the reviewer sequence and operator commands.
Closing an assignment does not apply a patch or grant approval.

## Layout and development

```text
generators/<id>/   generator.py, SUMMARY.md, notes.md, workspace/, evidence/, tests/
shared/           common runtime/helpers, tools/linters, data, inherited tests
catalog/          query metadata and runtime mappings
src/arcpuzzles/   public API, CLI, HTTP, generation/check/review operations
REVIEW/           requests, assignments, incoming returns, and dispositions
GUIDE/            executable DSL reference
tests/            public-interface regression tests
var/              ignored run output and scratch work
```

Edit a generator in its own folder and shared logic under `shared/`. Public
commands create disposable local runtime copies with the original tool layout;
no sibling source imports or symlinks are involved. Review workspace edits are
proposals, not changes to the selected generator. Each copy has source hashes.

```bash
python -m pytest -q
python -m pip wheel . --no-deps --wheel-dir dist
```

Read [shared tools](shared/README.md), [placement](docs/placement.md),
[migration/provenance](docs/migration.md), and [AGENTS.md](AGENTS.md).
