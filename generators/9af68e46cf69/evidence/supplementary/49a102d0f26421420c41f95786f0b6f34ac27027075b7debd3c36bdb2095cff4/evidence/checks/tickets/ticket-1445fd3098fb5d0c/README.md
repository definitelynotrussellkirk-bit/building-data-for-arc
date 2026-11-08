# Bounded adversarial witness: ticket-1445fd3098fb5d0c

Status: completed. This is a lawful witness of the selected rule, not a peer safety finding.

One generator call used the full pinned hexadecimal seed converted by `int(seed, 16)`, sample index 0, and exact controls `grid_h=9`, `grid_w=11`, `n_holey=1`, `n_solid=1`. The one tested shortcut is `any_bbox_background`. The independently implemented shortcut agrees with the source-declared rival and differs from the canonical Racket output at all six cells of the open-bbox negative object.

The background escape path `[3,5] -> [2,5] -> [1,5]` uses color 9 throughout and reaches outside the object bbox `[2,4,4,6]` (zero-based inclusive coordinates). Consequently an interior background pixel is insufficient to establish an enclosed background region. The Racket output agrees with the independently flood-filled full-region rule. Source and normalized authority hashes match the pinned ticket. The protected runtime identity and full canonical Racket text are retained.

Exactly one targeted probe ran, taking 5.035292 seconds. No retry, broad census, battery, or lesson-identifiability claim is included. Scope is one fixed controlled draw and one shortcut. No source, authority, approval, or peer audit file was changed.

## Reproduce

From `WORK/`, using the prepared offline runtime:

```sh
PYTHONPATH=repo/shared/runtime:repo/src:.review/python-deps PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.review/tmp" PLTUSERHOME="$PWD/.review/racket-runtime/user-home" RACKET_PATH="$PWD/.review/racket-runtime/racket/bin/racket" PATH="$PWD/.review/racket-runtime/racket/bin:$PATH" python3 checks/tickets/ticket-1445fd3098fb5d0c/probe.py
```

`run.log` records the actual original command/environment; `results.json` binds source, program, probe and runtime hashes. `witness.json` contains the lawful input, Racket output, shortcut output, exact differing cells, and escape path. `outcome.json` is the supplementary ticket row for integration.
