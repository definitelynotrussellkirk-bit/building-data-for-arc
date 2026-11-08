# Relative-aspect native family

`reference=axes` is the exact canonical Racket rule: each monochrome 4-connected
object is colored 2/3/4 when its bounding box is tall/wide/square.
`reference=largest` first finds the unique object with the most foreground
cells, then compares every object's bounding-box ratio with that reference.
Greater/equal/smaller ratios receive 2/4/3. Cross multiplication preserves exact
rational comparisons; only original object cells are painted.

The source generator and its canonical authority are unchanged. This separate
prototype is intended for owner native qualification and acceptance. Executed
examples alone do not authorize training use.

## Run from the outer review packet

```sh
WORK/.venv/bin/python review.py run python3 \
  generators/f47990415137/workspace/parametric/make_examples.py \
  --seed 17 --demos 3 --queries 4 --out ../checks/aspect-examples-new
```

This uses the native worker to execute both settings on the visible
demonstrations, require a single surviving setting, and verify all query labels
through protected Racket before writing either setting's example.

`public/` holds controller-side challenge files with masked answers. `turns/`
holds the actual actor-facing payloads: demonstrations plus exactly one current
query. Pass only the current turn file to the model. Query order and the full
private episodes are in `private/metadata.jsonl`; programs, settings and future
queries never appear in a turn. First-turn content is identical whether later
queries are retained or omitted. This helper does not implement a controller or
training loop.

For native installation after integration, first run the repository's manifest
and qualification commands documented in `docs/parametric-promotion.md`, inspect
the retained causal witness, then use the owner's acceptance workflow. The
review return includes native qualification and execution evidence, not an
invented acceptance record.

## Input and teaching contract

The adapter supports independent 2–6 demonstration and 1–4 query counts. Normal
examples use three demonstrations and four novel queries. Shared seeds give
identical inputs and ordering across settings. Demo and query RNG streams are
separate; extending either count preserves existing role prefixes.

Every scene has zero background and separated monochrome connected components.
The largest component by foreground count is unique. The standalone sampler
supports 8–30 cells per axis. Ordinary scenes use four or six slots; large scenes
use nine. Queries include an 8×8 boundary, a variable-size wide-reference scene,
a substantive 30×30 scene with objects across all bands and boundary contacts,
and a square-reference case. Large scenes are not padded small examples.

Teaching scenes have six components and include an irregular square whose bbox
area exceeds the reference's bbox area, a smaller object with the same aspect,
objects on each side of the reference ratio, and repeated input colors requiring
different labels. The first two demonstrations use opposite reference
orientations. Shapes, counts, sizes, colors, density, flips, and placements vary.

The slot grammar deliberately excludes touching objects and arbitrary connected
polyominoes. It does not distinguish 4-connectivity from 8-connectivity, and the
bounded rival audit proves only the finite cases and programs it executes.
Tied maximum component sizes are outside the sampler's admitted grammar.

## Files and focused verification

`adapter.py` loads only the adjacent `prototype.py`. `canonical.rkt` preserves
the catalog bytes; `relative.rkt` implements the alternate rule. `export.py` is a
reusable task-local writer with hidden-field invariance and preflight duplicate
checks. `audit.py` executes the finite shortcut and boundary checks.

```sh
WORK/.venv/bin/python review.py run python3 -m pytest \
  generators/f47990415137/tests/test_parameters.py \
  generators/f47990415137/tests/test_parametric_export.py -q
WORK/.venv/bin/python review.py run python3 \
  generators/f47990415137/workspace/parametric/audit.py \
  --out ../checks/aspect-audit-new.json
```

The causal counterfactual replaces the foreground-count reference selector with
a bounding-box-area selector. Comparing its executed output with the true
program shows that changing the reference changes labels on other objects.
