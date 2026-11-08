# Parametric family for `67ec1565020d`

This directory contains a proposed native parametric adapter. It does not alter
`generator.py`, replace the selected canonical ARC rule, grant owner acceptance,
or admit generated records to training.

## Settings

`mode=canonical` is the default. `adapter.program()` returns the exact selected
canonical Racket bytes from `canonical.rkt`: every monochrome 4-connected object
is recolored by its tight bounding-box aspect (`wide -> 2`, `tall -> 3`,
`square -> 4`) while holes remain background.

`mode=wide_region_relay` uses the same sampled input grids and adds a sequential
controller-to-payload dependency:

1. **A:** apply the canonical aspect recoloring to every object left of the
   full-height color-5 divider;
2. **intermediate:** count the connected color-2 regions left of the divider
   after those recolorings merge adjacent, formerly different-color wide
   objects; and
3. **B:** select that numbered one of the three payload objects, in row-major
   order, and recolor only it by its own bounding-box aspect.

Every relay scene starts with three separate wide controller objects, while the
post-A region count is 1, 2, or 3. Thus the count cannot be replaced by the raw
number of wide objects. `raw_wide_count.rkt` is the retained protected-Racket
counterfactual: it always uses the raw count of three and selects a different
payload whenever the post-A count is one or two.

## Episode contract

The adapter supports 2–6 demonstrations and 1–4 queries independently. For a
fixed seed and counts, both settings receive byte-identical inputs. Prefixes are
stable: requesting additional demonstrations or queries does not change earlier
pairs. Four private query profiles are retained, with the fourth a substantive
30×30 boundary case. Public turns contain all demonstrations and exactly one
query input; settings, programs, query answers, and dependency metadata remain
private.

The scene grammar deliberately includes wide, tall, and irregular square
objects; distinct controller colors that merge only after A; three differently
shaped payload candidates; and a separator that prevents accidental cross-side
components. Exact integer ARC colors are enforced, booleans and floats are
rejected, global RNG state is untouched, and generated inputs are distinct
within each episode.

## Evidence and limits

`audit.py` checks matched inputs, supported counts, all declared finite rivals,
intermediate values 1–3, the 30×30 counterfactual, and selected protected-Racket
labels. `make_examples.py` writes separate private episodes, hash-named public
four-query projections, and hash-named one-query actor turns, then verifies every
label through protected Racket. The task-local tests cover exact canonical bytes,
Racket parity, deterministic/prefix-stable sampling, request and numeric
boundaries, public/private separation, the 30×30 causal case, and the two helper
programs.

These are bounded checks against named alternatives and selected seeds, not a
proof of universal identifiability or learning value. Native qualification is
reviewer evidence only. Exact integrated-source owner replay, semantic approval,
and any training-admission decision remain pending.

## Reproduction from `WORK/`

```bash
python3 ../review.py run python3 -m pytest \
  generators/67ec1565020d/tests/test_parametric_family.py -q

python3 ../review.py run python3 \
  generators/67ec1565020d/workspace/parametric/audit.py \
  --seed-start 0 --seed-count 64 --racket-seed-count 2 \
  --out ../checks/67ec1565020d/audit/audit.json

python3 ../review.py run python3 \
  generators/67ec1565020d/workspace/parametric/make_examples.py \
  --out ../checks/67ec1565020d/examples --seed 0 --demos 3 --queries 4

python3 ../review.py run python3 -m arcpuzzles parametric qualify \
  67ec1565020d --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/67ec1565020d/qualification --summary
```

Current source hashes before native qualification:

- production `generator.py`: `2efca0bd793421b579ca67617984517d0a2ced51db10673a8d6cc84b822d8dc3`
- `canonical.rkt`: `b45100a04df96ba6369a6b371e8146853ea7ba349a67dc7a42f69ad52d790982`
- `wide_region_relay.rkt`: `992e630eb273c9e73e2677c11897ed8828fba386171e5c0c4ea22ab81a748b6d`
- `raw_wide_count.rkt`: `459a1b14ec26c5408789d4d79d2d325946049acf3ba325b0882c656835c5449a`
