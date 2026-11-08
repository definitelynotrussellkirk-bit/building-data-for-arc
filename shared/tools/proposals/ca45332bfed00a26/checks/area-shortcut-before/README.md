# Version 4.0.1: retained area-only teaching counterexample

This independent CPU rescore found a teaching defect in the already completed
300-lesson production census. All labels are the original materialized
canonical Racket outputs. The rescore executes only the rival, loads no
generator, and starts no Racket process.

The rival depends only on foreground area. It uses the canonical histograms
for areas 5, 9, and 13, a valid extension for area 14, and a bounded count table
for the remaining supported areas. Every rival prediction on the selected
area 3..14 domain is a valid digit grid. The runnable implementation and its
full source are retained in `rescore_area_lookup.py` and `report.json`.

| Band | Production lessons with ambiguity | Query rotations with ambiguity |
| --- | ---: | ---: |
| Easy | 6 / 100 | 44 / 600 |
| Medium | 8 / 100 | 43 / 600 |
| Hard | 6 / 100 | 41 / 600 |
| Total | 20 / 300 | 128 / 1,800 |

There are 1,677 distinct input grids across the materialized lessons and 128
distinct ambiguous held-out input grids. The rival fits all three labeled
canonical pairs. The original three-rival census pass remains accurate for
those three declared rivals; it did not cover this additional rival.

The retained exact teaching example is the first failing production lesson:
easy band, index/sample index 24, seed 1181072585. Its five demonstrations have
areas 9, 8, 3, 9, 8 and outputs `[[8,1]]`, `[[8]]`, `[[3]]`, `[[8,1]]`, `[[8]]`.
The query also has area 9, but its true output is `[[9]]`; the rival returns
`[[8,1]]`. The exact six pairs, replay identity, source hashes, and rival source
are in
`repo/generators/12ace26107fd/counterexamples/area_lookup_lesson_4_0_1.json`
relative to `WORK`.

## Source binding and replay

The complete source census remains at `WORK/checks/lesson-census-final.json`.
It is not duplicated here. Its SHA-256 is
`b829dd51375c8eadda5adb6d84d4c8907a0862ed19883eeb572fcfebe75961fc`.
It binds generator SHA-256
`6ad956a18b488e22280ac6b6658cbbae8c68b4502b7db65980cf384019a8fc77`
and canonical rule identity `3e24db6285e1`.

`report.json` records predictions, reference outputs, demonstration fits, and
all six query rotations for every lesson. It verifies each original
materialized instance hash before scoring. `commands.json` records the actual
command, working directory, interpreter, execution timestamps, and exit code
0. `file-hashes.json` binds the replay files and exact counterexample.

The command was run from
`/workspace/scratch/df43994906e4/arcpuzzles_review/WORK`:

```bash
/workspace/scratch/df43994906e4/arcpuzzles_review/WORK/.venv/bin/python -B checks/area-shortcut-before/rescore_area_lookup.py --census checks/lesson-census-final.json --canonical-ledger repo/shared/data/canonical/puzzles.jsonl --out checks/area-shortcut-before --counterexample repo/generators/12ace26107fd/counterexamples/area_lookup_lesson_4_0_1.json
```

The standalone script requires only Python's standard library. To replay after
relocation, select the relocated interpreter and source paths, and choose new
`--out` and `--counterexample` destinations. Existing outputs are refused.

This evidence describes version 4.0.1 only. Subsequent repairs need their own
source-bound checks. The rescore establishes this concrete finite teaching
failure; it is not an exhaustive search over alternative rules.
