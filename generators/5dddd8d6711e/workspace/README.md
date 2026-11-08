# Reusable verification for 5dddd8d6711e

`maze_probe.py` contains an independent component/door-graph interpreter and a
source-bound lesson probe. It reads the current generator's actual
`CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` mappings. It checks every usable
canonical pair, labels deduplicated inputs through public `Catalog.apply` in
batches of at most 64, and measures each complete lesson separately.

From the extracted review packet root:

```bash
python3 run_with_racket.py python3 -m pytest generators/5dddd8d6711e/tests -q
python3 run_with_racket.py python3 generators/5dddd8d6711e/workspace/maze_probe.py \
  --lessons-per-band 100 --out ../checks/lesson-probe-new
```

The output directory must be new. `--lessons-per-band 100` means **100 base-seed
blocks per band**, each tested at all three cyclic starts: 300 overlapping lesson
windows per band, 900 total. Six indexed draws supply each block's three windows.
The report separates indexed draws, unique grids, overlapping windows, and
cross-band duplicates. Default base seeds are 0..99; each lesson has three demos
and one query. Read `report.json`, `failures.json`, `cases.jsonl`, `lessons.jsonl`
and the exact `racket_batches/` receipts before making semantic claims.

The CLI needs the repository's public `arcpuzzles` API plus Racket, NumPy and
Pillow. Its pure Python oracle can also be imported in a copied portable runtime.
When staging a runtime, explicitly copy this workspace and task tests because
new files are not added automatically to the packet's frozen runtime mapping.
Never import a predecessor checkout to make a relocated test pass.

The sampler domain is rectangular chamber lattices. The oracle also supports
more general Racket components for hand-built regression witnesses, which does
not claim the generator samples that larger domain. Overrides are outside the
three-draw teaching guarantee. Training approval remains a separate decision.
