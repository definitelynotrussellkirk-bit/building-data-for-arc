# Marker-relay bounding-box family

This task-local family preserves the selected canonical rule exactly while adding
one nearby rule setting with a real sequential dependency.

## Settings

- `outline_scope=all_objects` — byte-exact canonical rule: draw the bounding-box
  outline of every nonzero 4-connected component on a blank canvas.
- `outline_scope=marker_relay` — first draw every outline, read the unique newly
  painted nonzero corner next to the color-9 marker, then keep only the two
  disconnected component outlines carrying that sampled color. A second repeated
  color pair is present as a distractor, so the remote payload cannot be selected
  from adjacency alone.

Inputs are matched across settings. Each episode supports 2–6 demonstrations and
exactly four distinct private queries; query four is a substantive 30×30 case.
The controller-side public projection reveals one query per turn and excludes
settings, programs, answers, and future queries.

## Run the focused task suite

From the packet's outer directory (the directory containing `review.py`):

```bash
python3 review.py task-tests 6347dcb736b5 --phase after \
  --out ../checks/6347dcb736b5-tests
```

## Rebuild bounded evidence

From `WORK/`:

```bash
python3 run_with_racket.py python3 \
  generators/6347dcb736b5/workspace/parametric/verify.py \
  --out generators/6347dcb736b5/workspace/parametric/evidence/recheck \
  --seed 0 --seed 17 --demos 3
```

## Native qualification

From `WORK/` after building the native manifest:

```bash
python3 run_with_racket.py python3 -m arcpuzzles parametric qualify \
  6347dcb736b5 --out ../checks/6347dcb736b5/qualification --summary
```

These checks are finite reviewer evidence. They do not grant owner acceptance or
training admission; the owner must replay qualification on the exact integrated
source bytes.
