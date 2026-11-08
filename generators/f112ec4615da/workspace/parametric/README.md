# Priority-direction extension — proposed prototype

This task-local experiment preserves the original four-quadrant overlay
reasoning and changes only the fixed precedence order. It does not change the
selected generator, canonical Racket rule, approval hash, or production API.

## Parameter and episode contract

| Parameter | Allowed values | Original | Effective precedence |
|---|---|---|---|
| `priority_order` | `canonical`, `reverse` | `canonical` | `TR > BL > BR > TL` or `TL > BR > BL > TR` |

The deterministic episode seed chooses one value once: even seeds select
`canonical`, odd seeds select `reverse`. The same instantiated Racket program
labels three demonstrations and one query. Input generation is independent of
the hidden setting and uses four lawful inputs from the selected generator.
Every selected-generator input contains an all-four local overlap, so the two
orders disagree on every pair rather than only on a rare query.

## Exact Racket authority

`prototype.py` reads the exact selected canonical `program_solution`. The
canonical setting returns that text byte-for-byte. The reverse setting replaces
one exact `let*` binding sequence, reversing the four source roles; a missing or
duplicate sequence is an error. Every canonical check, generated label, and
counterfactual output is obtained by actual `RacketBridge` execution. No Python
label mirror is used.

## Run from the outer extracted packet directory

```bash
python3 review.py run python3 generators/f112ec4615da/workspace/parametric/prototype.py \
  --seed 0 --out ../checks/parametric/priority-s0
```

Focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/f112ec4615da/tests/test_parametric_priority.py -p no:cacheprovider
```

The prototype refuses to overwrite evidence directories.

## Public versus private evidence

`public/episode-001.json` and `public/episode-002.json` contain only three
labelled training pairs and one unlabelled query input. They omit seed, hidden
parameter, rule text, query answer, and output dimensions. Matching `private/`
files retain the parameter, exact Racket, labels, alternative-setting outputs,
and rotation checks. `private/rules/` stores both exact instantiated programs.

## Scope and limits

The retained run covers both settings with two consecutive seeds, seven
canonical labels, eight generated labels, eight counterfactual labels, the two
production queries, and all eight single-query rotations. It tests only the one
declared alternative setting. It does not prove uniqueness against arbitrary
rules, all seeds, or broader parametric APIs, and it does not approve the
prototype for training or catalog integration.
