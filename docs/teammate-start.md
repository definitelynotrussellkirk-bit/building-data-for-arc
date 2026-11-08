# Generate puzzles or improve generators

HQ / all five jobs
· Download retained model traces

Accept the private GitHub invitation first. Clone ARCpuzzles for dataset
generation; the reviewer ZIP already contains its own generator library.

## Generate puzzles

From a fresh ARCpuzzles clone, use Python 3.12+ and install once:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[runtime]'
# On Debian/Ubuntu, if Racket is missing:
sudo apt-get install racket
```

### 1. Choose the generator pool

| Pool | Export flags | Meaning |
|---|---|---|
| Accepted parametric families | `--parametric-only` | Current accepted rule settings, Racket labels, four queries by default |
| Approved only | `--approved` | Current generator/rule hashes match approval, positive weight, no active veto |
| Unapproved only | `--not-approved --allow-unapproved` | Research/review pool; includes stale approvals, missing evidence and vetoed sources |

The flags select **generators**, not individual training episodes. An approved
generator can still fail a draw or a lesson check. An unapproved export remains
unapproved even when its reference execution succeeds. The exporter keeps these
source labels; it does not admit either export to model training.

Check current pool sizes with `.venv/bin/arcpuzzles list --approved --count`
and `.venv/bin/arcpuzzles list --not-approved --has-generator --count`.
The owner snapshot [accepted-family index](../REVIEW/parametric-families-current.json)
lists parameter choices, program hashes and per-family demonstration limits.
Exports check the actual source and acceptance again before generation.

### 2. Generate a small dataset

**Accepted parametric families — usual starting point for the new data:**

```bash
.venv/bin/arcpuzzles export --parametric-only --count 4 --seed 17 \
  --sampling uniform --style episodes --out var/datasets/accepted-s17
.venv/bin/arcpuzzles inspect-export var/datasets/accepted-s17
```

This mode defaults to four distinct queries and resolves each family's supported
demonstration count automatically, with a floor of two and a ceiling of six.
Omit `--train` so families needing three, four or five demonstrations get them.
Add `--id b5b012cd97d9` for a small single-family trial. For an explicit rule
setting, use [the native parametric exporter](parametric-promotion.md).
`--accepted-parameters` is the broader mixed option: it also permits canonical
draws from generators without an accepted parameter family.

**Approved canonical generators:**

```bash
.venv/bin/arcpuzzles export --approved --count 4 --seed 17 \
  --sampling uniform --style episodes --test 4 \
  --out var/datasets/approved-s17
.venv/bin/arcpuzzles inspect-export var/datasets/approved-s17
```

**Unapproved only — explicit research or generator review:**

```bash
.venv/bin/arcpuzzles export --not-approved --allow-unapproved --count 4 --seed 17 \
  --sampling uniform --style episodes --test 4 \
  --out var/datasets/unapproved-s17
.venv/bin/arcpuzzles inspect-export var/datasets/unapproved-s17
```

Uniform sampling makes every matching generator equally likely. Canonical
exports retain their declared minimum/floor-four demonstration policy; legacy
families can require more. Do not truncate a required teaching context.
`--draw-difficulty easy`, `medium` or `hard` controls canonical generation;
accepted parametric adapters have no shared difficulty control. Increase
`--count` after a small export verifies. It counts episodes, not individual query
targets; four episodes with four queries provide sixteen supervised answers.

`--allow-unapproved` **alone** permits a mixed approved/unapproved pool. Use it
with `--not-approved` when you want only unapproved generators. Keep the pools
in separate output directories so experiments cannot mix them accidentally.

### 3. Verify and hand off

**Result:** the new directory named by `--out`. Share that complete directory as
one archive, including `manifest.json`. The controller retains `public.jsonl`,
which contains every query input, and presents **one query at a time** to the
model. Send demonstrations and the current input; keep future inputs, answers,
settings, seeds and reference programs private. Wait for one answer before
presenting the next query, and keep query indices/total counts outside the prompt.
See [the one-query projection](datasets.md#four-supervised-queries-per-shared-demonstration-context).
Supervised answers are loss targets, never part of their input prompts. Existing
output directories are not overwritten.

Only use an export after `inspect-export` passes and its manifest says
`complete`. Invalid example-count declarations, failed draws and unsupported
lessons stay in private runtime/rejection evidence. If the draw cap is reached,
the export is `incomplete`; inspect `rejections.jsonl`, fix the source or use a
new output directory with an explicit larger `--max-attempts`. Never relabel a
short export as complete.

[Export options and exact files](datasets.md) cover difficulty, sampling and
rendering. Run `arcpuzzles stats` for this checkout's current source-bound
approval counts; README's import-time counts are historical. Puzzle approval
and model-trajectory admission are separate.

## Improve generators

**Download the current reviewer packet.**
Download **`SEND-THIS-ARCpuzzles-review.zip`**, extract it, read `START-HERE.md`, then
run `python3 review.py verify`, `python3 review.py start` and
`python3 review.py duties` from the extracted packet root. Current packets carry
a rotating 500-generator subset and pinned Racket, so no repo clone is needed.
Finish one robust parametric build from an unapproved base and deeply adversarially self-review it: check and repair each
base, add a meaningful family, adversarially self-review its learnability, and
complete protected execution, source inventory, causal witness and export checks.
There are no peer assignments. Source-bound older packets retain their own policy.

Return the delta ZIP produced by the packet's finish/build command. Do not zip
the entire library again. Follow `WORK/RETURN-GUIDE.md` for the concise brief,
changed source, actual check evidence, limits and biggest avoidable friction.
Reviewer readiness becomes owner acceptance only after each exact integrated
family passes the native owner path. Generator acceptance does not admit model traces
to training.

Local owner copy: `var/review/SEND-THIS-ARCpuzzles-review.zip`.
The source/checksum receipt is [REVIEW/full-packet-current.json](../REVIEW/full-packet-current.json).
The release's `SHA256SUMS` and handoff receipt must identify the same packet.
A newer local build can precede release publication: if its hash differs, ask
the owner for the receipt-pinned ZIP instead of calling the older release current.
Fast refreshes are published with checksums and explicit pending deep validation;
in-flight older returns remain valid against their own source pins. See [review operations](../REVIEW/README.md)
for intake and prior audit records.

### Label a hand-made audit input

Use the public reference runner during repair or audit. From an installed clone:

```bash
.venv/bin/arcpuzzles apply TASK --input input.json --reference canonical \
  --timeout 120 --out var/checks/TASK-apply.json
```

`input.json` can be one grid, `{"input": GRID}`, `{"inputs": [GRID, ...]}`,
or a list of grids. In an extracted packet, run
`python3 review.py run python3 -m arcpuzzles apply TASK --input INPUT --out OUTPUT`;
the input/output paths are relative to `WORK/repo/`. The wrapper selects the
packet's verified Racket runtime. Use a new output filename.

The receipt contains the selected reference, generator/rule hashes, normalized
outputs and a separate error for each input. It supports per-puzzle generators,
at most 64 rectangular grids of 1–30 rows/columns, with integer colors 0–9.
Input and output sizes may differ. Check `rule_hash_matches_catalog` and every
result's `error`; a process exit of 0 does not establish universal rule validity.
Reference answers must stay outside blind solves and model-visible evaluation
prompts. See [the Python API and exact hash meanings](verification.md#hand-made-inputs-and-reference-identity),
and [offline test setup](verification.md#offline-source-test-setup) for child-process imports.
