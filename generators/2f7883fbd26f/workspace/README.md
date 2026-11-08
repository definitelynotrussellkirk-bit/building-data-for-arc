# Workspace

`lesson_window_probe.py` is the retained task-local curriculum probe. It loads the selected generator in either source-checkout or staged task-test layout, reads the generator's actual rival/witness declarations, verifies that every declared canonical shortcut fits every usable canonical pair, and checks every cyclic schedule start in every difficulty band. It also holds out each labelled pair in turn.

Run from the repository root with the review runtime on `PYTHONPATH`, for example:

```sh
PYTHONPATH=src:shared/runtime python3 generators/2f7883fbd26f/workspace/lesson_window_probe.py \
  --seeds-per-start 50 \
  --out ../checks/lesson-window-probe.json
```

Use the shared live-Racket census for production-shaped authority evidence:

```sh
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 2f7883fbd26f \
  --per-band 100 --rotate-query --timeout 1800 \
  --out ../checks/lesson-census.json
```

The probe is finite evidence against declared rivals, not a proof that no other induction rule exists. Workspace drafts are never automatically selected; `../generator.py` remains the selected implementation.
