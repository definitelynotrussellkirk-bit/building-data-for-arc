# Diagonal frames and colored beams

This is an unapproved authoring proposal for official public parent `80a900e0`.
`reference.rkt` is a general geometric rule, with no original-grid or answer
lookup. `beam=walls` returns its exact bytes; `beam=solid` is a nearby variant.

## Rule and original reasoning

On the 0/1 checkerboard, recognize same-color hollow rectangles in the diagonal
lattice. Equivalently, transform coordinates to `u=r+c, v=r-c`, with step two
along either axis. A complete monochrome connected component must equal its
rectangle perimeter and have at least three lattice cells on each side.
Original cores are 3×3 in this lattice, appearing as eight-cell diamonds.

A differently colored, uniform line immediately outside any side is a cap.
Read all of its visible cells, allowing the canvas to clip its ends. The cap's
two geometric endpoints launch parallel rays in the direction away from that
frame. Only original carrier-1 cells are recolored. Zeros, cores, cap cells and
other existing foreground remain intact. Core/cap roles come from geometry;
one color may play both roles in different objects. Missing caps emit no ray.

`beam=solid` uses the same discovered frame/cap relationships but launches a
ray from every cap cell, filling the beam's carrier cells between its walls.
Both settings preserve the original recognition and direction-inference steps.

Stage A discovers the actual frame bounds, cap origins and outward directions.
Stage B consumes those input-dependent ray specifications. A protected
counterfactual reverses the inferred directions while retaining the caps;
the changed final output demonstrates the dependency.

## Domain and generated diversity

Inputs are exact list grids with exact integer colors, each axis 5–30. The
checkerboard may have either phase; inactive cells are 0 and active cells are
1 or a foreground color 2–9. Generated frames have 3–6 lattice cells per side,
including nonsquares, and scenes contain one to three frames. The larger-frame
grammar is a synthetic generalization of the supplied originals.

Generated solid beams never assign conflicting colors to a new cell. The
original labels do not establish precedence for such collisions, so they are
outside the generated family. Original foreground is preserved if a ray meets
it; the ray continues to the boundary. No global color-role assignment is used.

Three core demonstrations teach a nonsquare frame with all directions, a single
clipped cap, then several frames whose colors exchange roles. The single-cap
anchor rejects a shortcut requiring two or more caps before extending a beam.
Optional demonstrations
retain the same prefix. Four novel queries include a meaningful 5×7 clipped
case, intermediate scenes and a populated 30×30 scene. Rotations, reflections,
positions, frame geometry, missing caps and color assignments vary by seed.

`generate(seed, settings, demos=3, queries=4)` supports exact integer seeds
0 through 2**63−1, 3–6 demonstrations and 1–4 queries independently. Inputs match
across settings. The complete four-query bank is shuffled before choosing a
requested prefix; changing counts does not change earlier pairs. Returned rows
are independently owned. `program`, `mirror`, `analyze` and `first_stage` expose
the private rule and intermediate claims for reproducible review.

The root `generator.py` is self-contained and returns inputs only through
`generate(seed, sample_index, *, difficulty=None, **overrides)`. Its profile
schedule supplies varied geometry; `difficulty` does not change that schedule.
`AXES={}` declares no caller overrides. `self_check` returns an empty findings
list for a valid input and strings describing validation failures otherwise.
The prototype imports the adjacent root implementation by exact path and has
no dependency on another checkout or a task-local module cached by another task.

## Reproduce in this packet

From the outer packet, with its prepared Python 3.12 environment and Racket:

```sh
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m pytest --import-mode=importlib generators/public_eval_80a900e0/tests -q
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_80a900e0 --root . --out ../checks/public_eval_80a900e0/preflight
```

Choose fresh output paths when rerunning. `checks/PUBLIC_CREATION_TOOLS.md`
documents protected causal replay and actual public previews directly from an
authoring preflight. Give a solver one selected public query file; keep future
queries, directory listings, settings, rules, answers and permutations private.
This return's current beam receipts use `preflight-current`, `causal-current`
and `preview-current`; earlier unsuffixed folders retain pre-integration-fix
evidence. `RESULTS.json` points to the current artifacts.

Python labels are claims checked independently through protected Racket.
Finite semantic and rival checks do not establish unrestricted uniqueness or
learning gain. Authoring preflight is separate from owner registration, native
qualification, exact-source acceptance and training admission.
