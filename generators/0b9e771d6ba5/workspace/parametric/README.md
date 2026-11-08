# `line_span_policy` parametric prototype

This is a **proposed task-local authoring prototype** for generator `0b9e771d6ba5` (original ARC family `52df9849`). It does not modify or reapprove the production generator, catalog entry, canonical task, or training status.

## Parameter

`line_span_policy` is chosen once per episode from a deterministic rule-only seed stream and held fixed across every demonstration and query.

| Value | Meaning |
| --- | --- |
| `foreground_only` | Canonical/default. A complete collinear color span repaints only cells that were non-background in the original input. The materialized Racket source is the exact canonical program after outer-whitespace normalization. |
| `entire_span` | Proposed alternative. The same detected span repaints every in-bounds cell between its endpoints, including original background gaps. |

Both settings retain the same unique-modal background inference, impure foreground-only rectangle restoration, complete horizontal/vertical/diagonal detection, row-major endpoints, colors, and ascending overwrite order. Inputs are lawful `background_gap_stays` draws from the selected parent generator and are filtered so the two settings differ.

## Build fresh evidence

Run from the outer extracted packet directory. The output directory must not already exist.

```sh
python3 review.py run \
  python3 generators/0b9e771d6ba5/workspace/parametric/prototype.py \
  --out ../checks/parametric/line-span-policy-replay \
  --base-seed 20261023 \
  --demo-count 3 \
  --query-count 4
```

The writer selects one episode per setting, emits three demonstrations and four distinct queries per episode, executes both exact Racket programs over all 14 retained inputs, checks a Python mirror, scores the other setting using demonstrations only, and writes:

- `public/<opaque-visible-sha256>.json`: demonstrations plus query inputs only;
- `private/rules/`: exact Racket source and hashes;
- `private/racket/`: isolated Racket receipts;
- `private/episodes/`: seeds, hidden settings, all labels, rival checks;
- `report.json` and `manifest.json`: source bindings, counts, limitations, file hashes.

Public IDs are the SHA-256 of the exact bytes returned by `reviewer_support.public_challenge_bytes`; hidden settings, seeds, programs, and query answers cannot affect them.

## Focused tests

```sh
python3 review.py run \
  python3 -m pytest \
  generators/0b9e771d6ba5/tests/test_parametric_line_span_policy.py -q
```

The current source-bound evidence for this return is under `WORK/checks/0b9e771d6ba5-parametric-final-evidence/`; the replay command deliberately uses a new output directory.

## Scope and limits

The sampler supports 2–6 literal demonstrations and exactly four queries. Every episode includes one lawful 30×30 padded `background_gap_stays` stress input; padding uses the inferred background and is rechecked by the selected parent generator. The retained run covers only the two declared settings and that parent profile. Pairwise identifiability against the other setting does not establish uniqueness against arbitrary ARC programs or behavior outside that domain.
