# Parametric occupancy-rule prototype for `d70726fd510f`

This directory contains a **proposal**, not a production generator API or an
approval. The selected canonical generator remains the input sampler and the
canonical Racket rule remains authoritative. The prototype varies only two
small episode-level rule parameters while preserving the original aligned-panel
reasoning pattern.

## Declared parameters

| Parameter | Values | Canonical default |
|---|---|---|
| `operation` | `xor`, `and`, `or` over left/right nonzero occupancy | `xor` |
| `output_color` | ARC colors `1..9` | `2` |

There are 27 declared settings. `make_episode(seed)` chooses one setting once
through the versioned SHA-256 domain
`d70726fd510f:parameter-selection:v1:` and applies that same Racket program to
three demonstrations and one query. It never redraws a rule per pair.

The input contract is inherited from the selected generator: two equal-width
side-by-side panels separated by a full color-4 column, each panel empty or
monochrome apart from zero. Ordinary generated inputs contain all four aligned
occupancy states `00`, `01`, `10`, and `11`. Because the three operations select
different subsets of those states, and a selected cell reveals the paint color,
the demonstrations distinguish all 27 declared settings. The runtime checks
this by executing every rival on demonstrations only; query answers are not
passed to the identifiability checker.

## Racket is the label authority

`emit_program(Parameters(...))` materializes an exact callable Racket lambda.
`execute_program` runs that text through the included protected
`RacketBridge`; there is no Python label oracle. Canonical parity means the
default prototype produces the same executed outputs as every labeled
canonical pair, not that its program bytes are identical to the ledger text.

A solver-safe export contains only demonstration inputs/outputs and query
inputs. Seeds, selected parameters, program text, source metadata, and query
outputs stay in the private record.

## Reproduction

From the extracted packet root, reproduce the finite all-settings audit into a
new output directory:

```bash
python3 review.py run python3 generators/d70726fd510f/workspace/parametric/prototype.py \
  audit --seed-start 0 --out ../checks/parametric/replay-01
```

Create one canonical-default episode (`xor`, color 2; seed 7):

```bash
python3 review.py run python3 generators/d70726fd510f/workspace/parametric/prototype.py \
  episode --seed 7 --out ../checks/parametric/canonical-episode
```

Create a nearby alternative (`and`, color 2; seed 13):

```bash
python3 review.py run python3 generators/d70726fd510f/workspace/parametric/prototype.py \
  episode --seed 13 --out ../checks/parametric/and-episode
```

Run the focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/d70726fd510f/tests/test_parametric_extension.py
```

Existing output directories are refused so a replay cannot silently overwrite
older evidence.

## Retained evidence

The completed audit is under `WORK/checks/parametric/run-02/`:

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

The retained run completed all 27 settings with no failed episode, checked five
canonical pairs, and observed 27 distinct witness outputs. Public/private JSONL
rows align by order; failed attempts would retain `line_index: null` and would
make the audit fail.

## Limits

This is finite evidence: one seed-selected episode per setting, using sample
indices `0..3`. It does not cover every seed, every valid grid, every difficulty
band, or every imaginable competing ARC rule. Identifiability is only relative
to the 27 declared variants. The intentionally ambiguous diagnostic is outside
the ordinary full-state lesson contract and is retained to show that ambiguity
is reported rather than hidden. Production integration and variant approval
remain maintainer decisions.
