# Visible-only solve notes

## Exposure declaration

I had earlier exposure to this task's generator and rule semantics while repairing the generator. During this solve episode I did not reopen the generator, Racket authority, reference solution, private labels, or prior solution notes. I used only the four visible input/output pairs in `README.md` and the visible challenge data.

## Hypothesis from the visible pairs

The red cell (`2`) launches a beam one cell at a time to the **right**, including when the source is close to the right frame (training examples 1 and 2). Empty cells traversed by the beam become `8`. Existing nonempty objects remain unchanged.

The two mirror colors redirect the beam as follows:

- `3` is a slash mirror: right→up, up→right, left→down, down→left.
- `4` is a backslash mirror: right→down, down→right, left→up, up→left.
- `5` is an opaque wall/frame and stops the beam before that cell is changed.

Distractor mirrors and interior wall cells that the beam never reaches are unchanged. This explains all painted segments in all four examples, including the multi-turn path in example 1 and the off-path objects in examples 1–3.

## Implementation

`solution.py` copies the grid, finds the single red source, initializes direction `(0, 1)`, and traces until color `5` or the grid boundary. It paints only traversed zeros and applies the two mirror direction maps. A visited `(row, column, direction)` guard prevents an accidental mirror cycle from looping forever without altering ordinary examples.

## Why I stopped

The same deterministic rule accounts for every changed and unchanged cell in all four visible examples. In particular, the right-side red sources rule out launching toward the nearest frame or choosing launch direction from source position.
