# Parametric stacked-occupancy prototype for `55993f4c12af`

This directory contains a **task-local proposal**, not a production generator
API or an approval. The selected canonical generator remains the input sampler,
and the canonical Racket program remains authoritative. The prototype varies
only two episode-level rule parameters while preserving the original task's
aligned occupancy reasoning over the upper and lower halves of an even-height
grid.

## Declared parameters

| Parameter | Values | Canonical default |
|---|---|---|
| `operation` | `xor`, `and`, `or` over upper/lower nonzero occupancy | `or` |
| `output_color` | ARC colors `1..9` | `4` |

There are 27 declared settings. `make_episode(seed)` chooses one setting once
through the versioned SHA-256 domain
`55993f4c12af:parameter-selection:v1:` and applies the same Racket program to
three demonstrations and one query. A rule is never redrawn per pair.

The input contract is inherited from the selected generator: an even-height
grid split into two equal stacked halves, with one distinct nonzero foreground
color per half. Ordinary generated inputs contain all four aligned occupancy
states `00`, `10`, `01`, and `11`. Those states distinguish the three Boolean
operations, while any selected cell reveals the output color. The runtime
checks identifiability by executing every one of the 27 rival programs on the
demonstrations only; query labels are not supplied to that check.

## Racket is the label authority

`emit_program(Parameters(...))` materializes an exact callable Racket lambda.
`execute_program` evaluates that text through the packet's protected
`RacketBridge`; there is no Python label oracle. Canonical parity means the
canonical default (`or`, color 4) produces the same executed outputs as all
five labeled canonical pairs. It does not rely on textual equality with the
ledger program.

A solver-safe export contains demonstration inputs and outputs plus query
inputs. Seeds, selected parameters, program text, source identities, and query
outputs remain in the private record.

## Reproduction

Run commands from the extracted packet root. Materialize the finite all-settings
audit into a fresh output directory:

```bash
python3 review.py run python3 generators/55993f4c12af/workspace/parametric/prototype.py \
  audit --seed-start 0 --out ../checks/parametric/replay-01
```

Create one canonical-default episode (`or`, color 4; seed 9):

```bash
python3 review.py run python3 generators/55993f4c12af/workspace/parametric/prototype.py \
  episode --seed 9 --out ../checks/parametric/canonical-episode
```

Create a nearby alternative (`and`, color 4; seed 28):

```bash
python3 review.py run python3 generators/55993f4c12af/workspace/parametric/prototype.py \
  episode --seed 28 --out ../checks/parametric/and-episode
```

Run the focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/55993f4c12af/tests/test_parametric_extension.py
```

Existing output directories are refused so a replay cannot silently overwrite
older evidence.

## Retained evidence

The completed audit is under `WORK/checks/parametric/run-01/`:

| File | Meaning |
|---|---|
| `report.json` | Overall result, selected seeds, source hashes, runtime identity, failures, and limits. |
| `programs.json` | Exact Racket text and SHA-256 for all 27 settings. |
| `episodes.private.jsonl` | Complete labeled episodes, settings, programs, source identities, and rival results. |
| `challenges.public.jsonl` | Aligned public challenges with no query labels or hidden settings. |
| `canonical-parity.json` | Default rule executed on all five labeled canonical pairs. |
| `witness.json` | One lawful input on which all 27 settings produce distinct outputs. |
| `ambiguity.json` | Deliberately incomplete diagnostic where `and/3` and `or/3` both survive. |
| `command.json` | Exact payload command, working directory, and exit code. |

The retained run completed all 27 settings with no failure, checked all five
canonical pairs, and observed 27 distinct witness outputs. Public/private JSONL
rows align by order; failed attempts would retain `line_index: null` and make
the audit fail.

## Limits

This is finite evidence: one seed-selected episode per setting, using sample
indices `0..3`. It does not cover every seed, every valid grid, every difficulty
band, or every imaginable competing ARC rule. Identifiability is relative only
to the 27 declared variants. The deliberately ambiguous diagnostic is outside
the ordinary full-state lesson contract and is retained to prove ambiguity is
reported rather than hidden. Production integration and variant approval remain
maintainer decisions.
