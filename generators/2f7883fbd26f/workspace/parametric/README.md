# Target-color parameter — task-local prototype

This proposed extension keeps the family’s original reasoning and output
encoding while changing one object role: which input color supplies the
sliding `2 × 2` windows to count. It does **not** modify the selected
per-puzzle generator, canonical Racket authority, `RULE_HASH`, or approval
status, and it is not training-admission evidence.

| Parameter | Bounded values | Original/default | Executed change |
|---|---|---|---|
| `target_color` | literal integers `1`, `2` | `1` | Count every sliding all-`target_color` `2 × 2` window, then encode the count as a width-5 unary bar of color 1. |

The default setting is semantically identical to the canonical rule. The
alternative setting counts color-2 windows but intentionally preserves the
same overlapping-window semantics and the same output representation. Thus
one small parameter changes the selected object role without replacing the
core counting task.

## Inputs and episode contract

Both settings use the repaired selected generator’s unchanged exact grammar.
Each retained input is `9 × 9`, contains constructed color-1 and color-2
`2 × 2` windows plus isolated noise, and passes the selected generator’s
`self_check`. Input constraints do not depend on `target_color`.

`make_episode(seed, target_color=1)` is canonical by default. Passing `2`
changes the complete episode. Passing `None` chooses
`(1, 2)[seed % 2]` **once before any pair is generated**; the choice is
independent of demonstration/query count. The same seed produces the same
input sequence for either setting. A fixed four-pair witness plan requests
unequal color-1/color-2 counts `(2,4), (5,1), (3,2), (4,3)`, so each lawful
demonstration separates the two declared settings. Complete evidence uses
three demonstrations and one query.

`emit_racket()` returns exact `(rule! (lambda ...))` source.
`execute_racket()` evaluates that source through the packet’s public
`RacketBridge`; there is no Python label mirror. `analyze_settings()` executes
both finite settings against demonstrations and predicts queries without
reading hidden query answers. Private artifacts retain rule text and SHA-256
hashes. Public challenges omit the parameter, program, seed, source metadata,
and query outputs.

## Run from the outer extraction directory

These commands select the included offline Racket runtime:

```bash
python3 review.py run python3 generators/2f7883fbd26f/workspace/parametric/target_color.py --seed 9173 --out ../checks/parametric/target-color
python3 review.py run python3 -m arcpuzzles check 2f7883fbd26f --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

The output directory must be new. Payload paths are relative to `WORK/repo/`.
The evidence command creates exactly:

- `episodes.private.json`: both complete episodes, fixed settings, exact Racket
  programs/hashes, source bindings, direct predictions for both settings, and
  finite identifiability reports.
- `challenges.public.json`: demonstrations and query inputs only.
- `verification.json`: actual invocation, artifact hashes, direct reexecution
  of all labels, all four canonical comparisons, and a lawful differing
  witness.

## Evidence limits

The retained checks establish default parity and identifiability for the two
declared settings on the recorded examples. They do not enumerate arbitrary
alternative programs, prove every seed distribution, change canonical
approval, or establish model-trajectory value. The prototype remains under
the task workspace and has no production runtime interface.
