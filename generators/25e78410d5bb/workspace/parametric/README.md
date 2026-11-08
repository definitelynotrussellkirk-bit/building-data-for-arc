# Majority fill, then connected-component selection

This is a native parametric extension of `25e78410d5bb`. The production generator
and its canonical reference are unchanged. Native owner acceptance remains a
separate operation after exact-source integration.

| Private episode setting | Rule |
| --- | --- |
| `{"retention":"all"}` | Execute the exact canonical Racket program: fill every zero region using the strict majority of its cardinally adjacent indicator contacts. |
| `{"retention":"largest_filled_component"}` | First perform the same majority fill. Then discover same-color four-connected components in that completed grid, excluding walls, and retain every component tied for maximum cell count. Restore originally zero cells outside those components to zero. Preserve all original nonzero cells. |

The intermediate matters: a wall indicator can connect rooms that acquire its
color during filling. Component size after filling can therefore select several
joined rooms rather than the largest original room or marker blob. Counting all
cells of one color, including disconnected islands, is a different rule.

## Supported requests

`adapter.generate(seed, settings, demos=3, queries=4)` returns private labeled
`train`/`test` pairs, exact `program_solution`, settings and sampler metadata.
`adapter.program(settings)` returns the exact Racket text. Native qualification
independently re-executes every label; Python outputs alone are authoring claims.

- Seed: exact integer from 0 through `2**63 - 1`.
- Demonstrations: 2–6; normal qualification uses three.
- Queries: 1–4 independently; normal generation uses four.
- Colors and all grid cells are exact integers; booleans are rejected.
- Inputs are distinct and identical across settings for the same request.
- Asking for one query produces the same demonstrations and first query as
  asking for four; later queries and private metadata do not enter the first turn.

The sampler creates 2–5 by 2–5 rectangular zero regions separated by shared
one-cell walls. It varies region dimensions, two indicator colors, marker density
and positions, and whether the outside edge has a wall. Every region has a strict
majority; both colors win somewhere, and at least one region sees both colors.
Votes count cardinal contacts, not connected indicator objects. Demonstrations
select a two-example cover against declared alternatives and shortcuts, then add
new examples when more demonstrations are requested.

The four query profiles are 15×12 (3×3 regions), 20×24 (4×5), 27×23 (5×4), and
30×30 (5×5). Their room dimensions, markers, colors and resulting connections vary
by seed. These are populated lattices throughout the canvas. The separate helper
`sampler.sample_grid(seed, height, width, row_bands, col_bands)` supports feasible
10–30-side geometries; it raises on impossible or exhausted requests.
These larger dimensions are parametric support, not new production overrides.

Sampling is bounded: at most 400 marker draws for one lattice and 64 candidates
for a two-demo teaching cover. Exhaustion raises `ValueError` rather than returning
fewer examples. Reported finite success rates are not guarantees for all seeds.

## Replay and export a review batch

From the outer packet folder:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/25e78410d5bb/workspace/parametric/probe.py \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/25e78410d5bb/new-replay
```

Use a fresh output directory. The tool executes real protected Racket labels,
checks setting/rival identification from demonstrations alone, and writes sorted
hash-named public challenges separately from private labels and certificates.
Public names hash exactly the visible bytes. The public four-query file is a
controller-side pool: expose only one query at a time. A first-turn projection
contains the demonstrations and first query only; the tool does not implement a
training loop or turn controller.

`programs.rivals_for(retention)` lists the finite audit rivals, and
`programs.rival_program(name, retention)` provides their executable Racket.
Passing these checks establishes rejection of the declared rivals only.

## Native qualification and owner handoff

The native `promotion.json` declares settings and count limits. The retained
source inventory is `evidence/manifest.json`; the reviewer receipt and execution
are under `WORK/checks/25e78410d5bb/qualification/`. To qualify a newly integrated
copy after regenerating a current inventory:

```bash
python3 -m arcpuzzles parametric qualify 25e78410d5bb \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out var/review/majority-components-qualification --summary
```

The owner reviews the semantics and causal witness, then uses the native
`parametric accept` route on exact integrated bytes. The return package's
`ready`/`qualified` state is not acceptance or training admission.

## Source map

- `programs.py`: exact canonical authority, composed rule, Python mirrors,
  executable audit rivals, and intermediate component inspection.
- `sampler.py`: bounded lattice construction and matched-input teaching selection.
- `adapter.py` and `promotion.json`: native API and finite contract.
- `probe.py`: reusable protected replay and public/private export.
- `tests/`: literal semantics, count/typing boundaries, teaching and export checks.
